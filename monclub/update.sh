#!/usr/bin/env bash
# Mise à jour complète du site Enjeux SQY Ping : collecte FFTT, calibrage, simulation, pages.
# Usage : bash monclub/update.sh   (le site autonome est écrit dans monclub/site/index.html)
set -euo pipefail
cd "$(dirname "$0")"

rm -rf cache && mkdir -p cache site

echo "== 1/7 Poules de SQY Ping (saison en cours)"
python3 - <<'EOF'
import json, urllib.request
r = urllib.request.Request("https://apiv2.fftt.com/api/pools?group.tour.division.contest.season.current=true&itemsPerPage=100&poolOpponents.opponent.team.clubs.id=40001473",
                           headers={"Accept": "application/ld+json"})
d = json.load(urllib.request.urlopen(r, timeout=90))
json.dump(d, open("sqy_pools.json", "w"))
print(d["hydra:totalItems"], "poules")
EOF

echo "== 2/7 Rencontres et feuilles de match des poules SQY"
python3 collect.py > /dev/null
python3 build_site_data.py

echo "== 3/7 Feuilles de match des clubs adverses (brûlage)"
python3 collect_clubs.py | tail -1

echo "== 4/7 Calibrage du modèle"
python3 calibrate.py

echo "== 5/7 Simulation"
python3 simulate_v3.py

echo "== 6/7 Contrôles avant publication"
python3 - <<'EOF'
import json, sys
site = json.load(open("site.json"))
n_sqy = sum(len(p["sqy"]) for p in site)
no_compo = [t["name"] for p in site for k, t in p["teams"].items() if not (p["compo"].get(k) or {}).get("probable")]
cal = json.load(open("calibration.json"))
problems = []
if n_sqy < 20: problems.append(f"seulement {n_sqy} équipes SQY trouvées")
if len(no_compo) > 5: problems.append(f"{len(no_compo)} équipes sans composition")
if not (200 <= cal["D_simple"] <= 600): problems.append(f"calibrage anormal (D={cal['D_simple']})")
if problems:
    print("ÉCHEC DES CONTRÔLES :", "; ".join(problems)); sys.exit(1)
print(f"OK : {n_sqy} équipes SQY, {len(no_compo)} équipe(s) sans composition, D={cal['D_simple']}")
EOF

echo "== 7/7 Pages"
python3 render_montee.py > /dev/null
python3 comments.py
python3 weekly_summary.py
python3 combine.py > /dev/null
python3 make_standalone.py enjeux-sqy-ping.html site/index.html
printf "User-agent: *\nDisallow: /\n" > site/robots.txt
touch site/.nojekyll
echo "Site prêt : monclub/site/index.html"
