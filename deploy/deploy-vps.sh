#!/usr/bin/env bash
# Nasazení webové prezentace esbirka-skill na vlastní server s Apache (Debian/Ubuntu).
#
# Spouští se NA SERVERU jako root:
#   ./deploy-vps.sh esbirka-skill.example.com            # první nasazení (klon + vhost + TLS)
#   ./deploy-vps.sh esbirka-skill.example.com --update   # jen aktualizace obsahu (git pull)
#   ./deploy-vps.sh esbirka-skill.example.com --no-tls   # bez certbotu (např. za reverzní proxy)
#
# Co dělá: naklonuje veřejný repozitář do /var/www/<doména>, nastaví Apache vhost s kořenem
# v jeho složce docs/, zapne stránku a vyžádá certifikát Let's Encrypt. Nic mimo tuto doménu
# nemění a existující vhosty nechává být.
set -euo pipefail

REPO="${ESBIRKA_REPO:-https://github.com/LexaurinTheDog/esbirka-skill.git}"
DOMAIN="${1:-}"; shift || true
UPDATE=0; TLS=1
for a in "$@"; do
  case "$a" in
    --update) UPDATE=1;;
    --no-tls) TLS=0;;
    *) echo "neznámý přepínač: $a" >&2; exit 2;;
  esac
done
[ -n "$DOMAIN" ] || { sed -n '2,14p' "$0"; exit 2; }
[ "$(id -u)" = 0 ] || { echo "Spusťte jako root (sudo)." >&2; exit 1; }

SITE="/var/www/$DOMAIN"
WEBROOT="$SITE/docs"
VHOST="/etc/apache2/sites-available/$DOMAIN.conf"
ok(){ printf '  \033[32m✓\033[0m %s\n' "$*"; }
info(){ printf '  \033[33m·\033[0m %s\n' "$*"; }

echo "▸ Obsah → $SITE"
if [ -d "$SITE/.git" ]; then
  git -C "$SITE" fetch --quiet origin && git -C "$SITE" reset --hard --quiet origin/HEAD 2>/dev/null \
    || git -C "$SITE" pull --quiet --ff-only
  ok "aktualizováno na $(git -C "$SITE" log -1 --format=%h\ %s)"
else
  command -v git >/dev/null || { apt-get update -qq && apt-get install -y -qq git; }
  git clone --quiet --depth 1 "$REPO" "$SITE"
  ok "naklonováno $REPO"
fi
[ -f "$WEBROOT/index.html" ] || { echo "✗ chybí $WEBROOT/index.html" >&2; exit 1; }
chown -R www-data:www-data "$SITE"

if [ "$UPDATE" = 1 ]; then
  systemctl reload apache2 && ok "Apache znovu načten"
  echo; echo "Hotovo. Kontrola: curl -sI https://$DOMAIN | head -1"
  exit 0
fi

echo "▸ Apache vhost"
if [ -f "$VHOST" ]; then
  info "$VHOST už existuje – ponechávám beze změny"
else
  SRC="$(dirname "$(readlink -f "$0")")/apache-vhost.conf.example"
  [ -f "$SRC" ] || SRC="$SITE/deploy/apache-vhost.conf.example"
  sed -e "s|DOMAIN|$DOMAIN|g" -e "s|WEBROOT|$WEBROOT|g" "$SRC" > "$VHOST"
  ok "vytvořen $VHOST"
fi
a2enmod -q headers expires >/dev/null 2>&1 || true
a2ensite -q "$DOMAIN.conf" >/dev/null
apache2ctl configtest 2>&1 | grep -qi "syntax ok" || { echo "✗ chyba v konfiguraci Apache" >&2; apache2ctl configtest; exit 1; }
systemctl reload apache2
ok "stránka zapnuta a Apache znovu načten"

if [ "$TLS" = 1 ]; then
  echo "▸ TLS certifikát"
  if ! command -v certbot >/dev/null; then
    apt-get update -qq && apt-get install -y -qq certbot python3-certbot-apache
  fi
  if certbot certificates 2>/dev/null | grep -q "Domains:.*\b$DOMAIN\b"; then
    info "certifikát pro $DOMAIN už existuje"
  elif certbot --apache -n --agree-tos --redirect -d "$DOMAIN" --register-unsafely-without-email 2>/dev/null \
       || certbot --apache -n --agree-tos --redirect -d "$DOMAIN"; then
    ok "certifikát vystaven, HTTP přesměrováno na HTTPS"
  else
    info "certbot neuspěl – ověřte, že $DOMAIN míří na tento server (A záznam), a spusťte: certbot --apache -d $DOMAIN"
  fi
fi

echo
echo "Hotovo:  https://$DOMAIN/"
echo "Aktualizace obsahu později:  $0 $DOMAIN --update"
