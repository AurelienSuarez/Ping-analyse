# Récap des classements SQY Ping (API monclub FFTT)

Source : `apiv2.fftt.com`, l'API qui alimente monclub.fftt.com. Non documentée, elle peut changer.
Club SQY PING : n° FFTT `08781477`, id API `40001473`.

À lancer depuis ce dossier :

    # 1. lister les poules de la saison en cours
    python3 -c "import json,urllib.request as u;r=u.Request('https://apiv2.fftt.com/api/pools?group.tour.division.contest.season.current=true&itemsPerPage=100&poolOpponents.opponent.team.clubs.id=40001473',headers={'Accept':'application/ld+json'});json.dump(json.load(u.urlopen(r)),open('sqy_pools.json','w'))"
    # 2. récupérer les scores (mis en cache dans cache/ : videz-le pour rafraîchir)
    mkdir -p cache && python3 collect.py
    # 3. calculer les classements, puis générer la page
    python3 standings.py && python3 render.py

`find_sqy.py` a servi à retrouver l'id API du club.

## Probabilités de montée

    python3 build_site_data.py   # calendrier restant + compositions (utilise cache/)
    python3 collect_clubs.py     # feuilles de match de la phase de tous les clubs des poules (brûlage)
    python3 simulate_v2.py       # 20 000 simulations avec compositions tirées selon le brûlage -> site.json
    python3 render_montee.py     # -> montees-sqy-ping.html et maintien-sqy-ping.html
    python3 comments.py          # ajoute le point équipe par équipe aux deux pages
    python3 combine.py           # -> enjeux-sqy-ping.html (onglets Montée / Descente)

`site_template.html` : ébauche du site complet (une page par équipe), pas encore branchée.

## Brûlage

`lineup.py` applique l'article II.112.1 des règlements sportifs FFTT 2026-2027 : 2 rencontres dans des équipes de numéro inférieur interdisent les équipes de numéro supérieur ; pas de passage entre deux équipes d'un club dans une même poule ; brûlage séparé messieurs / dames.
