#!/usr/bin/env python3
"""
esbirka_browser.py — záložní přístup k e-Sbírce přes headless prohlížeč (Playwright).

Použije se, když REST rozhraní (API s klíčem i veřejná cache portálu) neodpovídá, vrací
403/429/5xx nebo místo JSON stránku WAF. Dva režimy:

  1. transport  – prohlížeč otevře portál e-sbirka.gov.cz a stejné JSON dotazy posílá z jeho
                  kontextu (fetch ze stejného originu, cookies, JS výzvy). Výstup je totožný,
                  všechny příkazy esbirka.py fungují beze změny.
  2. ui         – čte vykreslené stránky portálu: vyhledávání (/vyhledavani?f=…) a text předpisu
                  (/sb/ROK/CISLO/DATUM?zalozka=text#par_N). Nezávisí na cestách REST API,
                  jen na struktuře stránek (ověřeno 9/2026).

Závislost: `playwright` + Chromium. Instalace do izolovaného venv: `esbirka setup-browser`
(nebo ručně: pip install playwright && python -m playwright install chromium).
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse

PORTAL = "https://e-sbirka.gov.cz"
VENV_DIR = os.path.expanduser(os.environ.get("ESBIRKA_VENV", "~/.local/share/esbirka/venv"))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"


class BrowserUnavailable(Exception):
    pass


def venv_python():
    for p in (os.path.join(VENV_DIR, "bin", "python"), os.path.join(VENV_DIR, "Scripts", "python.exe")):
        if os.path.exists(p):
            return p
    return None


def ensure_playwright():
    """Vrátí sync_playwright. Není-li modul v aktuálním interpretu, ale existuje venv ze `setup-browser`,
    znovu spustí celý příkaz interpretem z venv (jednou, hlídáno proměnnou ESBIRKA_REEXEC)."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return sync_playwright
    except ImportError:
        vp = venv_python()
        if vp and not os.environ.get("ESBIRKA_REEXEC") and os.path.realpath(vp) != os.path.realpath(sys.executable):
            env = dict(os.environ, ESBIRKA_REEXEC="1", ESBIRKA_TRANSPORT=os.environ.get("ESBIRKA_TRANSPORT") or "browser")
            os.execve(vp, [vp] + sys.argv, env)
        raise BrowserUnavailable(
            "Modul playwright není k dispozici. Nainstalujte jej příkazem `esbirka setup-browser` "
            "(vytvoří venv v ~/.local/share/esbirka/venv a stáhne Chromium), nebo ručně: "
            "pip install playwright && python3 -m playwright install chromium.")


def setup_browser(verbose=True):
    """Vytvoří venv s Playwrightem a stáhne Chromium. Idempotentní."""
    say = (lambda *a: print(*a, file=sys.stderr)) if verbose else (lambda *a: None)
    vp = venv_python()
    if not vp:
        say(f"▸ vytvářím venv {VENV_DIR}")
        os.makedirs(os.path.dirname(VENV_DIR), exist_ok=True)
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
        vp = venv_python()
    say("▸ instaluji playwright do venv")
    subprocess.check_call([vp, "-m", "pip", "install", "--quiet", "--upgrade", "pip", "playwright"])
    say("▸ stahuji Chromium (jednorázově, ~150 MB)")
    subprocess.check_call([vp, "-m", "playwright", "install", "chromium"])
    say(f"✓ hotovo – prohlížeč připraven ({vp})")
    return vp


class BrowserSession:
    """Jedna instance headless Chromia na běh skriptu; stránka portálu zůstává otevřená."""

    def __init__(self, verbose=False, headless=True):
        self.verbose = verbose
        self._pw = ensure_playwright()().start()
        self._browser = self._pw.chromium.launch(headless=headless)
        self._ctx = self._browser.new_context(user_agent=UA, locale="cs-CZ", viewport={"width": 1280, "height": 900})
        self.page = self._ctx.new_page()
        self._on_portal = False

    def log(self, msg):
        if self.verbose:
            print(f"🌐 {msg}", file=sys.stderr)

    def close(self):
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:
            pass

    def _goto_portal(self):
        if not self._on_portal:
            self.log(f"otevírám {PORTAL}/")
            self.page.goto(PORTAL + "/", wait_until="domcontentloaded", timeout=60000)
            self._on_portal = True

    # ── režim 1: transport JSON dotazů z kontextu portálu ──
    def fetch_json(self, method, url, body=None, headers=None):
        """Provede fetch uvnitř stránky portálu; vrací (status, bytes)."""
        self._goto_portal()
        self.log(f"{method} {url}")
        res = self.page.evaluate(
            """async ({url, method, body, headers}) => {
                 const h = Object.assign({'Accept': 'application/json'}, headers || {});
                 if (body !== null) h['Content-Type'] = 'application/json';
                 const r = await fetch(url, {method, headers: h, body: body === null ? undefined : body, credentials: 'include'});
                 return {status: r.status, text: await r.text()};
               }""",
            {"url": url, "method": method, "body": json.dumps(body, ensure_ascii=False) if body is not None else None,
             "headers": headers or {}})
        return int(res["status"]), res["text"].encode("utf-8")

    # ── režim 2: čtení vykreslených stránek ──
    def ui_search(self, text, pocet=10):
        """Vyhledávání na portálu; vrací dict ve tvaru odpovědi /jednoducha-vyhledavani."""
        url = f"{PORTAL}/vyhledavani?f={urllib.parse.quote(text)}"
        self.log(f"UI vyhledávání {url}")
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        self._on_portal = True
        # výsledky se dokreslují asynchronně – čekej na řádky, nebo na hlášku o nulovém počtu
        for _ in range(60):
            state = self.page.evaluate(
                "() => document.querySelectorAll('tr.pravni-akt-row').length || (/0 výsledků|žádn[ée] výsledk|nebyl[oy] nalezen/i.test(document.body.innerText) ? -1 : 0)")
            if state:
                break
            self.page.wait_for_timeout(500)
        data = self.page.evaluate(
            """() => {
                 const rows = [...document.querySelectorAll('tr.pravni-akt-row')].map(r => {
                   const links = [...r.querySelectorAll('a[href^="/"]')];
                   const href = links[0] ? links[0].getAttribute('href').split('?')[0] : '';
                   const kod = links[0] ? links[0].textContent.trim() : '';
                   const nazev = (links.find(a => a.textContent.trim() !== kod) || {}).textContent || '';
                   const box = r.querySelector('[class*="esbir-pravni-akt-"]');
                   const cls = box ? box.className : '';
                   const stav = /zruseny/.test(cls) ? 'ZRUSENY' : /platny/.test(cls) ? 'AKTUALNE_PLATNY'
                              : /budouci/.test(cls) ? 'VYHLASENY_BUDOUCI' : /vyhlaseny/.test(cls) ? 'VYHLASENY_BEZ_UCINNOSTI' : cls.trim();
                   const m = (r.textContent || '').match(/(\\d{1,2})\\.\\s*(\\d{1,2})\\.\\s*(\\d{4})/);
                   const datum = m ? `${m[3]}-${m[2].padStart(2,'0')}-${m[1].padStart(2,'0')}` : '';
                   return {staleUrl: href, kodDokumentuSbirky: kod, nazev: nazev.trim().replace(/\\s+/g,' '), stavDokumentuSbirky: stav, datum};
                 });
                 const body = document.body.innerText;
                 const t = body.match(/z\\s*([\\d\\s\\u00a0]+)\\s*nalezen/) || body.match(/([\\d\\s\\u00a0]+)\\s*výsledk/);
                 const celkem = t ? parseInt(t[1].replace(/[^\\d]/g,''), 10) : rows.length;
                 return {pocetCelkem: celkem, seznam: rows};
               }""")
        data["seznam"] = data["seznam"][:pocet]
        data["zdroj"] = "portál (prohlížeč)"
        return data

    def ui_text(self, stale_url, ustanoveni=None):
        """Text znění (nebo jednoho ustanovení) z vykreslené stránky. Vrací dict s hlavičkou a řádky."""
        anchor = ""
        if ustanoveni:
            anchor = "#" + ustanoveni_to_anchor(ustanoveni)
        url = f"{PORTAL}{stale_url}?zalozka=text{anchor}"
        self.log(f"UI text {url}")
        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        self._on_portal = True
        self.page.wait_for_selector("div.fragment-wrapper", timeout=60000)
        # portál dokresluje fragmenty postupně – počkej, až se počet ustálí
        last = -1
        for _ in range(40):
            n = self.page.evaluate("document.querySelectorAll('div.fragment-wrapper').length")
            if n == last:
                break
            last = n
            self.page.wait_for_timeout(500)
        data = self.page.evaluate(
            """(ust) => {
                 const clean = s => s.replace(/\\s+/g, ' ').trim();
                 const hdr = clean((document.body.innerText.match(/(Aktuální|Minulé|Budoucí|Vyhlášené) znění[^\\n]{0,160}/) || [''])[0]);
                 const all = [...document.querySelectorAll('div.fragment-wrapper')];
                 let sel = ust ? all.filter(e => e.classList.contains('zvyrazneni-ustanoveni')) : all;
                 if (ust && sel.length === 0) {
                   // záložní postup: najdi označení a ber do dalšího § / čl.
                   const rx = new RegExp('^' + ust.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&').replace(/\\s+/g, '\\\\s*') + '$', 'i');
                   const i = all.findIndex(e => rx.test(clean(e.innerText)));
                   if (i >= 0) {
                     sel = [all[i]];
                     for (let j = i + 1; j < all.length; j++) {
                       if (all[j].querySelector('.type-paragraf, .type-clanek') || /^(§|Čl\\.)\\s*\\d/.test(clean(all[j].innerText))) break;
                       sel.push(all[j]);
                     }
                   }
                 }
                 const lines = sel.map(e => ({
                   id: e.getAttribute('data-fragment-id'),
                   typ: (e.className.match(/nt-styl-[\\w-]+/) || [''])[0],
                   paragraf: !!e.querySelector('.type-paragraf, .type-clanek') || /^(§|Čl\\.)\\s*\\d+[a-z]?$/.test(clean(e.innerText)),
                   nadpis: /nadpis/.test(e.className),
                   text: clean(e.innerText)
                 })).filter(l => l.text);
                 return {title: document.title, hlavicka: hdr, url: location.href, pocetFragmentu: all.length, radky: lines};
               }""", ustanoveni or None)
        data["staleUrl"] = urllib.parse.urlparse(data["url"]).path
        data["zdroj"] = "portál (prohlížeč)"
        return data


def ustanoveni_to_anchor(text):
    """'§ 2079' → 'par_2079', '§ 2079 odst. 2' → 'par_2079-odst_2', '§ 310 písm. c)' → 'par_310-pism_c', 'čl. 10' → 'cl_10'."""
    t = text.strip()
    parts = []
    m = re.match(r"^(§|čl\.?|Čl\.?)\s*(\d+[a-zA-Z]*)", t)
    if not m:
        return "par_" + re.sub(r"\D", "", t)
    parts.append(("par_" if m.group(1) == "§" else "cl_") + m.group(2))
    for kind, val in re.findall(r"(odst\.?|písm\.?|pism\.?|bod)\s*(\d+[a-z]?|[a-z]+)\)?", t[m.end():], flags=re.I):
        k = kind.lower()
        parts.append(("odst_" if k.startswith("odst") else "pism_" if k.startswith("p") else "bod_") + val)
    return "-".join(parts)


def render_ui_text(data, fmt="md"):
    """Převede řádky z ui_text na text/markdown."""
    if fmt == "json":
        return json.dumps(data, ensure_ascii=False, indent=1)
    out = []
    for l in data["radky"]:
        t = l["text"]
        if fmt == "md":
            if l["paragraf"]:
                out.append(f"\n### {t}")
            elif l["nadpis"]:
                out.append(f"**{t}**")
            elif re.match(r"^[a-z]\)\s", t):
                out.append("  " + t)
            else:
                out.append(t)
        else:
            out.append(("\n" + t) if l["paragraf"] else t)
    return "\n".join(out).strip() + "\n"


if __name__ == "__main__":
    # rychlý samostatný test: python3 esbirka_browser.py "insolvenční zákon" | python3 esbirka_browser.py /sb/2012/89 "§ 2079"
    args = sys.argv[1:]
    s = BrowserSession(verbose=True)
    try:
        if args and args[0].startswith("/"):
            print(render_ui_text(s.ui_text(args[0], args[1] if len(args) > 1 else None)))
        else:
            print(json.dumps(s.ui_search(" ".join(args) or "občanský zákoník", 5), ensure_ascii=False, indent=1))
    finally:
        s.close()
