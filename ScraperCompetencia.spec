# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/gui.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=['fuentes', 'paises.ecuador', 'paises.ecuador.nicovita', 'paises.ecuador.haid', 'paises.ecuador.aquaxcel', 'paises.ecuador.biomar', 'paises.ecuador.agripac', 'paises.honduras', 'paises.honduras.nicovita', 'paises.mexico', 'paises.mexico.nicovita', 'paises.mexico.aquaxcel', 'paises.mexico.vimifos', 'paises.mexico.apiaba', 'paises.mexico.nutrimar', 'paises', 'paises._compartido', 'paises._compartido.nicovita', 'paises._compartido.aquaxcel', 'paises._compartido.nicovita_scraper', 'paises._compartido.nicovita_parser', 'paises._compartido.aquaxcel_scraper', 'paises._compartido.aquaxcel_parser', 'paises.ecuador.haid_scraper', 'paises.ecuador.haid_parser', 'paises.ecuador.agripac_scraper', 'paises.ecuador.agripac_parser', 'paises.ecuador.agrizon_scraper', 'paises.ecuador.agrizon_parser', 'paises.mexico.vimifos_scraper', 'paises.mexico.vimifos_parser', 'paises.mexico.apiaba_scraper', 'paises.mexico.apiaba_parser', 'paises.mexico.nutrimar_scraper', 'paises.mexico.nutrimar_parser', 'paises.nicaragua', 'paises.panama', 'netutil'],
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
