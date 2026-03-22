# iLovePDF — Required Software & Dependencies

## Python Packages
```bash
pip install -r requirements.txt
```

## System-Level Dependencies

### 1. LibreOffice (Required for Word/Excel/PowerPoint/ODT/ODS/ODP/RTF conversions)

**Windows:**
1. Download from https://www.libreoffice.org/download/download-libreoffice/
2. Install to default path: `C:\Program Files\LibreOffice\`
3. Verify: Open PowerShell and run:
   ```powershell
   & "C:\Program Files\LibreOffice\program\soffice.exe" --version
   ```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install libreoffice
```

**macOS:**
```bash
brew install --cask libreoffice
```

---

### 2. Ghostscript (Required for PDF Compression)

**Windows:**
1. Download from https://ghostscript.com/releases/gsdnld.html
2. Install and add to PATH:
   ```
   C:\Program Files\gs\gs<version>\bin
   ```
3. Verify: `gswin64c --version`

**Linux:**
```bash
sudo apt install ghostscript
```

**macOS:**
```bash
brew install ghostscript
```

---

### 3. Poppler (Required for PDF to Image conversion)

**Windows:**
1. Download from https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to `C:\poppler\`
3. Add `C:\poppler\Library\bin` to system PATH
4. Verify: `pdftoppm -h`

**Linux:**
```bash
sudo apt install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

---

### 4. pdf2htmlEX (Required for PDF to HTML conversion — Linux server only)

**Linux:**
```bash
wget https://github.com/pdf2htmlEX/pdf2htmlEX/releases/download/v0.18.8.rc1/pdf2htmlEX-0.18.8.rc1-master-20200630-Ubuntu-bionic-x86_64.deb
sudo dpkg -i pdf2htmlEX*.deb
sudo apt-get install -f
```

> **Note:** pdf2htmlEX is not available on Windows. The PDF-to-HTML tool will only work on the Linux server.

---

## Quick Verification Script (Windows PowerShell)
```powershell
Write-Host "Checking dependencies..."

# LibreOffice
if (Test-Path "C:\Program Files\LibreOffice\program\soffice.exe") {
    Write-Host "[OK] LibreOffice found" -ForegroundColor Green
} else {
    Write-Host "[MISSING] LibreOffice not found" -ForegroundColor Red
}

# Ghostscript
try { gswin64c --version 2>$null; Write-Host "[OK] Ghostscript found" -ForegroundColor Green }
catch { Write-Host "[MISSING] Ghostscript not found" -ForegroundColor Red }

# Poppler
try { pdftoppm -h 2>$null; Write-Host "[OK] Poppler found" -ForegroundColor Green }
catch { Write-Host "[MISSING] Poppler not found" -ForegroundColor Red }
```
