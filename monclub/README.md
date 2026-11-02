# Récap des classements SQY Ping (API monclub FFTT)

Source : `apiv2.fftt.com`, l'API qui alimente monclub.fftt.com. Non documentée, elle peut changer.

**Authentification obligatoire** (les requêtes anonymes sont refusées depuis novembre 2026) : exportez vos identifiants monclub avant de lancer les scripts.

    export FFTT_LICENCE_USER='votre identifiant'
    export FFTT_LICENCE_PWD='votre mot de passe'

Tous les appels passent par `fftt_api.py` (`POST /api/login_check`, scope `licence`). Le jeton dure 10 minutes : il reste en mémoire et il est renouvelé automatiquement.
Club SQY PING : n° FFTT `08781477`, id API `40001473`.

À lancer depuis ce dossier :

    # 1. lister les poules de la saison en cours
    python3 -c "import json,fftt_api;json.dump(fftt_api.get('/api/pools?group.tour.division.contest.season.current=true&itemsPerPage=100&poolOpponents.opponent.team.clubs.id=40001473'),open('sqy_pools.json','w'))"
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

## Site en ligne (GitHub Pages)

Le site est servi depuis la branche `gh-pages` : https://aureliensuarez.github.io/Ping-analyse/

Pour le mettre à jour après un nouveau calcul :

    python3 make_standalone.py enjeux-sqy-ping.html /chemin/vers/gh-pages/index.html
    # puis commit + push de la branche gh-pages

## Corrections manuelles

`overrides.json` : joueurs à ajouter à la main (recrue sans feuille de match, etc.), avec leurs points et leur probabilité de présence.

## Progression des jeunes (classement virtuel, tournois compris)

    python3 progression.py --du 2026-10-01 --au 2026-11-30             # affiche le classement et le podium
    python3 progression.py --du 2026-10-01 --au 2026-11-30 --discord   # l'envoie aussi (webhook dans DISCORD_WEBHOOK_URL)

À fournir dans ce dossier (non versionnés) :
- `jeunes.json` : `[{"licence": "1234567", "nom": "Prénom NOM"}, ...]`, généré par `python3 trouver_jeunes.py` (joueurs SQY du Championnat des Jeunes). L'API ne donne pas l'âge des licenciés : un jeune absent de ce championnat (ex. qui ne joue qu'en équipe adulte) est à mettre dans `jeunes_ajouts.json`, même format, repris à chaque relance.
- `bareme.json` (versionné) : la grille de l'article IV.205.1, recopiée du texte de juillet 2021, à confirmer pour 2026-2027.

Toutes les parties de simple de la saison sont comptées (`/api/games`) : championnat, tournois, critérium. Chaque résultat est multiplié par le coefficient de sa compétition, lu dans l'API. C'est une estimation : l'API ne fournit pas les points mensuels de référence, on prend les points affichés dans chaque partie.
