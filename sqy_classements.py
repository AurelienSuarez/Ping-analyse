#!/usr/bin/env python3
"""Récap des classements des équipes d'un club via l'API SmartPing de la FFTT.

Prérequis :
  - accès réseau à www.fftt.com
  - identifiants API SmartPing (demande à faire auprès de la FFTT) :
      export FFTT_ID=SWxxxx FFTT_PWD=motdepasse

Usage :
  python3 sqy_classements.py --cherche "SQY"        # trouve le numéro du club (dép. 78)
  python3 sqy_classements.py --club 0878xxxx        # récap des classements
  python3 sqy_classements.py --club 0878xxxx --md recap.md
"""
import argparse
import datetime
import hashlib
import hmac
import os
import random
import string
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://www.fftt.com/mobile/pxml/"


class SmartPing:
    def __init__(self, app_id, password):
        self.app_id = app_id
        self.key = hashlib.md5(password.encode()).hexdigest()
        self.serie = os.environ.get("FFTT_SERIE") or "".join(
            random.choices(string.ascii_uppercase + string.digits, k=15)
        )
        self._initialised = False

    def _auth(self):
        tm = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
        tmc = hmac.new(self.key.encode(), tm.encode(), hashlib.sha1).hexdigest()
        return {"serie": self.serie, "tm": tm, "tmc": tmc, "id": self.app_id}

    def get(self, script, **params):
        if not self._initialised and script != "xml_initialisation.php":
            self._initialised = True
            self.get("xml_initialisation.php")
        query = urllib.parse.urlencode({**self._auth(), **params})
        with urllib.request.urlopen(f"{BASE}{script}?{query}", timeout=30) as r:
            raw = r.read()
        # L'API répond en ISO-8859-1
        return ET.fromstring(raw.decode("iso-8859-1").encode("utf-8"))


def text(node, tag):
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def cherche_club(api, nom, dep):
    for club in api.get("xml_club_dep2.php", dep=dep).iter("club"):
        if nom.lower() in text(club, "nom").lower():
            print(f"{text(club, 'numero')}  {text(club, 'nom')}")


def equipes(api, club):
    for type_ in ("M", "F"):
        for eq in api.get("xml_equipe.php", numclu=club, type=type_).iter("equipe"):
            # liendivision ressemble à "cx_poule=123&D1=456&organisme_pere=78"
            lien = urllib.parse.parse_qs(text(eq, "liendivision"))
            yield {
                "equipe": text(eq, "libequipe"),
                "division": text(eq, "libdivision"),
                "poule": lien.get("cx_poule", [""])[0],
                "d1": lien.get("D1", [""])[0],
            }


def classement(api, d1, poule):
    root = api.get(
        "xml_result_equ.php", action="classement", auto="1", D1=d1, cx_poule=poule
    )
    return [
        {
            "clt": text(c, "clt"),
            "equipe": text(c, "equipe"),
            "joue": text(c, "joue"),
            "pts": text(c, "pts"),
            "vic": text(c, "vic"),
            "nul": text(c, "nul"),
            "def": text(c, "def"),
        }
        for c in root.iter("classement")
    ]


def recap(api, club, nom_club):
    lignes = ["# Classements des équipes", ""]
    for eq in equipes(api, club):
        lignes += [f"## {eq['equipe']} — {eq['division']}", ""]
        if not eq["d1"]:
            lignes += ["_Pas de poule associée._", ""]
            continue
        lignes += ["| Clt | Équipe | J | V | N | D | Pts |", "|---|---|---|---|---|---|---|"]
        for c in classement(api, eq["d1"], eq["poule"]):
            nom = c["equipe"]
            if nom_club.lower() in nom.lower():
                nom = f"**{nom}**"
            lignes.append(
                f"| {c['clt']} | {nom} | {c['joue']} | {c['vic']} | {c['nul']} | {c['def']} | {c['pts']} |"
            )
        lignes.append("")
    return "\n".join(lignes)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--club", help="numéro FFTT du club")
    p.add_argument("--cherche", help="rechercher un club par nom")
    p.add_argument("--dep", default="78", help="département pour --cherche")
    p.add_argument("--nom", default="SQY", help="texte pour surligner le club")
    p.add_argument("--md", help="écrire le récap dans ce fichier Markdown")
    args = p.parse_args()

    app_id, pwd = os.environ.get("FFTT_ID"), os.environ.get("FFTT_PWD")
    if not app_id or not pwd:
        sys.exit("Définir FFTT_ID et FFTT_PWD (identifiants API SmartPing).")
    api = SmartPing(app_id, pwd)

    if args.cherche:
        cherche_club(api, args.cherche, args.dep)
    elif args.club:
        out = recap(api, args.club, args.nom)
        if args.md:
            with open(args.md, "w", encoding="utf-8") as f:
                f.write(out)
        print(out)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
