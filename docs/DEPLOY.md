# Předání webové prezentace k nasazení

Tento dokument popisuje nasazení stránky z této složky jako živého webu.

**Stav: nasazeno 5. 9. 2026 na GitHub Pages** (větev `main`, složka `/docs`, HTTPS vynuceno):
https://lexaurinthedog.github.io/esbirka-skill/ – každý push do `main` měnící `docs/` se nasadí automaticky.
Níže zůstává postup pro případné přenesení jinam nebo na vlastní doménu.

## Co se předává

| Soubor | Účel |
|---|---|
| `docs/index.html` | celá prezentace, jeden statický soubor: HTML, CSS i JavaScript uvnitř, žádný build |
| `docs/og-image.png` | sociální náhled 1200×630 px (`og:image`, `twitter:image`); vygenerován z `docs/og-source.html` |
| `docs/og-source.html` | zdroj náhledu; při změně textu znovu vyrenderovat (viz Údržba) |
| `docs/.nojekyll` | vypíná Jekyll na GitHub Pages, aby se soubory podávaly beze změny |
| `docs/DEPLOY.md` | tento návod |

Externí závislosti stránky: pouze Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) pro písma
Libre Caslon Text, Source Sans 3 a IBM Plex Mono. Vše má deklarované náhradní systémové fonty, takže stránka
funguje i bez nich. Žádná analytika, žádné cookies, žádné API volání z prohlížeče návštěvníka.

Stránka je česky (cílová skupina jsou čeští právníci a vývojáři), v hlavičce má anglické shrnutí.
Obsahuje pouze veřejné informace o projektu. Neobsahuje žádný API klíč ani osobní údaje. Jediný obrázek je
sociální náhled `og-image.png`; favicon je inline SVG (znak §).

## Doporučený postup: GitHub Pages ze složky `docs/`

Nejjednodušší a zdarma; repozitář už je veřejný. Zapnout Pages pro větev `main`, složku `/docs`:

```bash
gh api -X POST repos/LexaurinTheDog/esbirka-skill/pages \
  -f "source[branch]=main" -f "source[path]=/docs"
# stav a URL:
gh api repos/LexaurinTheDog/esbirka-skill/pages --jq '.html_url + " " + .status'
```

Nebo v nastavení repozitáře: Settings → Pages → Source „Deploy from a branch“ → Branch `main`, folder `/docs`.

Výsledná adresa: `https://lexaurinthedog.github.io/esbirka-skill/`. Tuto adresu už obsahují `og:url`, `og:image`
a `twitter:image` v hlavičce `index.html` (sociální sítě vyžadují absolutní URL obrázku); při jiné doméně je změňte.

Každý další push do `main`, který změní `docs/`, se nasadí automaticky během minuty.

## Alternativy

Statický hosting bez buildu, kořenový adresář `docs/`:

| Platforma | Nastavení |
|---|---|
| Cloudflare Pages | Build command prázdný, Build output directory `docs` |
| Netlify | Publish directory `docs`, žádný build; nebo `netlify deploy --prod --dir docs` |
| Vercel | Framework „Other“, Output directory `docs`; nebo `vercel --prod docs` |
| vlastní server | zkopírovat obsah `docs/` do webrootu; stačí libovolný HTTP server |

## Vlastní doména (volitelné)

1. Přidejte soubor `docs/CNAME` s doménou (např. `esbirka.example.cz`) a nasměrujte DNS podle
   dokumentace zvoleného hostingu (u GitHub Pages CNAME záznam na `lexaurinthedog.github.io`).
2. Upravte `og:url`, `og:image` a `twitter:image` v `docs/index.html` na novou doménu.
3. U GitHub Pages zapněte „Enforce HTTPS“ po vystavení certifikátu.

## Kontrola po nasazení

- Stránka se načte ve světlém i tmavém režimu (řídí se nastavením systému; barvy jsou v CSS proměnných).
- Tlačítka „Kopírovat“ fungují jen na HTTPS nebo localhost (Clipboard API); na HTTP jen změní popisek.
- Karty instalace se přepínají myší i šipkami vlevo/vpravo.
- Časová osa v části druhé vykresluje 18 znění občanského zákoníku z dat vložených ve skriptu na konci souboru;
  po najetí ukazuje interval účinnosti a novely.
- Na šířce pod 900 px se postranní sloupce skládají pod sebe, tabulky rolují vodorovně uvnitř svého rámu.
- Doporučeno projet Lighthouse (Performance, Accessibility, SEO); stránka nemá žádné blokující skripty.
- Sociální náhled ověřte nástrojem platformy (např. opengraph.xyz, LinkedIn Post Inspector, X Card Validator);
  obrázek musí být dostupný na absolutní adrese z meta tagu `og:image`.

## Údržba obsahu

Zdroj pravdy o funkcích je repozitář (README, SKILL.md). Při změně verze skillu upravte:

- číslo verze v hlavičce stránky (`<small>v1.1.0</small>`),
- počet testů, pokud se změní (`27 živých testů v CI`, § 12),
- tabulku příkazů v části šesté, přibude-li příkaz,
- data časové osy jen tehdy, změní-li se ukázkový předpis; jsou to skutečné hodnoty z `esbirka zneni 89/2012`
  ke dni 5. 9. 2026 a jako taková jsou v popisku datovaná.

Sociální náhled (`og-image.png`) se generuje z `docs/og-source.html` headless prohlížečem, aby písma odpovídala stránce:

```bash
python3 - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1200,"height":630})
    pg.goto("file://"+__import__("os").path.abspath("docs/og-source.html")); pg.wait_for_timeout(3000)
    pg.screenshot(path="docs/og-image.png", clip={"x":0,"y":0,"width":1200,"height":630}); b.close()
PY
```

Při změně názvu, verze nebo čísel v náhledu upravte `og-source.html` a obrázek přegenerujte.
