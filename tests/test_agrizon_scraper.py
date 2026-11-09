from paises.ecuador import agrizon_scraper


class _Resp:
    def __init__(self, products):
        self.status_code = 200
        self.url = "https://agrizon.com/x"
        self.headers = {}
        self._products = products

    def json(self):
        return {"products": self._products}

    def raise_for_status(self):
        pass


class _Session:
    def __init__(self, n_productos):
        self.urls = []
        self.n = n_productos

    def get(self, url, **kwargs):
        self.urls.append(url)
        return _Resp([{"vendor": "BioMar"}] * self.n if len(self.urls) == 1 else [])


def test_pagina_incompleta_no_pide_la_siguiente():
    s = _Session(181)
    assert len(agrizon_scraper.fetch_collection_products(s)) == 181
    assert len(s.urls) == 1
