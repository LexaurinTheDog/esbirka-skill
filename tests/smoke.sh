#!/usr/bin/env bash
# Kouřové testy proti živé e-Sbírce. Použití: tests/smoke.sh [cesta k esbirka.py]
# Bez klíče běží proti veřejné cache portálu; s klíčem (esbirka.env) proti API.
set -u
S="${1:-$(dirname "$0")/../skills/esbirka/scripts/esbirka.py}"
pass=0; fail=0
chk() { local label="$1" pat="$2"; shift 2
  if [ "$label" = "výpadek→browser" ]; then out=$(ESBIRKA_BASE=https://127.0.0.1:9 ESBIRKA_PUBLIC_BASE=https://127.0.0.1:9 python3 "$S" "$@" 2>&1); else out=$(python3 "$S" "$@" 2>&1); fi
  if printf '%s' "$out" | grep -q -E "$pat"; then echo "PASS  $label"; pass=$((pass+1))
  else echo "FAIL  $label (očekáváno /$pat/)"; printf '%s\n' "$out" | tail -3; fail=$((fail+1)); fi; }

chk "search"          "182/2006 Sb\."                          search "insolvenční zákon" --pocet 3
chk "info aktuální"   "aktuální znění"                          info 89/2012
chk "info --k"        "1\. 6\. 2019 do 30\. 9\. 2019"           info 182/2006 --k 1.6.2019
chk "info zrušený"    "ZRUŠEN k 1\. 1\. 2014"                   info 40/1964
chk "zneni"           "AKTUÁLNÍ"                                zneni 182/2006
chk "obsah"           "ČÁST PRVNÍ"                              obsah 182/2006
chk "obsah --uzel"    "HLAVA I"                                 obsah 89/2012 --uzel 645208419
chk "par §"           "Kupní smlouvou se prodávající"           par 89/2012 "§ 2079" --format text
chk "par holé číslo"  "Kupní smlouvou"                          par 89/2012 2079 --format text
chk "par odst."       "^\(2\) Neplyne-li"                       par 89/2012 "§ 2079 odst. 2" --format text
chk "par --k minulé"  "od 1\. 12\. 2018 do 30\. 6\. 2020"       par 89/2012 "§ 2079" --k 1.5.2020
chk "par čl."         "Vyhlášené mezinárodní smlouvy"           par 1/1993 "čl. 10" --format text
chk "par čl. holé"    "Vyhlášené mezinárodní smlouvy"           par 1/1993 10 --format text
chk "text --od --do"  "§ 2081"                                  text 89/2012 --od 2080 --do 2081 --format text
chk "diff"            "Změněných fragmentů: [1-9]"              diff 89/2012 --z 2025-07-01 --k 2026-01-01 --par "§ 757"
chk "souvislosti"     "JE_RUSEN"                                souvislosti 40/1964 --typ JE_RUSEN
chk "castka"          "overena-zneni/"                          castka sb 2025 100
chk "raw GET"         "historie"                                raw GET "/dokumenty-sbirky/%2Fsb%2F2012%2F89/historie"
chk "raw POST"        "pocetCelkem"                             raw POST /jednoducha-vyhledavani '{"fulltext":"nadace","start":0,"pocet":2}'
chk "chyba data"      "DOKUMENT_NENALEZEN"                      info 40/1964 --k 2026-01-01
chk "json"            '"staleUrl"'                              info 89/2012 --json
chk "diagnose"        "HTTP 200"                                diagnose

if python3 -c 'import playwright' 2>/dev/null; then
  echo "— prohlížeč (Playwright) —"
  chk "ui search"       "85/1996 Sb\."                           --ui search "zákon o advokacii" --pocet 3
  chk "ui par odst."    "^\(2\) Neplyne-li"                       --ui par 89/2012 "§ 2079 odst. 2" --format text
  chk "ui par --k"      "1\. 12\. 2018 - 30\. 6\. 2020"          --ui par 89/2012 "§ 2079" --k 1.5.2020
  chk "browser info"    "1\. 6\. 2019 do 30\. 9\. 2019"           --browser info 182/2006 --k 1.6.2019
  chk "výpadek→browser" "přepínám na dotazy z prohlížeče"        info 89/2012
else
  echo "— prohlížeč (Playwright) není nainstalován, testy záložního režimu přeskočeny —"
fi

echo; echo "Výsledek: $pass PASS, $fail FAIL"
[ "$fail" -eq 0 ]
