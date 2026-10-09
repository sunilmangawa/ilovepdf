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
sudo apt update
sudo apt --fix-broken install
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
### 5. HTML to PDF
python -m playwright install --with-deps chromium

## GNU GET TEXT
sudo apt update && sudo apt install gettext
python manage.py makemessages -l af -l ar -l az -l bg -l be -l bn -l br -l bs -l ca -l cs -l cy -l da -l de -l el -l en -l en_GB -l eo -l es -l es_AR -l es_MX -l es_NI -l es_VE -l et -l eu -l fa -l fi -l fr -l fy_NL -l ga -l gl -l he -l hi -l hr -l hu -l ia -l id -l is -l it -l ja -l ka -l kk -l km -l kn -l ko -l lb -l lt -l lv -l mk -l ml -l mn -l nb -l ne -l nl -l nn -l pa -l pl -l pt -l pt_BR -l ro -l ru -l sk -l sl -l sq -l sr -l sr_LAtn -l sv -l sw -l ta -l te -l th -l tr -l tt -l udm -l uk -l ur -l vi -l zh_CN -l zh_TW

# xyz.com//rosetta/files/project/

python manage.py compilemessages -l af -l ar -l az -l bg -l be -l bn -l br -l bs -l ca -l cs -l cy -l da -l de -l el -l en -l en_GB -l eo -l es -l es_AR -l es_MX -l es_NI -l es_VE -l et -l eu -l fa -l fi -l fr -l fy_NL -l ga -l gl -l he -l hi -l hr -l hu -l ia -l id -l is -l it -l ja -l ka -l kk -l km -l kn -l ko -l lb -l lt -l lv -l mk -l ml -l mn -l nb -l ne -l nl -l nn -l pa -l pl -l pt -l pt_BR -l ro -l ru -l sk -l sl -l sq -l sr -l sr_LAtn -l sv -l sw -l ta -l te -l th -l tr -l tt -l udm -l uk -l ur -l vi -l zh_CN -l zh_TW