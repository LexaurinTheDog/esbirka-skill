# esbirka-skill — zákony a jejich časová znění z e-Sbírky pro kódovací agenty

Skill pro **Claude Code, Codex CLI a další agenty podporující formát Agent Skills (`SKILL.md`)**, který
odpovídá na otázky o českých právních předpisech přímo z **e-Sbírky**, oficiální elektronické Sbírky zákonů
a mezinárodních smluv (Ministerstvo vnitra ČR). Jádrem je jeden skript v Pythonu bez závislostí.

> **English summary.** An agent skill (Claude Code / Codex / any `SKILL.md`-compatible agent) for querying
> the official Czech legislation portal e-Sbírka: find an act, list its time versions, get the text of a
> section as in force on a given date, diff two versions, list amendments. Single dependency-free Python
> script; works with or without an API key. Documentation is in Czech, as is the law it serves.

Co umí:

| Otázka | Příkaz |
|---|---|
| Jak zněl § 2079 občanského zákoníku k 1. 5. 2020? | `esbirka par 89/2012 "§ 2079" --k 1.5.2020` |
| Které znění insolvenčního zákona platilo 1. 6. 2019 a jaká novela ho založila? | `esbirka info 182/2006 --k 1.6.2019` |
| Kolik znění má zákon a kdy začne platit budoucí? | `esbirka zneni 182/2006` |
| Co se změnilo v § 757 OZ mezi 1. 7. 2025 a 1. 1. 2026? | `esbirka diff 89/2012 --z 2025-07-01 --k 2026-01-01 --par "§ 757"` |
| Které předpisy novelizují zákon o advokacii? | `esbirka souvislosti 85/1996 --typ JE_MENEN` |
| Čím byl zrušen starý občanský zákoník? | `esbirka info 40/1964` |
| Jak se jmenuje zákon č. 250/2016 Sb.? | `esbirka search "250/2016"` |

Agent pak odpoví s přesnou citací: „§ 108 odst. 1 zákona č. 182/2006 Sb., insolvenční zákon, ve znění
účinném od 1. 6. 2019 do 30. 9. 2019 (novela č. 31/2019 Sb.)“ a doslovným textem ustanovení.

## Instalace

Požadavky: Python 3.9+ a přístup na internet. Nic dalšího se neinstaluje.

### Claude Code

Jako plugin (skill se zaregistruje sám, aktualizace přes plugin manager):

```
/plugin marketplace add LexaurinTheDog/esbirka-skill
/plugin install esbirka@esbirka-skill
```

Nebo ručně do `~/.claude/skills/esbirka`:

```bash
git clone https://github.com/LexaurinTheDog/esbirka-skill.git
cd esbirka-skill && ./install.sh
```

### Codex CLI

```bash
git clone https://github.com/LexaurinTheDog/esbirka-skill.git
cd esbirka-skill && ./install.sh --codex        # → ~/.codex/skills/esbirka
```

### Ostatní agenti (Cursor, Gemini CLI, OpenCode, Amp …)

Skill je v adresáři `skills/esbirka/` ve standardním rozvržení Agent Skills (`SKILL.md` + `scripts/`,
`reference/`). Použijte instalátor skillů vašeho agenta, nebo:

```bash
npx skills add LexaurinTheDog/esbirka-skill          # univerzální CLI pro Agent Skills
./install.sh --agents                                # → ~/.agents/skills/esbirka
./install.sh --dir .claude/skills                    # do konkrétního projektu
./install.sh --all                                   # Claude + Codex + ~/.agents
```

Instalátor navíc vytvoří spouštěč `esbirka` v `~/.local/bin`, takže skript funguje i mimo agenta jako běžný
příkaz. `./install.sh --check` jen zkontroluje stav.

## API klíč (doporučeno, není nutný)

E-Sbírka nabízí registrované REST API na `api.e-sbirka.gov.cz`. Klíč přiděluje Ministerstvo vnitra
(odbor strategického rozvoje a koordinace veřejné správy) na žádost o registraci odběru dat zaslanou
datovou schránkou; odpověď přijde jako dopis s podmínkami užití a klíčem. Technická podpora API:
esel@spcss.cz. Podrobnosti: https://www.e-sbirka.cz/rest-api (přesměruje na e-sbirka.gov.cz).

```bash
cp skills/esbirka/esbirka.env.example ~/.claude/esbirka.env
chmod 600 ~/.claude/esbirka.env
# do souboru doplňte: ESBIRKA_API_KEY=<klíč>   (bez uvozovek a mezer)
esbirka diagnose
```

Soubor s klíčem může být i v `~/.config/esbirka/esbirka.env` nebo na cestě v proměnné `ESBIRKA_ENV`.
Klíč se posílá v HTTP hlavičce `esel-api-access-key` (dopis MV název hlavičky neuvádí).

**Bez klíče** skript automaticky používá veřejnou cache portálu (`e-sbirka.gov.cz/sbr-cache`), kterou čte
sám web e-Sbírky. Data i cesty jsou totožné; rozhraní ale není určeno pro strojové odběry a MV k němu
neposkytuje podporu. Pro pravidelné použití si klíč vyřiďte.

Podmínky užití API podle dopisu MV ve zkratce: klíč jen pro vlastní organizaci a účel z žádosti, nesdílet,
nepřetěžovat API nad nahlášený počet volání, data jsou informativní a mohou se měnit.

## Příkazy

| Příkaz | Co dělá | Důležité volby |
|---|---|---|
| `search DOTAZ` | fulltextové vyhledání předpisů, nálezů ÚS, sdělení a smluv | `--pocet`, `--start`, `--json` |
| `info PŘEDPIS` | metadata znění: úplná citace, interval účinnosti, novely, zrušení, částka | `--k DATUM`, `--json` |
| `zneni PŘEDPIS` | historie všech časových znění včetně budoucích | `--json` |
| `obsah PŘEDPIS` | systematika (části, hlavy, díly) s rozsahem paragrafů | `--k`, `--uzel ID` |
| `par PŘEDPIS "§ N"` | text ustanovení včetně odstavců a písmen | `--k`, `--format md/text/html/json` |
| `text PŘEDPIS` | celý text znění nebo souvislý rozsah | `--od "§ A" --do "§ B"`, `--k`, `--format` |
| `diff PŘEDPIS --z D1 --k D2` | rozdíly mezi zněními s vyznačením vloženého a vypuštěného textu | `--par "§ N"`, `--json` |
| `souvislosti PŘEDPIS` | novelizuje, je novelizován, ruší, je rušen, provádí, nálezy ÚS | `--typ`, `--limit` |
| `castka SBÍRKA ROK ČÍSLO` | metadata částky a odkaz na právně závazné PDF | `--json` |
| `raw GET/POST CESTA [JSON]` | libovolný endpoint (viz `skills/esbirka/reference/api.md`) | |
| `diagnose` | ověření klíče, hlavičky a dostupnosti | |

Předpis: `89/2012`, `89/2012 Sb.`, `č. 89/2012 Sb.`, `6/2021 Sb. m. s.`, `/sb/2012/89`. Ustanovení: `"§ 2079"`,
`"§ 2079 odst. 2"`, `"§ 310 písm. c)"`, `"čl. 10"` nebo jen `2079`. Datum: `2020-05-01` i `1. 5. 2020`;
znamená znění účinné k tomuto dni. Globální přepínače: `--verejne` (vynutit cache portálu), `--no-cache`, `-v`.

Ukázka (`esbirka info 40/1964 --k 2013-06-01`):

```
Zákon č. 40/1964 Sb., Občanský zákoník
minulé znění, účinné od 1. 1. 2013 do 31. 12. 2013  (staleUrl /sb/1964/40/2013-01-01, ELI /eli/cz/sb/1964/40/2013-01-01)
ZRUŠEN k 1. 1. 2014 předpisem 89/2012 Sb.
novely tohoto znění: 428/2011 Sb.
```

## Obsah repozitáře

| Cesta | Účel |
|---|---|
| `skills/esbirka/SKILL.md` | instrukce pro agenta: kdy skill použít, postup, pravidla citace |
| `skills/esbirka/AGENTS.md` | průvodce pro agenty: rozhodovací strom, recepty, tvar výstupů, chyby |
| `skills/esbirka/scripts/esbirka.py` | CLI klient (Python 3.9+, pouze standardní knihovna) |
| `skills/esbirka/reference/api.md` | katalog REST endpointů, filtrů a číselníků e-Sbírky |
| `skills/esbirka/esbirka.env.example` | šablona souboru s klíčem |
| `skills/esbirka/agents/openai.yaml` | metadata pro Codex |
| `install.sh` | instalace do Claude Code / Codex / libovolného adresáře |
| `.claude-plugin/` | manifest pluginu a marketplace pro Claude Code |

## Jak to funguje

Skript volá REST rozhraní e-Sbírky (`/dokumenty-sbirky/{staleUrl}`, `/historie`, `/fragmenty`,
`/nabidka-ustanoveni`, `/rozdilove-fragmenty`, `/souvislosti`, `POST /jednoducha-vyhledavani` …).
Identifikátorem je `staleUrl` ve tvaru `/sb/2012/89/2020-05-01`, kde datum značí znění účinné k tomuto dni.
Text předpisu přichází po stránkách o 1000 fragmentech s hierarchií v ELI; skript je skládá, u kodexů první
stažení trvá několik sekund a výsledek 7 dní drží v `~/.cache/esbirka/`.

API s klíčem nenabízí systematiku, srovnání znění a přehled znění ke srovnání; tyto dotazy skript
automaticky posílá do cache portálu. Kompletní popis rozhraní včetně rozdílů je v `skills/esbirka/reference/api.md`.
Oficiální dokumentace API na webu MV v době vzniku (9/2026) nebyla dostupná; katalog vznikl z funkční
specifikace veřejného API (registr smluv) a z klienta portálu a každý endpoint je ověřen živě.

## Řešení potíží

| Projev | Řešení |
|---|---|
| `401 NEPLATNY_API_KLIC: Nezaslán API klíč` | `esbirka diagnose`; případně `ESBIRKA_AUTH=header:esel-api-access-key` v env souboru |
| `400 DOKUMENT_NENALEZEN … /sb/1964/40/2026-01-01` | k datu předpis nebyl účinný; `esbirka zneni` ukáže platné intervaly |
| `Ustanovení '§ 5' … nenalezeno` | předpis je členěn na články (`"čl. 5"`) nebo ustanovení v tomto znění neexistuje; `esbirka obsah` |
| první `par`/`text` u kodexu trvá 5–15 s | stahuje se text po stránkách; další dotazy jdou z cache |
| `Chyba spojení` | výpadek sítě nebo API; zkuste `--verejne` |

## Právní upozornění

Konsolidovaná znění v e-Sbírce jsou úřední konsolidací MV a podle podmínek užití API jsou informativní.
Právně závazné je vyhlášené znění v částce Sbírky (`esbirka castka` vrací odkaz na podepsané PDF).
Projekt není dílem Ministerstva vnitra ani s ním není spojen. Výstupy nejsou právní službou; před použitím
v podání je ověřte.

## Přispívání

Chyby a návrhy vítány v Issues. Pravidla: žádné klíče ani osobní údaje v kódu, příkladech a testech;
každou změnu chování skriptu ověřte živě proti e-Sbírce a aktualizujte `reference/api.md`, pokud se
rozhraní chová jinak, než je popsáno. CI kontroluje kompilaci, instalaci a nepřítomnost klíčů.

Licence: MIT.
