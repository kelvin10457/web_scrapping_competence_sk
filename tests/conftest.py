import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

FIXTURES = Path(__file__).resolve().parent / "fixtures"


import netutil  # noqa: E402

netutil.ENABLED = False  # tests sin pausas de cortesia


import pytest  # noqa: E402
import powerbi  # noqa: E402


@pytest.fixture(autouse=True)
def _powerbi_fuera_del_repo(tmp_path, monkeypatch):
    """Ningun test escribe data/powerbi/ real: build_master lo regenera siempre,
    y con datos de prueba borraba los Excel reales (ver revision_pendiente.md)."""
    monkeypatch.setattr(powerbi, "POWERBI_DIR", tmp_path / "_powerbi_test")
    monkeypatch.setattr(powerbi, "HUMAN_PATH", None)
