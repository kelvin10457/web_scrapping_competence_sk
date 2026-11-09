# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

# R10.1: Tesseract (OCR de HAID, Nutrimar y El Pedregal) va dentro del .exe, en
# 'tesseract' (src/ocr.py lo busca en sys._MEIPASS). Se toma de TESSERACT_DIR o de
# la instalacion por defecto de UB-Mannheim. Sin Tesseract o sin espanol, la
# compilacion falla: no se entrega un .exe sin OCR.
TESSERACT_DIR = Path(os.environ.get('TESSERACT_DIR', r'C:\Program Files\Tesseract-OCR'))
_tessdata = TESSERACT_DIR / 'tessdata'
if not (TESSERACT_DIR / 'tesseract.exe').exists() or not (_tessdata / 'spa.traineddata').exists():
    raise SystemExit(f'Falta Tesseract con espanol (spa.traineddata) en {TESSERACT_DIR}. '
                     'Instalar con: winget install UB-Mannheim.TesseractOCR, o definir TESSERACT_DIR.')
tesseract_binaries = [(str(TESSERACT_DIR / 'tesseract.exe'), 'tesseract')]
tesseract_binaries += [(str(dll), 'tesseract') for dll in TESSERACT_DIR.glob('*.dll')]
tesseract_datas = [(str(_tessdata / f'{lang}.traineddata'), 'tesseract/tessdata')
                   for lang in ('spa', 'eng', 'osd') if (_tessdata / f'{lang}.traineddata').exists()]



a = Analysis(
    ['src/gui.py'],
    pathex=['src'],
    binaries=tesseract_binaries,
    datas=tesseract_datas,
    hiddenimports=['fuentes', 'paises.ecuador', 'paises.ecuador.nicovita', 'paises.ecuador.haid', 'paises.ecuador.aquaxcel', 'paises.ecuador.biomar', 'paises.ecuador.agripac', 'paises.ecuador.prilabsa', 'paises.ecuador.prilabsa_scraper', 'paises.ecuador.prilabsa_parser', 'paises.honduras', 'paises.honduras.nicovita', 'paises.mexico', 'paises.mexico.nicovita', 'paises.mexico.aquaxcel', 'paises.mexico.vimifos', 'paises.mexico.apiaba', 'paises.mexico.nutrimar', 'paises.mexico.elpedregal', 'paises.mexico.elpedregal_scraper', 'paises.mexico.elpedregal_parser', 'paises.mexico.aquatec', 'paises.mexico.aquatec_scraper', 'paises.mexico.aquatec_parser', 'paises.mexico.skilla', 'paises.mexico.skilla_scraper', 'paises.mexico.skilla_parser', 'paises.mexico.proaqua', 'paises.mexico.proaqua_scraper', 'paises.mexico.proaqua_parser', 'paises', 'paises._compartido', 'paises._compartido.nicovita', 'paises._compartido.aquaxcel', 'paises._compartido.nicovita_scraper', 'paises._compartido.nicovita_parser', 'paises._compartido.aquaxcel_scraper', 'paises._compartido.aquaxcel_parser', 'paises.ecuador.haid_scraper', 'paises.ecuador.haid_parser', 'paises.ecuador.agripac_scraper', 'paises.ecuador.agripac_parser', 'paises.ecuador.agrizon_scraper', 'paises.ecuador.agrizon_parser', 'paises.ecuador.agrizon_hatchery', 'paises.ecuador.megasupply', 'paises.mexico.vimifos_scraper', 'paises.mexico.vimifos_parser', 'paises.mexico.apiaba_scraper', 'paises.mexico.apiaba_parser', 'paises.mexico.nutrimar_scraper', 'paises.mexico.nutrimar_parser', 'paises.nicaragua', 'paises.panama', 'paises.panama.nasafeed', 'paises.panama.nasafeed_scraper', 'paises.panama.nasafeed_parser', 'paises.panama.italcol', 'paises.panama.italcol_scraper', 'paises.panama.italcol_parser', 'netutil', 'ocr'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ScraperCompetencia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
