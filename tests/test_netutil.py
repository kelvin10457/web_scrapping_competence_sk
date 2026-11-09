"""R6.1 + R6.2: ritmo de PACED_HOSTS y freno por dominio tras un captcha."""
import pytest
import requests

import netutil


@pytest.fixture
def ritmo(monkeypatch, tmp_path):
    """Activa las pausas, registra los sleeps sin dormir y limpia el estado."""
    esperas = []
    monkeypatch.setattr(netutil, "ENABLED", True)
    monkeypatch.delenv("SCRAPER_NO_PAUSE", raising=False)
    monkeypatch.setattr(netutil.time, "sleep", esperas.append)
    monkeypatch.setattr(netutil, "BLOQUEOS_DIR", tmp_path / "bloqueos")
    netutil.reset_blocked()
    netutil._state.update(n=0, next_long=99)
    yield esperas
    netutil.reset_blocked()


class _Resp:
    def __init__(self, url, status=200):
        self.url, self.status_code, self.text, self.headers = url, status, "", {}


class _Session:
    def __init__(self, captcha_hosts=()):
        self.pedidas, self.captcha_hosts = [], set(captcha_hosts)

    def get(self, url, **kw):
        self.pedidas.append(url)
        host = requests.utils.urlparse(url).hostname
        return _Resp("https://validate.perfdrive.com/x" if host in self.captcha_hosts else url)


# REQ-1
def test_pausas_cortas_y_larga_cada_6_a_10(ritmo, monkeypatch):
    netutil._state.update(n=0, next_long=netutil.LONG_EVERY[0])
    assert netutil.SHORT_PAUSE == (0.5, 2.5, 1.0)
    assert netutil.LONG_PAUSE == (5.0, 12.0)
    assert netutil.LONG_EVERY == (6, 10)
    for _ in range(30):
        netutil.pause("https://nicovita.com/p")
    assert all(0.5 <= e <= 12.0 for e in ritmo)
    largas = [e for e in ritmo if e >= 5.0 and e > 2.5]
    assert 3 <= len(largas) <= 5
    netutil.pause("https://otro.example/x")  # dominio sin ritmo
    assert len(ritmo) == 30


def test_pagina_en_cache_no_pausa(ritmo, tmp_path, monkeypatch):
    from paises._compartido import nicovita_scraper as ns
    monkeypatch.setattr(ns, "HTML_CACHE_DIR", tmp_path)
    url = "https://nicovita.com/producto/x"
    ns.cache_path(url).write_text("<html>cache</html>", encoding="utf-8")
    llamadas = []
    monkeypatch.setattr(netutil, "get", lambda *a, **k: llamadas.append(a))
    assert "cache" in ns.fetch(url)
    assert llamadas == [] and ritmo == [] and netutil._state["n"] == 0


# REQ-3
def test_captcha_frena_solo_ese_dominio(ritmo):
    s = _Session(captcha_hosts={"nicovita.com"})
    with pytest.raises(netutil.BlockedError):
        netutil.get(s, "https://nicovita.com/a", retries=0)
    ritmo.clear()
    netutil.pause("https://nicovita.com/b")
    assert len(ritmo) == 1 and netutil.SLOW_PAUSE[0] <= ritmo[0] <= netutil.SLOW_PAUSE[1]
    netutil.pause("https://agrizon.com/c")
    assert ritmo[1] <= netutil.LONG_PAUSE[1]
    assert "agrizon.com" not in netutil._lentos


# REQ-4
def test_tras_dos_captchas_no_vuelve_a_la_red(ritmo):
    s = _Session(captcha_hosts={"nicovita.com"})
    for u in ("https://nicovita.com/a", "https://nicovita.com/b"):
        with pytest.raises(netutil.BlockedError):
            netutil.get(s, u, retries=0)
    with pytest.raises(netutil.BlockedError) as exc:
        netutil.get(s, "https://nicovita.com/c", retries=0)
    assert s.pedidas == ["https://nicovita.com/a", "https://nicovita.com/b"]
    # revision Codex: el error sin red apunta al ultimo captcha guardado, no a None
    assert exc.value.saved is not None and exc.value.saved.exists()
    assert "perfdrive" in exc.value.captcha_url
    netutil.get(s, "https://el-pedregal.com/ok", retries=0)  # otro dominio sigue
    assert s.pedidas[-1] == "https://el-pedregal.com/ok"


# REQ-5
def test_reset_limpia_ritmo_lento_y_contador(ritmo):
    s = _Session(captcha_hosts={"nicovita.com"})
    for u in ("https://nicovita.com/a", "https://nicovita.com/b"):
        with pytest.raises(netutil.BlockedError):
            netutil.get(s, u, retries=0)
    netutil.reset_blocked()
    assert netutil._lentos == set() and netutil.blocked_events() == []
    s.captcha_hosts.clear()
    netutil.get(s, "https://nicovita.com/d", retries=0)
    assert s.pedidas[-1] == "https://nicovita.com/d"
