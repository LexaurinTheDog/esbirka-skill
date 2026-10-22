"""API klíč smí odejít jen na api.e-sbirka.gov.cz a nesmí se objevit ve výpisu -v. Bez sítě."""
import contextlib
import importlib.util
import io
import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(ROOT, "skills", "esbirka", "scripts", "esbirka.py")
KEY = "TAJNY+KLIC"


def load_mod():
    spec = importlib.util.spec_from_file_location("esbirka_key_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.load_env = lambda: {"ESBIRKA_API_KEY": KEY}
    return mod


class KeyTest(unittest.TestCase):
    def setUp(self):
        self.m = load_mod()

    def leaked(self, req):
        return "KLIC" in req.full_url or any("KLIC" in v for v in req.headers.values())

    def test_cizi_base_klic_nedostane(self):
        c = self.m.Client(base="https://evil.example")
        for auth in self.m.AUTH_CANDIDATES:
            self.assertFalse(self.leaked(c._build("GET", "/x", None, None, auth)), auth)

    def test_oficialni_api_klic_dostane(self):
        c = self.m.Client()
        self.assertIn("TAJNY", c._build("GET", "/x", None, None, ("query", "apiKey")).full_url)

    def test_verbose_klic_skryje(self):
        c = self.m.Client()
        c.verbose = True
        buf = io.StringIO()
        req = self.m.urllib.request.Request("http://127.0.0.1:9/?apiKey=TAJNY%2BKLIC")
        with contextlib.redirect_stderr(buf):
            with contextlib.suppress(SystemExit, Exception):
                c._do(req)
        self.assertNotIn("TAJNY", buf.getvalue())
        self.assertIn("***", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
