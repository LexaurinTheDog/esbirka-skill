# Pokyny pro agenty pracující v tomto repozitáři

Toto je repozitář skillu `esbirka` (dotazy na e-Sbírku). Samotný skill je v `skills/esbirka/`;
průvodce pro agenty, kteří skill **používají**, je `skills/esbirka/AGENTS.md`.

Pro agenty, kteří repozitář **upravují**:

- Skript `skills/esbirka/scripts/esbirka.py` musí zůstat bez závislostí mimo standardní knihovnu a kompatibilní
  s Pythonem 3.9 (viz CI).
- Každou změnu chování ověř živě: `python3 skills/esbirka/scripts/esbirka.py --verejne info 89/2012`
  a `… par 89/2012 "§ 2079 odst. 2"`. Bez klíče skript používá veřejnou cache portálu.
- Zjistíš-li rozdíl mezi popsaným a skutečným chováním rozhraní, oprav `skills/esbirka/reference/api.md`
  a uveď datum ověření.
- Do repozitáře nikdy nepatří API klíč, dopis MV s klíčem, ani osobní údaje. Šablona `esbirka.env.example`
  má hodnotu prázdnou.
- Dokumentace je česky (cílová skupina jsou čeští právníci); v README zůstává krátké anglické shrnutí.
- Instalace: `./install.sh` (Claude Code), `--codex`, `--agents`, `--dir`, `--check`. Změníš-li rozvržení
  adresářů, uprav instalátor, CI i `.claude-plugin/`.
