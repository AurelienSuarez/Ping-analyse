"""Transforme la page de l'artifact en page HTML autonome pour GitHub Pages."""
import sys
src, dst = sys.argv[1], sys.argv[2]
body = open(src, encoding="utf-8").read()
head = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
*,*::before,*::after{box-sizing:border-box}body{margin:0;font:14px/1.5 system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
"""
# le <title>, les <link> et le <style> de la page restent dans le <head>
cut = body.index("</style>") + len("</style>")
open(dst, "w", encoding="utf-8").write(head + body[:cut] + "\n</head>\n<body>\n" + body[cut:] + "\n</body>\n</html>\n")
