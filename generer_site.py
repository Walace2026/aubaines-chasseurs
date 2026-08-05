#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generer_site.py — Génère le sous-site « aubaines.chasseursdedealsqc.com »
=========================================================================

Lit les aubaines depuis la feuille Google publiée (Site_Aubaines) et produit
un site statique optimisé pour Google, Bing ET les robots des IA :

  - index.html                 la page d'accueil (les 50 meilleures aubaines)
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

# Notifications push OneSignal (app « Chasseurs de Deals - Aubaines »).
ONESIGNAL_APP_ID = "a5d68a4c-b078-4294-921f-53a46cbf1e7a"
ONESIGNAL = (
    '<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>'
    '<script>window.OneSignalDeferred=window.OneSignalDeferred||[];'
    'OneSignalDeferred.push(async function(OneSignal){await OneSignal.init({appId:"'
    + ONESIGNAL_APP_ID + '"});});</script>'
)

NB_AUBAINES = 100         # nombre de pages à générer (les meilleurs rabais)
FUSEAU = timezone(timedelta(hours=-4))  # heure de l'Est

# Balise de vérification Google Search Console (jeton propre au compte Google —
# la même balise valide toutes les propriétés du compte).
GOOGLE_VERIF = ('<meta name="google-site-verification" '
                'content="737lfq2zJvydj4UTXGY0UncdQNHKiuT1RN5XDP0UYAw">')

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
    return retenues[:NB_AUBAINES]


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
</main>
<footer>Mis à jour le {e(maj_iso)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a></footer>
</body></html>"""


def q(s) -> str:
    """Chaîne JSON sûre pour le JSON-LD."""
    import json
    return json.dumps(str(s), ensure_ascii=False)


def page_index(aubaines, maj_iso, maj_lisible) -> str:
    cartes = "\n".join(f"""<a class="carte" href="/aubaine/{e(a['slug'])}.html">
<img src="{e(a['image'])}" alt="{e(a['titre'])}" loading="lazy" onerror="this.style.opacity=0">
<span class="rabais">−{round(a['rabais'])} %</span>
<span class="cat">{e(a['categorie'])}</span>
<span class="t">{e(a['titre'][:70])}</span>
<span class="p">{e(prix_txt(a))}</span></a>""" for a in aubaines)
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
<section class="grille">{cartes}</section>
</main>
<footer>Mis à jour le {e(maj_lisible)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a></footer>
</body></html>"""


def sitemap(aubaines, maj_iso) -> str:
    urls = [f"<url><loc>{DOMAINE}/</loc><lastmod>{maj_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for a in aubaines:
        urls.append(f"<url><loc>{DOMAINE}/aubaine/{a['slug']}.html</loc>"
                    f"<lastmod>{maj_iso}</lastmod><changefreq>daily</changefreq></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


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
