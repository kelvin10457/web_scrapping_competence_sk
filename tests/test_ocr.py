"""R10.1: Tesseract empaquetado en el .exe (src/ocr.py)."""
from pathlib import Path

import pytesseract

import ocr

ROOT = Path(__file__).resolve().parent.parent


def _fake_tesseract(base: Path) -> Path:
    exe = base / "tesseract" / "tesseract.exe"
    (exe.parent / "tessdata").mkdir(parents=True)
    exe.write_bytes(b"")
    return exe


def test_req1_exe_usa_tesseract_empaquetado(tmp_path, monkeypatch):
    monkeypatch.setattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
    exe = _fake_tesseract(tmp_path)
    env = {}
    instalado = tmp_path / "instalado.exe"
    instalado.write_bytes(b"")
    assert ocr.configurar(meipass=str(tmp_path), candidatos=[str(instalado)], environ=env) == str(exe)
    assert pytesseract.pytesseract.tesseract_cmd == str(exe)
    assert env["TESSDATA_PREFIX"] == str(exe.parent / "tessdata")


def test_req2_sin_empaquetado_usa_instalacion_de_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
    instalado = tmp_path / "Tesseract-OCR" / "tesseract.exe"
    instalado.parent.mkdir()
    instalado.write_bytes(b"")
    env = {}
    cmd = ocr.configurar(meipass=str(tmp_path / "vacio"), candidatos=[str(tmp_path / "no.exe"), str(instalado)],
                         environ=env)
    assert cmd == str(instalado) and pytesseract.pytesseract.tesseract_cmd == str(instalado)
    assert "TESSDATA_PREFIX" not in env


def test_req3_sin_nada_queda_el_del_path(tmp_path, monkeypatch):
    monkeypatch.setattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
    assert ocr.configurar(meipass=None, candidatos=[str(tmp_path / "no.exe")], environ={}) == "tesseract"
    assert pytesseract.pytesseract.tesseract_cmd == "tesseract"


def test_req4_scrapers_no_repiten_rutas_de_tesseract():
    for rel in ("src/paises/ecuador/haid_scraper.py", "src/paises/mexico/elpedregal_scraper.py"):
        texto = (ROOT / rel).read_text(encoding="utf-8")
        assert "Tesseract-OCR" not in texto and "ocr.configurar()" in texto, rel


def test_req5_spec_empaqueta_tesseract_y_ocr():
    spec = (ROOT / "ScraperCompetencia.spec").read_text(encoding="utf-8")
    assert "TESSERACT_DIR" in spec and "spa.traineddata" in spec
    assert "'tesseract'" in spec and "'ocr'" in spec
