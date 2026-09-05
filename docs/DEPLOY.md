# Předání webové prezentace k nasazení

Tento dokument je pro agenta (nebo člověka), který má stránku z této složky nasadit jako živý web.
Autor stránky ji nenasazoval; vše potřebné je zde a v souboru `index.html`.

## Co se předává

| Soubor | Účel |
|---|---|
| `docs/index.html` | celá prezentace, jeden statický soubor: HTML, CSS i JavaScript uvnitř, žádný build |
| `docs/.nojekyll` | vypíná Jekyll na GitHub Pages, aby se soubory podávaly beze změny |
| `docs/DEPLOY.md` | tento návod |

Externí závislosti stránky: pouze Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) pro písma
Libre Caslon Text, Source Sans 3 a IBM Plex Mono. Vše má deklarované náhradní systémové fonty, takže stránka
funguje i bez nich. Žádná analytika, žádné cookies, žádné API volání z prohlížeče návštěvníka.

Stránka je česky (cílová skupina jsou čeští právníci a vývojáři), v hlavičce má anglické shrnutí.
Obsahuje pouze veřejné informace o projektu. Neobsahuje žádný API klíč ani osobní údaje. Obrázky nejsou,
favicon je inline SVG (znak §).

## Doporučený postup: GitHub Pages ze složky `docs/`

Nejjednodušší a zdarma; repozitář už je veřejný. Zapnout Pages pro větev `main`, složku `/docs`:

```bash
gh api -X POST repos/LexaurinTheDog/esbirka-skill/pages \
  -f "source[branch]=main" -f "source[path]=/docs"
# stav a URL:
gh api repos/LexaurinTheDog/esbirka-skill/pages --jq '.html_url + " " + .status'
```

Nebo v nastavení repozitáře: Settings → Pages → Source „Deploy from a branch“ → Branch `main`, folder `/docs`.

Výsledná adresa: `https://lexaurinthedog.github.io/esbirka-skill/`. Tuto adresu už obsahuje `og:url`
v hlavičce `index.html`; při jiné doméně ji změňte.

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
2. Upravte `og:url` v `docs/index.html`.
3. U GitHub Pages zapněte „Enforce HTTPS“ po vystavení certifikátu.

## Kontrola po nasazení

- Stránka se načte ve světlém i tmavém režimu (řídí se nastavením systému; barvy jsou v CSS proměnných).
- Tlačítka „Kopírovat“ fungují jen na HTTPS nebo localhost (Clipboard API); na HTTP jen změní popisek.
- Karty instalace se přepínají myší i šipkami vlevo/vpravo.
- Časová osa v části druhé vykresluje 18 znění občanského zákoníku z dat vložených ve skriptu na konci souboru;
  po najetí ukazuje interval účinnosti a novely.
- Na šířce pod 900 px se postranní sloupce skládají pod sebe, tabulky rolují vodorovně uvnitř svého rámu.
- Doporučeno projet Lighthouse (Performance, Accessibility, SEO); stránka nemá žádné blokující skripty.

## Údržba obsahu

Zdroj pravdy o funkcích je repozitář (README, SKILL.md). Při změně verze skillu upravte:

- číslo verze v hlavičce stránky (`<small>v1.1.0</small>`),
- počet testů, pokud se změní (`27 živých testů v CI`, § 12),
- tabulku příkazů v části šesté, přibude-li příkaz,
- data časové osy jen tehdy, změní-li se ukázkový předpis; jsou to skutečné hodnoty z `esbirka zneni 89/2012`
  ke dni 5. 9. 2026 a jako taková jsou v popisku datovaná.

Doporučené sociální náhledy (`og:image`) stránka nemá; pokud je hosting vyžaduje, vytvořte PNG 1200×630
s názvem a taglinem ve stejných barvách (oxblood `#7B1E2E` na papírové `#F4F3EE`) a doplňte meta tag.
