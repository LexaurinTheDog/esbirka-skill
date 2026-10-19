"""Tempo a opakování HTTP volání e-Sbírky. Bez sítě."""
import importlib.util
import os
import shutil
import tempfile
import unittest
import urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(ROOT, "skills", "esbirka", "scripts", "esbirka.py")


def load_mod():
    spec = importlib.util.spec_from_file_location("esbirka_pace_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Clock:
    def __init__(self):
        self.t = 1000.0
        self.sleeps = []

    def time(self):
        return self.t

    def sleep(self, secs):
        self.sleeps.append(secs)
        self.t += secs


class PaceTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_mod()
        self.tmp = tempfile.mkdtemp()
        self.mod.CACHE_DIR = self.tmp
        self._env = os.environ.copy()
        os.environ.pop("ESBIRKA_API_KEY", None)
        os.environ.pop("ESBIRKA_BASE", None)
        os.environ.pop("ESBIRKA_AUTH", None)
        os.environ.pop("ESBIRKA_PUBLIC_BASE", None)
        os.environ["ESBIRKA_MIN_INTERVAL"] = "0"
        self.clock = Clock()
        self.mod.time.time = self.clock.time
        self.mod.time.sleep = self.clock.sleep
        self.calls = []

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _client(self, **kw):
        c = self.mod.Client(verejne=True, **kw)
        c._http_once = self._http
        return c

    def _http(self, req):
        self.calls.append(req.full_url)
        return 200, b'{"a":1}', {}

    def test_429_then_200_waits_and_retries(self):
        answers = [(429, b"", {}), (200, b'{"a":1}', {})]

        def http(req):
            self.calls.append(req.full_url)
            return answers.pop(0)

        c = self._client()
        c._http_once = http
        data = c.call("GET", "/sbirky")
        self.assertEqual(data, {"a": 1})
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.clock.sleeps, [1])

    def test_retry_after_header(self):
        answers = [(429, b"", {"Retry-After": "5"}), (200, b'{"a":1}', {})]

        def http(req):
            return answers.pop(0)

        c = self._client()
        c._http_once = http
        c.call("GET", "/sbirky")
        self.assertEqual(self.clock.sleeps, [5])

    def test_400_is_not_retried(self):
        def http(req):
            self.calls.append(1)
            return 400, b'{"chyby":[{"kod":"X","popis":"y"}]}', {}

        c = self._client()
        c._http_once = http
        with self.assertRaises(SystemExit):
            c.call("GET", "/sbirky")
        self.assertEqual(self.calls, [1])
        self.assertEqual(self.clock.sleeps, [])

    def test_connection_error_then_ok(self):
        n = {"i": 0}

        def http(req):
            n["i"] += 1
            if n["i"] == 1:
                raise urllib.error.URLError("timed out")
            return 200, b'{"a":1}', {}

        c = self._client()
        c._http_once = http
        self.assertEqual(c.call("GET", "/sbirky"), {"a": 1})
        self.assertEqual(n["i"], 2)
        self.assertEqual(self.clock.sleeps, [1])

    def test_two_starts_keep_interval(self):
        os.environ["ESBIRKA_MIN_INTERVAL"] = "1"
        starts = []

        def http(req):
            starts.append(self.clock.time())
            return 200, b'{"a":1}', {}

        c = self.mod.Client(verejne=True)
        c._http_once = http
        c.call("GET", "/a")
        c.call("GET", "/b")
        self.assertEqual(len(starts), 2)
        self.assertGreaterEqual(starts[1] - starts[0], 1.0)
        self.assertEqual(self.clock.sleeps, [1])

    def test_exhausted_429_still_falls_back(self):
        os.environ["ESBIRKA_API_KEY"] = "test-key"
        os.environ["ESBIRKA_AUTH"] = "header:esel-api-access-key"
        os.environ["ESBIRKA_MIN_INTERVAL"] = "0"
        c = self.mod.Client(base=self.mod.API_BASE)
        seen = []

        def http_bound(req):
            seen.append(c.base)
            return 429, b"", {}

        def no_browser(reason=""):
            raise self.mod.Nedostupne("bez prohlížeče")

        c._http_once = http_bound
        c.use_browser_transport = no_browser
        with self.assertRaises(self.mod.Nedostupne) as ctx:
            c.call("GET", "/sbirky")
        self.assertIn("429", str(ctx.exception))
        self.assertEqual(seen.count(self.mod.API_BASE), 4)
        self.assertEqual(seen.count(self.mod.PUBLIC_BASE), 4)
        self.assertEqual(self.clock.sleeps, [1, 2, 4, 1, 2, 4])

    def test_fragments_stop_when_subtree_complete(self):
        pages = {
            0: [{"id": 1, "eli": "/eli/par_1"}, {"id": 2, "eli": "/eli/par_2"}],
            1: [{"id": 3, "eli": "/eli/par_2/odst_1"}, {"id": 4, "eli": "/eli/par_3"}],
            2: [{"id": 5, "eli": "/eli/par_4"}],
        }
        asked = []

        class C:
            def dok(self, su, sub="", params=None, cache=False):
                n = params["cisloStranky"]
                asked.append(n)
                return {"seznam": pages[n], "pocetStranek": 3}

        fr = self.mod.all_fragments(C(), "/sb/2012/89", until_id=2)
        self.assertEqual([f["id"] for f in fr], [1, 2, 3])
        self.assertEqual(asked, [0, 1])

        asked.clear()
        fr = self.mod.all_fragments(C(), "/sb/2012/89")
        self.assertEqual([f["id"] for f in fr], [1, 2, 3, 4, 5])
        self.assertEqual(asked, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
