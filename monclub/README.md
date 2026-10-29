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
    python3 simulate.py          # 20 000 simulations des fins de phase -> site.json
    python3 render_montee.py     # -> montees-sqy-ping.html et maintien-sqy-ping.html
    python3 comments.py          # ajoute le point équipe par équipe aux deux pages

`site_template.html` : ébauche du site complet (une page par équipe), pas encore branchée.
