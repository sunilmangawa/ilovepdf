/** Shared interaction helpers for both page shells. */
(function () {
  'use strict';

  const overlayPattern = /(modal|overlay|processing)/i;

  function isVisible(element) {
    if (!element || element.hidden) return false;
    const style = window.getComputedStyle(element);
    return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
  }

  function visibleOverlays() {
    return [...document.querySelectorAll('[id], [role="dialog"], .modal, .overlay')]
      .filter((element) => overlayPattern.test(element.id || element.className || '') && isVisible(element));
  }

  function syncScrollLock() {
    document.documentElement.classList.toggle('has-open-overlay', visibleOverlays().length > 0);
  }

  function prepareDialogs() {
    document.querySelectorAll('[role="dialog"], .modal, [id*="Modal"], [id*="modal"]').forEach((dialog) => {
      if (!dialog.hasAttribute('aria-modal')) dialog.setAttribute('aria-modal', 'true');
      if (!dialog.hasAttribute('tabindex')) dialog.setAttribute('tabindex', '-1');
    });
    syncScrollLock();
  }

  function closeOverlay(overlay) {
    if (!overlay || overlay.classList.contains('processing-overlay') || /processing/i.test(overlay.id || '')) return;
    const closeButton = overlay.querySelector('[data-modal-close], [data-close-overlay], .btn-close, .modal-close');
    if (closeButton) {
      closeButton.click();
      return;
    }
    overlay.hidden = true;
    overlay.style.display = 'none';
    overlay.setAttribute('aria-hidden', 'true');
    syncScrollLock();
  }

  document.addEventListener('DOMContentLoaded', prepareDialogs);

  // Inline tool scripts toggle display directly; observe those changes so a
  // dismissed popup never leaves the document locked on mobile.
  if (window.MutationObserver) {
    new MutationObserver(syncScrollLock).observe(document.documentElement, {
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'style', 'hidden', 'aria-hidden']
    });
  }

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const overlays = visibleOverlays();
    if (overlays.length) closeOverlay(overlays[overlays.length - 1]);
  });

  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-modal-close], [data-close-overlay]');
    if (!target) return;
    const overlay = target.closest('.modal, [role="dialog"], [id*="Modal"], [id*="modal"], .overlay');
    if (overlay) closeOverlay(overlay);
  });
})();
