#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generer_site.py — Génère le sous-site « aubaines.chasseursdedealsqc.com »
=========================================================================

Lit les aubaines depuis la feuille Google publiée (Site_Aubaines) et produit
un site statique optimisé pour Google, Bing ET les robots des IA :

  - index.html                 la page d'accueil (jusqu'à 1000 aubaines, photo obligatoire)
  - aubaine/<slug>.html        une page par aubaine, indexable
  - sitemap.xml                le plan du site (soumis à Google/Bing)
  - robots.txt                 ouvert aux moteurs et aux IA (GPTBot, ClaudeBot…)
  - llms.txt                   résumé du site pour les IA (norme émergente)

Chaque page pointe vers l'aubaine Amazon (lien affilié) et vers la page
Facebook « Chasseurs de Deals Québec ». Prévu pour tourner chaque matin sur
GitHub Actions, juste après la reconstruction Make de 5 h.

Dépendances : requests (seulement). Python 3.9+.
"""

import csv
import html
import io
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Identifiant du fichier Google Sheets et de la feuille « Site_Aubaines ».
SHEET_ID = "16kg2Kjn7jBLJ0fxIrw6Yg85A5dNRK6piX5Effa8aK7w"
SHEET_GID = "543278811"

# Deux façons de lire la feuille publiée. On essaie la première, puis l'autre.
CSV_URLS = [
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={SHEET_GID}",
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}",
]

# Adresses publiques.
DOMAINE = "https://aubaines.chasseursdedealsqc.com"
PAGE_FACEBOOK = "https://www.facebook.com/ChasseursDeDealsQc"
SITE_PRINCIPAL = "https://www.chasseursdedealsqc.com"

# Infolettre : webhook Make qui ajoute l'abonné à la liste Brevo.
INFOLETTRE_HOOK = "https://hook.us2.make.com/jc2sk18m25gcbykk8xf6fa7aokeudccy"


def formulaire_infolettre(site: str, compact: bool = False) -> str:
    """Bloc d'inscription à l'infolettre (POST url-encodé → webhook Make)."""
    titre = "" if compact else (
        '<h2>📬 L\'infolettre des aubaines</h2>'
        '<p>Reçois chaque matin les meilleures aubaines du jour, directement '
        'dans ta boîte courriel. Gratuit, désabonnement en un clic.</p>')
    return (
        '<section class="infolettre' + (' compacte' if compact else '') + '">'
        + titre +
        '<form class="inf-form" onsubmit="return _inf(this)">'
        '<input type="email" name="email" required placeholder="Ton adresse courriel">'
        '<button type="submit">Je m\'abonne</button>'
        '</form>'
        '<p class="inf-ok" hidden>Merci ! Tu recevras l\'infolettre dès demain matin. 🎉</p>'
        '<script>function _inf(f){var e=f.email.value;'
        'fetch("' + INFOLETTRE_HOOK + '",{method:"POST",mode:"no-cors",'
        'headers:{"Content-Type":"application/x-www-form-urlencoded"},'
        'body:"email="+encodeURIComponent(e)+"&site=' + site + '"});'
        'f.hidden=true;f.parentNode.querySelector(".inf-ok").hidden=false;return false;}</script>'
        '</section>')


# Notifications push OneSignal (app « Chasseurs de Deals - Aubaines »).
ONESIGNAL_APP_ID = "a5d68a4c-b078-4294-921f-53a46cbf1e7a"
ONESIGNAL = (
    '<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>'
    '<script>window.OneSignalDeferred=window.OneSignalDeferred||[];'
    'OneSignalDeferred.push(async function(OneSignal){await OneSignal.init({appId:"'
    + ONESIGNAL_APP_ID + '"});});</script>'
)

NB_AUBAINES = 1000        # nombre de pages à générer (les meilleurs rabais)
FUSEAU = timezone(timedelta(hours=-4))  # heure de l'Est

# Balise de vérification Google Search Console (jeton propre au compte Google —
# la même balise valide toutes les propriétés du compte).
GOOGLE_VERIF = ('<meta name="google-site-verification" '
                'content="737lfq2zJvydj4UTXGY0UncdQNHKiuT1RN5XDP0UYAw">')
# Balise de vérification Pinterest — permet de revendiquer le domaine sur Pinterest
GOOGLE_VERIF += '<meta name="p:domain_verify" content="643106277e09e6d158eaa73f88c1bf3c">'

SORTIE = Path(__file__).resolve().parent / "public"

# rootCat Amazon.ca → nom de catégorie lisible (best-effort ; « Aubaines » sinon).
CATEGORIES = {
    "6205517011": "Mode",
    "21204935011": "Mode",
    "2206275011": "Maison et cuisine",
    "3006902011": "Outils et bricolage",
    "6205499011": "Sports et plein air",
    "2242989011": "Sports et plein air",
    "6967215011": "Auto",
    "667823011": "Électronique",
    "3198031": "Électronique",
    "6205511011": "Jouets et jeux",
}

# Pages catégories PERMANENTES (URL stables pour Google, contenu regénéré
# chaque matin avec les aubaines du jour).
CATS_PAGES = [
    ("Électronique", "electronique"),
    ("Maison et cuisine", "maison-cuisine"),
    ("Mode", "mode"),
    ("Jouets et jeux", "jouets-jeux"),
    ("Sports et plein air", "sports-plein-air"),
    ("Outils et bricolage", "outils-bricolage"),
    ("Auto", "auto"),
    ("Aubaines", "autres-aubaines"),
]
CATS_LIBELLES = {"Aubaines": "Autres aubaines"}  # libellé affiché pour le fallback


# ---------------------------------------------------------------------------
# Lecture des données
# ---------------------------------------------------------------------------

def slugifier(texte: str, asin: str) -> str:
    t = unicodedata.normalize("NFKD", texte or "").encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    t = t[:60].strip("-") or "aubaine"
    return f"{t}-{asin.lower()}"


def nombre(v: str):
    v = re.sub(r"[^\d.,-]", "", str(v or "")).replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


# --- Regroupement des variantes (même produit, grandeurs différentes) --------
# On retire du titre les mentions de taille / format / quantité, puis on
# regroupe les produits qui ne diffèrent que par la grandeur pour ne garder
# que la variante LA MOINS CHÈRE.
_MOTS_TAILLE = re.compile(
    r"\b("
    r"\d+(?:[.,]\d+)?\s?(?:mm|cm|m|in|inch|inches|ft|pi|po|pouces?|"
    r"ml|l|litres?|cl|g|kg|mg|oz|lb|lbs)"                          # mesures + unité
    r"|(?:pack|paquet|lot|ensemble|set|paq)\s?(?:of|de|d')?\s?\d+"  # pack de N
    r"|\d+\s?(?:x|pack|paquet|pi[eè]ces?|pcs?|ct|count|unit[eé]s?|mcx)"  # N pièces
    r"|(?:taille|size|pointure|us|eu|uk|eur|fr)\s?\d+(?:[.,]\d+)?"   # taille numérique
    r"|(?:taille|size)\s?(?:s|m|l|x{1,3}(?:s|l)|xs|xl|xxl|"
    r"small|medium|large|petit|moyen|grand)"                       # taille + lettre/mot
    r"|x{1,3}(?:s|l)|xxl|xs|small|medium|large|"
    r"one\s?size|taille\s?unique"                                  # tailles seules
    r")\b",
    re.IGNORECASE,
)


def cle_variante(titre: str) -> str:
    t = unicodedata.normalize("NFKD", titre or "").encode("ascii", "ignore").decode().lower()
    t = _MOTS_TAILLE.sub(" ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    t = re.sub(r"\s+", " ", t)
    # Si le nettoyage réduit trop le titre, on retombe sur le titre complet
    # pour ne pas fusionner par erreur deux produits différents.
    return t if len(t) >= 12 else (titre or "").strip().lower()


def choisir_moins_cher(items: list) -> dict:
    avec_prix = [x for x in items if x.get("prix") is not None]
    if avec_prix:
        return min(avec_prix, key=lambda x: x["prix"])
    return max(items, key=lambda x: x["rabais"])


def lire_aubaines() -> list:
    dernier = None
    for url in CSV_URLS:
        try:
            r = requests.get(url, timeout=45)
            r.raise_for_status()
            r.encoding = "utf-8"
            texte = r.text
            if "<html" in texte[:200].lower():
                raise ValueError("réponse HTML au lieu du CSV (feuille non publiée ?)")
            break
        except (requests.RequestException, ValueError) as e:
            dernier = e
            texte = None
    if texte is None:
        raise SystemExit(f"ERREUR : impossible de lire la feuille publiée ({dernier}).")

    aubaines = []
    for ligne in csv.reader(io.StringIO(texte)):
        if len(ligne) < 9:
            continue
        date, asin, titre, rabais, prix, lien, etiquette, statut, rootcat = ligne[:9]
        asin = (asin or "").strip()
        if not re.fullmatch(r"[A-Z0-9]{10}", asin):
            continue  # ignore l'en-tête ou les lignes vides
        if (statut or "").strip().lower() not in ("actif", "", "aubaine du jour"):
            continue
        aubaines.append({
            "asin": asin,
            "titre": (titre or "").strip() or "Aubaine",
            "rabais": nombre(rabais) or 0,
            "prix": nombre(prix),
            "lien": (lien or "").strip(),
            "categorie": CATEGORIES.get((rootcat or "").strip(), "Aubaines"),
        })

    # 1) Dédoublonnage strict par ASIN.
    par_asin = {}
    for a in aubaines:
        par_asin.setdefault(a["asin"], a)

    # 2) Regroupe les variantes (même produit, grandeurs différentes) et ne
    #    garde que la MOINS CHÈRE de chaque groupe.
    groupes = {}
    for a in par_asin.values():
        groupes.setdefault(cle_variante(a["titre"]), []).append(a)
    retenues = [choisir_moins_cher(g) for g in groupes.values()]

    # 3) Meilleurs rabais d'abord, puis slug + image.
    retenues.sort(key=lambda x: x["rabais"], reverse=True)
    for a in retenues:
        a["slug"] = slugifier(a["titre"], a["asin"])
        a["image"] = f"https://images-na.ssl-images-amazon.com/images/P/{a['asin']}.01._SCLZZZZZZZ_.jpg"

    # 4) LA PHOTO EST OBLIGATOIRE. Une annonce sans image ne s'affiche pas.
    #    Amazon ne renvoie pas d'erreur pour une image absente : il renvoie un
    #    GIF d'un seul pixel, à peine quelques dizaines d'octets. On mesure.
    retenues = garder_avec_photo(retenues)
    return retenues[:NB_AUBAINES]


def garder_avec_photo(aubaines):
    """Ne garde que les aubaines dont l'image Amazon existe vraiment."""
    from concurrent.futures import ThreadPoolExecutor

    def a_une_photo(a):
        try:
            r = requests.head(a["image"], timeout=8, allow_redirects=True)
            taille = int(r.headers.get("Content-Length") or 0)
            if r.status_code != 200:
                return False
            if taille:            # le GIF « image absente » fait ~40 octets
                return taille > 1000
            # Pas de Content-Length ? On lit le début du fichier pour trancher.
            g = requests.get(a["image"], timeout=8, stream=True)
            morceau = next(g.iter_content(2048), b"")
            g.close()
            return len(morceau) > 1000
        except requests.RequestException:
            # Dans le doute (réseau qui tousse), on garde : le filet
            # côté navigateur retirera la carte si l'image ne vient pas.
            return True

    with ThreadPoolExecutor(max_workers=16) as pool:
        verdicts = list(pool.map(a_une_photo, aubaines))
    gardees = [a for a, ok in zip(aubaines, verdicts) if ok]
    retirees = len(aubaines) - len(gardees)
    if retirees:
        print(f"{retirees} aubaine(s) sans photo écartée(s) — la photo est obligatoire.")
    return gardees


# ---------------------------------------------------------------------------
# Génération des pages
# ---------------------------------------------------------------------------

def e(s) -> str:
    return html.escape(str(s), quote=True)


def prix_txt(a) -> str:
    return f"{a['prix']:.2f} $".replace(".", ",") if a["prix"] else "Voir le prix"


def page_aubaine(a, maj_iso: str) -> str:
    titre_page = f"{a['titre']} — {round(a['rabais'])} % de rabais | Chasseurs de Deals Québec"
    desc = (f"{a['titre']} en aubaine à {prix_txt(a)} "
            f"({round(a['rabais'])} % de rabais). Repéré par Chasseurs de Deals Québec.")
    url = f"{DOMAINE}/aubaine/{a['slug']}.html"
    jsonld = (
        '{"@context":"https://schema.org/","@type":"Product",'
        f'"name":{q(a["titre"])},"image":{q(a["image"])},'
        f'"description":{q(desc)},"sku":{q(a["asin"])},'
        '"offers":{"@type":"Offer","priceCurrency":"CAD",'
        + (f'"price":"{a["prix"]:.2f}",' if a["prix"] else "")
        + f'"url":{q(a["lien"])},"availability":"https://schema.org/InStock"}}}}'
    )
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titre_page)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="product">
<meta property="og:title" content="{e(a['titre'])}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(a['image'])}">
<meta property="og:url" content="{e(url)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<script type="application/ld+json">{jsonld}</script>
<style>{CSS}</style>
{GOOGLE_VERIF}
{ONESIGNAL}
</head>
<body>
<header><a class="logo" href="/">🔥 Chasseurs de Deals Québec</a>
<a class="fb" href="{e(PAGE_FACEBOOK)}" rel="noopener">Suivre la page Facebook</a></header>
<main>
<nav class="fil"><a href="/">Accueil</a> › <span>{e(a['categorie'])}</span></nav>
<article class="fiche">
<img src="{e(a['image'])}" alt="{e(a['titre'])}" loading="lazy"
 onerror="this.style.display='none'">
<div class="info">
<span class="cat">{e(a['categorie'])}</span>
<h1>{e(a['titre'])}</h1>
<p class="prix">{e(prix_txt(a))} <span class="rabais">−{round(a['rabais'])} %</span></p>
<a class="cta" href="{e(a['lien'])}" rel="nofollow sponsored noopener" target="_blank">
Voir l'aubaine sur Amazon →</a>
<p class="avis">En tant que Partenaire Amazon, Chasseurs de Deals Québec est rémunéré
pour les achats admissibles. Le prix affiché peut avoir changé.</p>
<a class="fb2" href="{e(PAGE_FACEBOOK)}" rel="noopener">
Les meilleurs deals chaque jour → notre page Facebook</a>
</div>
</article>
{formulaire_infolettre("aubaines", compact=True)}
</main>
<footer>Mis à jour le {e(maj_iso)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a></footer>
</body></html>"""


def q(s) -> str:
    """Chaîne JSON sûre pour le JSON-LD."""
    import json
    return json.dumps(str(s), ensure_ascii=False)


def cartes_html(aubaines) -> str:
    return "\n".join(f"""<a class="carte" href="/aubaine/{e(a['slug'])}.html">
<img src="{e(a['image'])}" alt="{e(a['titre'])}" loading="lazy"
 onload="if(this.naturalWidth<2)this.closest('.carte').remove()"
 onerror="this.closest('.carte').remove()">
<span class="rabais">−{round(a['rabais'])} %</span>
<span class="cat">{e(a['categorie'])}</span>
<span class="t">{e(a['titre'][:70])}</span>
<span class="p">{e(prix_txt(a))}</span></a>""" for a in aubaines)


def chips_html(active_slug: str = "") -> str:
    chips = []
    for nom, slug in CATS_PAGES:
        lib = CATS_LIBELLES.get(nom, nom)
        cls = "chip actif" if slug == active_slug else "chip"
        chips.append(f'<a class="{cls}" href="/categorie/{slug}.html">{e(lib)}</a>')
    return '<nav class="chips">' + "".join(chips) + "</nav>"


def page_categorie(nom, slug, items, maj_lisible) -> str:
    lib = CATS_LIBELLES.get(nom, nom)
    desc = (f"Les meilleures aubaines Amazon « {lib} » au Québec, mises à jour chaque matin "
            f"par Chasseurs de Deals Québec. Rabais vérifiés du jour.")
    contenu = (f'<section class="grille">{cartes_html(items)}</section>' if items else
               '<p class="vide">Aucune aubaine dans cette catégorie aujourd\'hui — '
               'les aubaines changent chaque matin, reviens demain ! '
               '<a href="/">Voir toutes les aubaines du jour →</a></p>')
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aubaines {e(lib)} au Québec — rabais du jour | Chasseurs de Deals</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(DOMAINE)}/categorie/{slug}.html">
<meta name="robots" content="index,follow,max-image-preview:large">
<style>{CSS}</style>
{GOOGLE_VERIF}
{ONESIGNAL}
</head>
<body>
<header><a class="logo" href="/">🔥 Chasseurs de Deals Québec</a>
<a class="fb" href="{e(PAGE_FACEBOOK)}" rel="noopener">Suivre la page Facebook</a></header>
<main>
<nav class="fil"><a href="/">Accueil</a> › <span>{e(lib)}</span></nav>
<section class="intro">
<h1>Aubaines {e(lib)} au Québec</h1>
<p>Les rabais Amazon « {e(lib)} » repérés aujourd'hui, mis à jour chaque matin.</p>
</section>
{chips_html(slug)}
{contenu}
{formulaire_infolettre("aubaines")}
</main>
<footer>Mis à jour le {e(maj_lisible)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a></footer>
</body></html>"""


def page_index(aubaines, maj_iso, maj_lisible) -> str:
    cartes = cartes_html(aubaines)
    desc = ("Les meilleures aubaines Amazon du jour au Québec, mises à jour chaque matin. "
            "Rabais vérifiés, une page par aubaine. Par Chasseurs de Deals Québec.")
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aubaines du jour au Québec — Chasseurs de Deals Québec</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(DOMAINE)}/">
<meta property="og:title" content="Aubaines du jour au Québec">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(DOMAINE)}/">
<meta name="robots" content="index,follow,max-image-preview:large">
<style>{CSS}</style>
{GOOGLE_VERIF}
{ONESIGNAL}
</head>
<body>
<header><a class="logo" href="/">🔥 Chasseurs de Deals Québec</a>
<a class="fb" href="{e(PAGE_FACEBOOK)}" rel="noopener">Suivre la page Facebook</a></header>
<main>
<section class="intro">
<h1>Les aubaines du jour au Québec</h1>
<p>Les {len(aubaines)} meilleurs rabais Amazon repérés aujourd'hui, mis à jour chaque matin.
Clique une aubaine pour la voir — et suis notre
<a href="{e(PAGE_FACEBOOK)}" rel="noopener">page Facebook</a> pour ne rien manquer.</p>
</section>
{chips_html()}
<div class="recherche"><input type="search" id="q" placeholder="🔎 Rechercher un produit… (nom, marque, catégorie)"
 autocomplete="off"><span class="r-nb" id="qn"></span></div>
<section class="grille" id="grille">{cartes}</section>
<p class="r-vide" id="qv" hidden>Aucune aubaine ne correspond. Essaie un mot plus court —
« casque » plutôt que « casque bluetooth sony ».</p>
<script>
(function(){{
  var q=document.getElementById('q'),g=document.getElementById('grille'),
      n=document.getElementById('qn'),v=document.getElementById('qv');
  function plat(s){{return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');}}
  var cartes=[].slice.call(g.children).map(function(c){{
    return {{el:c,txt:plat(c.textContent||'')}};}});
  function filtre(){{
    var t=plat(q.value.trim()),vis=0;
    cartes.forEach(function(c){{
      var ok=!t||t.split(/\s+/).every(function(m){{return c.txt.indexOf(m)>=0;}});
      c.el.style.display=ok?'':'none';if(ok)vis++;}});
    n.textContent=t?vis+' résultat'+(vis>1?'s':''):'';
    v.hidden=!t||vis>0;}}
  q.addEventListener('input',filtre);
}})();
</script>
{formulaire_infolettre("aubaines")}
</main>
<footer>Mis à jour le {e(maj_lisible)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a></footer>
</body></html>"""


def sitemap(aubaines, maj_iso) -> str:
    urls = [f"<url><loc>{DOMAINE}/</loc><lastmod>{maj_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for _nom, slug in CATS_PAGES:
        urls.append(f"<url><loc>{DOMAINE}/categorie/{slug}.html</loc>"
                    f"<lastmod>{maj_iso}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>")
    for a in aubaines:
        urls.append(f"<url><loc>{DOMAINE}/aubaine/{a['slug']}.html</loc>"
                    f"<lastmod>{maj_iso}</lastmod><changefreq>daily</changefreq></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


def infolettre_html(aubaines, maj_lisible) -> str:
    """Courriel quotidien (HTML simple compatible courriel, styles en ligne).

    Le lien {{ unsubscribe }} est remplacé automatiquement par Brevo.
    """
    lignes = []
    for a in aubaines[:12]:
        lignes.append(
            '<tr><td style="padding:10px 0;border-bottom:1px solid #e8ecf0;">'
            f'<a href="{e(DOMAINE)}/aubaine/{e(a["slug"])}.html" '
            'style="color:#12232e;text-decoration:none;font-family:Arial,sans-serif;">'
            f'<strong style="color:#e4572e;">−{round(a["rabais"])} %</strong> '
            f'{e(a["titre"][:80])} — <strong>{e(prix_txt(a))}</strong></a></td></tr>')
    return f"""<!doctype html>
<html lang="fr-CA"><head><meta charset="utf-8"><title>Aubaines du jour</title></head>
<body style="margin:0;background:#f6f7f9;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:22px 10px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;">
<tr><td style="background:#12232e;padding:18px 24px;">
<span style="color:#ffffff;font-size:20px;font-weight:bold;">🔥 Chasseurs de Deals Québec</span><br>
<span style="color:#cfe0e6;font-size:13px;">Les aubaines du jour — {e(maj_lisible)}</span></td></tr>
<tr><td style="padding:20px 24px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{''.join(lignes)}</table>
<p style="text-align:center;margin:22px 0 8px;">
<a href="{e(DOMAINE)}/" style="background:#e4572e;color:#ffffff;text-decoration:none;
font-weight:bold;padding:12px 22px;border-radius:24px;display:inline-block;">
Voir les {len(aubaines)} aubaines du jour →</a></p>
<p style="color:#8496a8;font-size:11px;text-align:center;margin-top:18px;">
En tant que Partenaire Amazon, nous sommes rémunérés pour les achats admissibles.
Les prix peuvent avoir changé.<br>
<a href="{{{{ unsubscribe }}}}" style="color:#8496a8;">Se désabonner</a> ·
<a href="{e(PAGE_FACEBOOK)}" style="color:#8496a8;">Facebook</a></p>
</td></tr></table></td></tr></table></body></html>"""


ROBOTS = f"""# Ouvert aux moteurs de recherche et aux robots des IA.
User-agent: *
Allow: /

# Robots des IA explicitement autorisés (indexation et citation)
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Claude-Web
Allow: /
User-agent: anthropic-ai
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: Bingbot
Allow: /
User-agent: CCBot
Allow: /

Sitemap: {DOMAINE}/sitemap.xml
"""


def llms_txt(aubaines, maj_lisible) -> str:
    lignes = [
        "# Chasseurs de Deals Québec — Aubaines du jour",
        "",
        "> Aubaines Amazon.ca sélectionnées chaque matin pour le public québécois "
        "(rabais vérifiés). Publié par Chasseurs de Deals Québec.",
        "",
        f"Mise à jour : {maj_lisible}",
        f"Page Facebook : {PAGE_FACEBOOK}",
        f"Site principal : {SITE_PRINCIPAL}",
        "",
        "## Aubaines du jour",
        "",
    ]
    for a in aubaines[:NB_AUBAINES]:
        lignes.append(f"- [{a['titre']}]({DOMAINE}/aubaine/{a['slug']}.html) — "
                      f"{prix_txt(a)}, {round(a['rabais'])} % de rabais ({a['categorie']})")
    return "\n".join(lignes) + "\n"


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
background:#f6f7f9;color:#1a2230;line-height:1.5}
a{color:#e4572e;text-decoration:none}
header{display:flex;justify-content:space-between;align-items:center;gap:12px;
padding:14px 20px;background:#12232e;position:sticky;top:0;z-index:5;flex-wrap:wrap}
header .logo{color:#fff;font-weight:800;font-size:17px}
header .fb{background:#1877f2;color:#fff;padding:8px 14px;border-radius:8px;font-weight:600;font-size:14px}
main{max-width:1100px;margin:0 auto;padding:20px}
.intro{padding:24px 4px 10px}
.intro h1{font-size:26px;margin-bottom:8px}
.grille{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-top:14px}
.carte{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(20,40,70,.07);
display:flex;flex-direction:column;padding:12px;position:relative;transition:transform .1s}
.carte:hover{transform:translateY(-3px)}
.carte img{width:100%;height:150px;object-fit:contain}
.recherche{display:flex;align-items:center;gap:10px;margin:14px 0 6px}
.recherche input{flex:1;max-width:520px;padding:11px 14px;font-size:15px;border:2px solid #d90429;border-radius:10px;outline:none}
.recherche input:focus{box-shadow:0 0 0 3px rgba(217,4,41,.15)}
.r-nb{color:#666;font-size:13px;white-space:nowrap}
.r-vide{color:#666;padding:24px 0;text-align:center}
.carte .rabais{position:absolute;top:10px;left:10px;background:#e4572e;color:#fff;
font-weight:700;font-size:12px;padding:3px 8px;border-radius:20px}
.carte .cat{color:#8496a8;font-size:11px;text-transform:uppercase;margin-top:8px;letter-spacing:.4px}
.carte .t{font-size:13.5px;color:#1a2230;margin:3px 0 6px;flex:1}
.carte .p{font-weight:700;color:#128a5b}
.fiche{display:flex;gap:26px;background:#fff;border-radius:14px;padding:24px;
box-shadow:0 2px 14px rgba(20,40,70,.08);flex-wrap:wrap}
.fiche img{width:320px;max-width:100%;height:auto;object-fit:contain}
.fiche .info{flex:1;min-width:260px}
.fiche h1{font-size:22px;margin:6px 0 12px}
.fiche .cat{color:#8496a8;font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.fiche .prix{font-size:22px;font-weight:800;color:#128a5b;margin-bottom:16px}
.fiche .rabais{background:#e4572e;color:#fff;font-size:14px;padding:3px 10px;border-radius:20px;margin-left:8px}
.cta{display:inline-block;background:#e4572e;color:#fff;font-weight:700;padding:13px 22px;
border-radius:10px;font-size:16px}
.avis{color:#8496a8;font-size:12px;margin:14px 0}
.fb2{display:inline-block;background:#1877f2;color:#fff;padding:10px 16px;border-radius:8px;font-weight:600;font-size:14px}
.fil{color:#8496a8;font-size:13px;margin-bottom:14px}
.fil a{color:#8496a8}
footer{text-align:center;color:#8496a8;font-size:13px;padding:26px}
footer a{color:#8496a8}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 6px}
.chip{background:#fff;color:#1a2230;border:1px solid #d7dee6;padding:7px 14px;
border-radius:20px;font-size:13px;font-weight:600}
.chip:hover{border-color:#e4572e;color:#e4572e}
.chip.actif{background:#e4572e;color:#fff;border-color:#e4572e}
.vide{background:#fff;border-radius:12px;padding:26px;text-align:center;color:#5a6b7d}
.infolettre{background:#12232e;border-radius:14px;padding:24px;margin:28px 0;color:#fff;text-align:center}
.infolettre h2{font-size:20px;margin-bottom:6px}
.infolettre p{color:#cfe0e6;font-size:14px;margin-bottom:14px}
.inf-form{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
.inf-form input{padding:12px 16px;border-radius:24px;border:none;font-size:15px;min-width:240px}
.inf-form button{background:#e4572e;color:#fff;border:none;font-weight:700;font-size:15px;
padding:12px 22px;border-radius:24px;cursor:pointer}
.inf-ok{color:#7fd8a8;font-weight:600}
.infolettre.compacte{padding:16px;margin:18px 0}
@media(max-width:520px){.fiche{flex-direction:column}.fiche img{width:100%}}
"""


# ---------------------------------------------------------------------------
# Notification push quotidienne (« Aubaine du jour »)
# ---------------------------------------------------------------------------

ONESIGNAL_REST_URL = "https://api.onesignal.com/notifications"


def envoyer_push(aubaines) -> None:
    """Envoie une notification push OneSignal pour la meilleure aubaine du jour.

    La clé API REST est lue dans la variable d'environnement
    ONESIGNAL_REST_API_KEY (secret GitHub). Sans clé (ex. exécution locale),
    l'envoi est simplement ignoré — la génération du site n'est jamais bloquée.
    """
    cle = os.environ.get("ONESIGNAL_REST_API_KEY", "").strip()
    if not cle:
        print("Push OneSignal ignoré (variable ONESIGNAL_REST_API_KEY absente).")
        return
    if not aubaines:
        return
    a = aubaines[0]  # la meilleure aubaine (plus haut rabais) = « aubaine du jour »
    message = f"🔥 {a['titre'][:70]} — {round(a['rabais'])} % de rabais"
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Subscribed Users"],
        "headings": {"en": "Chasseurs de Deals — Aubaine du jour"},
        "contents": {"en": message},
        "url": DOMAINE + "/",
        "chrome_web_icon": a.get("image", ""),
    }
    scheme = "Key" if cle.startswith("os_") else "Basic"
    headers = {"Authorization": f"{scheme} {cle}",
               "Content-Type": "application/json; charset=utf-8"}
    try:
        r = requests.post(ONESIGNAL_REST_URL, json=payload, headers=headers, timeout=30)
        print(f"Push OneSignal → HTTP {r.status_code} : {r.text[:300]}")
    except requests.RequestException as e:
        print(f"Push OneSignal échoué (sans bloquer la génération) : {e}")


def main() -> int:
    aubaines = lire_aubaines()
    if not aubaines:
        raise SystemExit("ERREUR : aucune aubaine lue — rien n'est généré (le site précédent reste en place).")

    maintenant = datetime.now(FUSEAU)
    maj_iso = maintenant.strftime("%Y-%m-%d")
    maj_lisible = maintenant.strftime("%d %B %Y à %H h%M")

    SORTIE.mkdir(exist_ok=True)
    (SORTIE / "aubaine").mkdir(exist_ok=True)
    (SORTIE / "categorie").mkdir(exist_ok=True)

    # Pages catégories permanentes (contenu du jour).
    for nom, slug in CATS_PAGES:
        items = [a for a in aubaines if a["categorie"] == nom]
        (SORTIE / "categorie" / f"{slug}.html").write_text(
            page_categorie(nom, slug, items, maj_lisible), encoding="utf-8")

    # Gabarit du courriel quotidien (lu par Brevo via Make chaque matin).
    (SORTIE / "infolettre.html").write_text(
        infolettre_html(aubaines, maj_lisible), encoding="utf-8")

    (SORTIE / "index.html").write_text(page_index(aubaines, maj_iso, maj_lisible), encoding="utf-8")
    (SORTIE / "sitemap.xml").write_text(sitemap(aubaines, maj_iso), encoding="utf-8")
    (SORTIE / "robots.txt").write_text(ROBOTS, encoding="utf-8")
    (SORTIE / "llms.txt").write_text(llms_txt(aubaines, maj_lisible), encoding="utf-8")
    # Un domaine personnalisé sur GitHub Pages a besoin d'un fichier CNAME.
    (SORTIE / "CNAME").write_text("aubaines.chasseursdedealsqc.com\n", encoding="utf-8")
    # Service worker OneSignal (doit être à la racine du site pour le push web).
    (SORTIE / "OneSignalSDKWorker.js").write_text(
        'importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");\n',
        encoding="utf-8")

    for a in aubaines:
        (SORTIE / "aubaine" / f"{a['slug']}.html").write_text(
            page_aubaine(a, maj_lisible), encoding="utf-8")

    print(f"OK : {len(aubaines)} aubaines → {SORTIE}")
    print(f"  index.html, sitemap.xml ({len(aubaines)+1} URL), robots.txt, llms.txt, "
          f"{len(aubaines)} pages d'aubaines.")

    envoyer_push(aubaines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
