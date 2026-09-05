#!/usr/bin/env bash
# Instalace skillu e-Sbírka pro kódovací agenty.
#
#   ./install.sh                 → Claude Code (~/.claude/skills/esbirka)
#   ./install.sh --codex         → Codex CLI   (~/.codex/skills/esbirka)
#   ./install.sh --agents        → společný adresář ~/.agents/skills/esbirka (standard Agent Skills)
#   ./install.sh --all           → všechny tři
#   ./install.sh --dir CESTA     → libovolný adresář (např. .claude/skills v projektu)
#   ./install.sh --check         → jen zkontroluje, nic nemění
#   ./install.sh --browser       → navíc nainstaluje Playwright + Chromium (záložní režim při výpadku API)
#
# Vždy navíc vytvoří spouštěč `esbirka` v ~/.local/bin (přeskočit: --no-bin).
# Klíč k API se NEinstaluje – patří do ~/.claude/esbirka.env, viz README.
set -uo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills/esbirka"
BIN_DIR="${ESBIRKA_BIN_DIR:-$HOME/.local/bin}"
targets=(); check=0; bin=1; browser=0
while [ $# -gt 0 ]; do
  case "$1" in
    --claude) targets+=("$HOME/.claude/skills/esbirka");;
    --codex)  targets+=("$HOME/.codex/skills/esbirka");;
    --agents) targets+=("$HOME/.agents/skills/esbirka");;
    --all)    targets+=("$HOME/.claude/skills/esbirka" "$HOME/.codex/skills/esbirka" "$HOME/.agents/skills/esbirka");;
    --dir)    shift; targets+=("${1%/}/esbirka");;
    --check)  check=1;;
    --no-bin) bin=0;;
    --browser) browser=1;;
    -h|--help) sed -n '2,15p' "$0"; exit 0;;
    *) echo "neznámý přepínač: $1" >&2; exit 2;;
  esac; shift
done
[ ${#targets[@]} -eq 0 ] && targets=("$HOME/.claude/skills/esbirka")

ok() { printf '  \033[32m✓\033[0m %s\n' "$*"; }
miss() { printf '  \033[33m✗\033[0m %s\n' "$*"; }

echo "▸ Předpoklady"
if command -v python3 >/dev/null 2>&1; then
  v=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
  python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)' && ok "python3 $v" || miss "python3 $v je starší než 3.9"
else
  miss "python3 nenalezen"; exit 1
fi

echo "▸ Skill"
for t in "${targets[@]}"; do
  if [ "$check" = 1 ]; then
    [ -f "$t/SKILL.md" ] && ok "$t" || miss "$t (nenainstalováno)"
    continue
  fi
  mkdir -p "$(dirname "$t")"
  rm -rf "$t"
  cp -R "$SRC" "$t"
  find "$t" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
  chmod +x "$t/scripts/esbirka.py"
  ok "$t"
done

if [ "$bin" = 1 ]; then
  echo "▸ Spouštěč esbirka"
  first="${targets[0]}/scripts/esbirka.py"
  if [ "$check" = 1 ]; then
    command -v esbirka >/dev/null 2>&1 && ok "esbirka → $(command -v esbirka)" || miss "esbirka není v PATH"
  else
    mkdir -p "$BIN_DIR"
    printf '#!/usr/bin/env bash\nexec python3 "%s" "$@"\n' "$first" > "$BIN_DIR/esbirka"
    chmod +x "$BIN_DIR/esbirka"
    ok "$BIN_DIR/esbirka"
    case ":$PATH:" in *":$BIN_DIR:"*) ;; *) miss "$BIN_DIR není v PATH – přidejte do shellu: export PATH=\"$BIN_DIR:\$PATH\"";; esac
  fi
fi

echo "▸ Klíč k API (volitelný)"
found=""
for f in "${ESBIRKA_ENV:-}" "$HOME/.config/esbirka/esbirka.env" "$HOME/.claude/esbirka.env" "$HOME/.codex/esbirka.env"; do
  [ -n "$f" ] && [ -f "$f" ] && { found="$f"; break; }
done
if [ -n "$found" ]; then
  ok "$found"
  perm=$(stat -f '%Lp' "$found" 2>/dev/null || stat -c '%a' "$found" 2>/dev/null)
  [ "$perm" = "600" ] || miss "doporučeno chmod 600 $found (nyní $perm)"
else
  miss "bez klíče – skill použije veřejnou cache portálu; klíč: cp skills/esbirka/esbirka.env.example ~/.claude/esbirka.env"
fi

echo "▸ Záložní režim prohlížeče (Playwright)"
if python3 -c 'import playwright' 2>/dev/null || [ -x "$HOME/.local/share/esbirka/venv/bin/python" ]; then
  ok "Playwright k dispozici"
elif [ "$browser" = 1 ] && [ "$check" = 0 ]; then
  python3 "${targets[0]}/scripts/esbirka.py" setup-browser && ok "Playwright + Chromium nainstalován do ~/.local/share/esbirka/venv" || miss "instalace Playwrightu selhala"
else
  miss "Playwright chybí – při výpadku API nebude záložní režim; doinstalujte: esbirka setup-browser (nebo ./install.sh --browser)"
fi

if [ "$check" = 0 ]; then
  echo "▸ Test"
  python3 "${targets[0]}/scripts/esbirka.py" --help >/dev/null && ok "skript se spouští" || miss "skript se nespustil"
fi
echo; echo "Hotovo. Ověření spojení: esbirka diagnose"
