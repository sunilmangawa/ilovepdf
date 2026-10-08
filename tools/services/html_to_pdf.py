from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from django.conf import settings
from playwright.sync_api import Browser, Error as PlaywrightError, Page, sync_playwright


class PdfConversionError(Exception):
    """Raised for safe, user-displayable conversion failures."""


@dataclass(frozen=True)
class PdfOptions:
    format: str = "A4"
    print_background: bool = True
    margin: dict[str, str] | None = None

    def as_dict(self) -> dict:
        return {
            "format": self.format,
            "print_background": self.print_background,
            "margin": self.margin or {"top": "12mm", "right": "12mm", "bottom": "12mm", "left": "12mm"},
            "prefer_css_page_size": True,
            "display_header_footer": False,
        }


def _is_public_ip(address: str) -> bool:
    """Return True only for globally routable addresses."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return not any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_multicast, ip.is_reserved, ip.is_unspecified))


def _assert_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in settings.HTML_TO_PDF_ALLOWED_SCHEMES or not parsed.hostname:
        raise PdfConversionError("Enter a valid public HTTP or HTTPS URL.")

    hostname = parsed.hostname.rstrip(".")
    if hostname.lower() == "localhost" or hostname.lower().endswith(".localhost"):
        raise PdfConversionError("Local and private network URLs cannot be converted.")

    try:
        addresses = {result[4][0] for result in socket.getaddrinfo(hostname, parsed.port or 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise PdfConversionError("The web address could not be resolved.") from exc

    if not addresses or not all(_is_public_ip(address) for address in addresses):
        raise PdfConversionError("Local and private network URLs cannot be converted.")


def _route_request(route) -> None:
    """Allow only public HTTP(S) resources and practical page resource types."""
    request = route.request
    if request.resource_type in {"media", "websocket", "eventsource"}:
        route.abort()
        return

    parsed = urlparse(request.url)
    if parsed.scheme not in {"http", "https", "data", "blob"}:
        route.abort()
        return

    if parsed.scheme in {"data", "blob"}:
        route.continue_()
        return

    try:
        _assert_public_http_url(request.url)
    except PdfConversionError:
        route.abort()
        return
    route.continue_()


def _open_browser() -> tuple[object, Browser]:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=settings.HTML_TO_PDF_PLAYWRIGHT_HEADLESS,
        args=["--disable-dev-shm-usage"],
    )
    return playwright, browser


def _new_page(browser: Browser) -> Page:
    context = browser.new_context(
        viewport={"width": 1440, "height": 1080},
        java_script_enabled=True,
        user_agent="Mozilla/5.0 (compatible; HTML-to-PDF/1.0)",
    )
    page = context.new_page()
    page.set_default_navigation_timeout(settings.HTML_TO_PDF_NAVIGATION_TIMEOUT_MS)
    page.set_default_timeout(settings.HTML_TO_PDF_NAVIGATION_TIMEOUT_MS)
    page.route("**/*", _route_request)
    return page


def _wait_for_page(page: Page) -> None:
    # "networkidle" is best effort: some pages keep a connection open forever.
    try:
        page.wait_for_load_state("networkidle", timeout=8_000)
    except PlaywrightError:
        pass
    # Let web fonts and browser layout settle without an arbitrary long sleep.
    page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")


def convert_url_to_pdf(url: str) -> bytes:
    _assert_public_http_url(url)
    playwright, browser = _open_browser()
    try:
        page = _new_page(browser)
        response = page.goto(url, wait_until="domcontentloaded")
        if response is None or response.status >= 400:
            status = response.status if response else "unknown"
            raise PdfConversionError(f"The web page could not be loaded (HTTP {status}).")
        _assert_public_http_url(page.url)  # Check the final URL after redirects.
        _wait_for_page(page)
        return page.pdf(**PdfOptions().as_dict())
    except PdfConversionError:
        raise
    except PlaywrightError as exc:
        raise PdfConversionError("The web page could not be rendered. Check the URL and try again.") from exc
    finally:
        browser.close()
        playwright.stop()


def convert_html_to_pdf(html: str) -> bytes:
    # The uploaded file is rendered as document content. Base URL is deliberately
    # omitted so it cannot read local files; external HTTP(S) requests still pass
    # through the route guard above.
    playwright, browser = _open_browser()
    try:
        page = _new_page(browser)
        page.set_content(html, wait_until="domcontentloaded")
        _wait_for_page(page)
        return page.pdf(**PdfOptions().as_dict())
    except PlaywrightError as exc:
        raise PdfConversionError("The HTML file could not be rendered.") from exc
    finally:
        browser.close()
        playwright.stop()