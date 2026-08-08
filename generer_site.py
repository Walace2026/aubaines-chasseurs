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
import json
import html
import io
import os
import re
import sys
import time
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

# Cache des titres traduits en francais (onglet « Traductions », colonnes
# ASIN | titre FR). Alimente chaque matin a 5 h 12 par le scenario Make
# « TRADUCTION - cache titres FR », soit avant la generation de 5 h 20.
# Traduction des titres en francais avec Claude (API Anthropic).
# Le cache est un fichier du depot : chaque ASIN n est traduit qu une seule
# fois dans sa vie, et GitHub Actions reverse le fichier a chaque execution.
# Sans cle ANTHROPIC_API_KEY, on garde simplement les titres d origine.
TRAD_FICHIER = Path(__file__).resolve().parent / "traductions.json"
ANTHROPIC_MODELE = "claude-haiku-4-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
LOT_TRADUCTION = 25      # titres par appel
MAX_TRADUCTIONS = 400    # garde-fou de cout par execution

TRAD_URLS = [
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Traductions",
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet=Traductions",
]

# Offres eclair Amazon, via le point d acces /lightningdeal de Keepa.
# Keepa les rafraichit toutes les 10 minutes ; le site est regenere trois fois
# par jour, ce qui suffit pour en attraper la majorite avant leur expiration.
# La cle vit dans les secrets GitHub : ce depot est public.
KEEPA_ECLAIR_URL = "https://api.keepa.com/lightningdeal"
KEEPA_DOMAINE = 6                 # 6 = Amazon.ca
TAG_AFFILIE = "dtlinformat0f-20"
ECLAIR_RABAIS_MIN = 10            # sous ce seuil, ce n est pas une aubaine
ECLAIR_MAX = 24                   # on garde la section courte et lisible

# Prix rouges : produits vendus sous le prix conseille du fabricant.
# C est le pourcentage qu Amazon affiche en rouge sur ses fiches. Pris seul,
# ce chiffre ne veut pas dire grand-chose : beaucoup d articles ne se vendent
# jamais au prix conseille. On exige donc AUSSI que le prix courant soit egal
# ou inferieur a sa moyenne des 90 derniers jours. Un produit qui passe les
# deux conditions est reellement bon marche aujourd hui, pas seulement en
# apparence.
KEEPA_QUERY_URL = "https://api.keepa.com/query"
KEEPA_PRODUIT_URL = "https://api.keepa.com/product"
ROUGE_RABAIS_MIN = 15             # % minimum sous le prix conseille
ROUGE_CANDIDATS = 150             # ASIN examines par cycle (1 jeton Keepa chacun)
                                  # 100 = un seul appel /product. Au-dela, Keepa
                                  # renvoyait des erreurs de quota de jetons.
ROUGE_MAX = 36                    # affiches sur la page
ROUGE_LOT = 100                   # ASIN par appel /product

# Amazon Warehouse : retours clients revendus a rabais par Amazon lui-meme.
# Ce sont de VRAIES baisses de prix, pas des prix conseilles gonfles — mais ce
# sont des articles d occasion, d ou leur section a part et l etat affiche sur
# chaque carte. On exclut l etat « acceptable », visiblement use, qui genere
# l essentiel des deceptions.
KEEPA_DEAL_URL = "https://api.keepa.com/deal"
WH_ETATS = {2: "Comme neuf", 3: "Très bon état", 4: "Bon état",
            5: "État acceptable", 0: "État non précisé"}
WH_ETATS_VOULUS = [2, 3, 4]
WH_RABAIS_MIN = 15
WH_MAX = 48                       # sur la page de categorie
WH_ACCUEIL = 4                    # sur la page d accueil
KC_WAREHOUSE = 9

# Indices des series de prix Keepa (voir la documentation « csv »).
KC_AMAZON, KC_NEUF, KC_RANG, KC_PRIX_CONSEILLE = 0, 1, 3, 4
KC_NOTE, KC_AVIS, KC_BOITE_ACHAT = 16, 17, 18

# Les memes categories racines que la requete Make quotidienne.
CATEGORIES_KEEPA = [
    667823011, 6205514011, 6948389011, 6205124011, 6967215011, 6205517011,
    3198031, 2206275011, 21204935011, 2235620011, 3006902011, 6205511011,
    6205177011, 2242989011, 6205499011, 3561346011,
]
EPOQUE_KEEPA = 21564000           # minutes Keepa -> minutes Unix

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

# strftime("%B") renvoie le mois en anglais : GitHub Actions tourne en locale C,
# et installer une locale francaise sur le runner serait fragile. Table en dur.
MOIS_FR = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre")

# Balise de vérification Google Search Console (jeton propre au compte Google —
# la même balise valide toutes les propriétés du compte).
GOOGLE_VERIF = ('<meta name="google-site-verification" '
                'content="737lfq2zJvydj4UTXGY0UncdQNHKiuT1RN5XDP0UYAw">')
# Balise de vérification Pinterest — permet de revendiquer le domaine sur Pinterest
GOOGLE_VERIF += '<meta name="p:domain_verify" content="643106277e09e6d158eaa73f88c1bf3c">'

SORTIE = Path(__file__).resolve().parent / "public"

# Contenu editorial des pages categorie (voir intros_categories.py).
try:
    from intros_categories import INTROS
except ImportError:            # le site se genere quand meme sans les intros
    INTROS = {}

# rootCat Amazon.ca → nom de catégorie lisible (best-effort ; « Aubaines » sinon).
# Table corrigee le 7 aout 2026 a partir des 537 aubaines reelles de la feuille :
# chaque identifiant a ete verifie contre les produits qui le portent. Quatre
# associations etaient inversees et cinq manquaient — d ou du the et des noix
# classes sous « Auto », des jouets sous « Mode », et une page Auto vide pendant
# que les vraies pieces d auto tombaient dans « Autres aubaines ».
CATEGORIES = {
    "21204935011": "Mode",                 # Vetements, chaussures et bijoux
    "2235620011":  "Mode",                 # Montres
    "3006902011":  "Outils et bricolage",  # Outils et renovation
    "2206275011":  "Maison et cuisine",    # Maison et cuisine
    "2242989011":  "Sports et plein air",  # Sports et plein air
    "667823011":   "Électronique",         # Électronique
    "6205517011":  "Jouets et jeux",       # Jouets et jeux
    "6948389011":  "Auto",                 # Auto et moto
    # --- categories propres, ouvertes le 8 aout 2026 -----------------------
    "3198031":     "Jeux vidéo",           # Jeux video et consoles
    "6967215011":  "Épicerie",             # Epicerie et gourmet
    "6205124011":  "Beauté",               # Beaute et soins
    "6205177011":  "Santé et soins",       # Sante et soins personnels
    "6205514011":  "Animalerie",           # Articles pour animaux
    "3561346011":  "Bébé",                 # Bebe et puericulture
    "6205511011":  "Produits de bureau",   # Fournitures de bureau et scolaires
    "6205499011":  "Terrasse et jardin",   # Terrasse, pelouse et jardin
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
    ("Jeux vidéo", "jeux-video"),
    ("Épicerie", "epicerie"),
    ("Beauté", "beaute"),
    ("Santé et soins", "sante-soins"),
    ("Animalerie", "animalerie"),
    ("Bébé", "bebe"),
    ("Produits de bureau", "produits-bureau"),
    ("Terrasse et jardin", "terrasse-jardin"),
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


# Suffixes de taille propres aux vetements et aux chaussures, que le motif
# general ci-dessus ne couvre pas : « 32W x 34L », « 9.5 N US », « 48G US ».
_SUFFIXE_TAILLE = re.compile(
    r"\b("
    r"\d+(?:[.,]\d+)?\s?w\s?x\s?\d+(?:[.,]\d+)?\s?l"      # 32W x 34L
    r"|w\d+\s?x\s?l\d+"                                    # W36 x L80
    r"|\d+(?:[.,]\d+)?\s?[a-z]{0,2}\s?(?:us|ca|eu|uk)\b"     # 9.5 N US, 48G US
    r"|\d+(?:[.,]\d+)?\s?(?:w|l|d|dd|ddd)\b"                 # 46W, 34L, 54DD
    r")",
    re.IGNORECASE,
)


def cle_variante(titre: str) -> str:
    """Cle de regroupement : deux variantes du meme produit la partagent.

    Amazon construit ses titres ainsi : le nom du produit, puis les attributs
    de variante apres une virgule (« ...Ankle Boot, Black Tumbled, 9.5 N US »).
    On coupe donc a la premiere virgule quand ce qui precede suffit a
    identifier le produit : cela regle d un coup les couleurs ET les tailles.
    Le seuil de 25 caracteres evite de tronquer « Club House, Quality Herbs... »
    a une marque seule et de fusionner des produits sans rapport.
    """
    brut = (titre or "").strip()
    t = unicodedata.normalize("NFKD", brut).encode("ascii", "ignore").decode()
    tete = t.split(",")[0].strip()
    if len(tete) >= 25:
        t = tete
    t = _SUFFIXE_TAILLE.sub(" ", t)
    t = _MOTS_TAILLE.sub(" ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
    t = re.sub(r"\s+", " ", t)
    # Si le nettoyage reduit trop le titre, on retombe sur le titre complet
    # pour ne pas fusionner par erreur deux produits differents.
    return t if len(t) >= 12 else brut.lower()


def choisir_moins_cher(items: list) -> dict:
    avec_prix = [x for x in items if x.get("prix") is not None]
    if avec_prix:
        return min(avec_prix, key=lambda x: x["prix"])
    return max(items, key=lambda x: x["rabais"])


def heure_keepa(minutes: int) -> int:
    """Minutes Keepa -> secondes Unix."""
    return (int(minutes) + EPOQUE_KEEPA) * 60


def lire_offres_eclair(exclure: set) -> list:
    """Offres eclair Amazon.ca en cours, via Keepa.

    Ces offres-la n apparaissent pas dans le flux habituel : Keepa compare au
    prix recent, et une offre eclair porte souvent sur un article dont le prix
    courant n a pas bouge depuis des semaines. C est pourtant le genre de
    rabais que les gens cherchent, avec l urgence en prime.

    Sans cle KEEPA_API_KEY, la fonction renvoie une liste vide : le site se
    genere exactement comme avant.
    """
    cle = os.environ.get("KEEPA_API_KEY", "").strip()
    if not cle:
        print("  offres eclair : KEEPA_API_KEY absente, section ignoree")
        return []
    try:
        r = requests.get(KEEPA_ECLAIR_URL, timeout=45,
                         params={"key": cle, "domain": KEEPA_DOMAINE})
        r.raise_for_status()
        brut = r.json().get("lightningDeals") or []
    except (requests.RequestException, ValueError) as e:
        print(f"  offres eclair : lecture impossible ({type(e).__name__}), section ignoree")
        return []

    maintenant = int(time.time())
    offres = []
    for d in brut:
        asin = (d.get("asin") or "").strip()
        prix = d.get("dealPrice") or 0
        rabais = d.get("percentOff") or 0
        fin = heure_keepa(d.get("endTime") or 0)
        if not re.fullmatch(r"[A-Z0-9]{10}", asin) or asin in exclure:
            continue
        if d.get("dealState") != "AVAILABLE" or prix <= 0:
            continue
        if rabais < ECLAIR_RABAIS_MIN or fin <= maintenant + 600:
            continue          # moins de 10 min restantes : inutile de l afficher
        offres.append({
            "asin": asin,
            "titre": (d.get("title") or "Aubaine").strip(),
            "rabais": float(rabais),
            "prix": prix / 100.0,
            "lien": f"https://www.amazon.ca/dp/{asin}?tag={TAG_AFFILIE}",
            "categorie": "Offre eclair",
            "fin": fin,
            "image": f"https://images-na.ssl-images-amazon.com/images/P/{asin}.01._SCLZZZZZZZ_.jpg",
        })

    offres.sort(key=lambda x: x["rabais"], reverse=True)
    offres = garder_avec_photo(offres)[:ECLAIR_MAX]
    offres = appliquer_traductions(offres)
    print(f"  offres eclair : {len(offres)} retenues sur {len(brut)} annoncees par Keepa")
    return offres


def _indice_prix(serie):
    """Indice du premier prix exploitable : boite d achat, Amazon, puis neuf.

    On renvoie l INDICE et non la valeur, pour pouvoir lire la moyenne 90 jours
    au meme indice. Comparer un prix de boite d achat a une moyenne « Amazon »
    n aurait aucun sens et laisserait passer de faux bas prix.
    """
    for i in (KC_BOITE_ACHAT, KC_AMAZON, KC_NEUF):
        try:
            v = serie[i]
        except (IndexError, TypeError):
            continue
        if isinstance(v, int) and v > 0:
            return i
    return None


def lire_prix_rouges(exclure: set) -> list:
    """Produits vendus sous leur prix conseille, et au plus bas depuis 90 jours.

    Deux appels Keepa. Le premier, /query, laisse le serveur faire le gros du
    tri : bonne categorie, bien classe, bien note, et surtout prix inferieur ou
    egal a la moyenne des 90 derniers jours. Le second, /product, ramene les
    prix reels pour calculer l ecart avec le prix conseille — c est le chiffre
    qu Amazon affiche en rouge.

    L ordre compte : le garde-fou des 90 jours est applique cote serveur, donc
    on ne depense un jeton /product que sur des candidats deja credibles.
    """
    # DESACTIVE PAR DEFAUT, et volontairement.
    #
    # Cette recherche coute une centaine de jetons Keepa par execution — un
    # appel /query puis un /product par ASIN — et n a jamais rien produit :
    # sur Amazon.ca le prix conseille egale presque toujours le prix de vente,
    # donc il n y a pas d ecart a calculer. Les badges rouges que l on voyait
    # sur les fiches etaient des prix Amazon Business, invisibles au public.
    #
    # Pire, ces jetons manquaient ensuite a Warehouse et aux offres eclair, qui
    # ramenent de vrais produits. Le code reste en place : si Amazon se remet a
    # publier des prix conseilles credibles, il suffit de poser la variable
    # PRIX_ROUGES=1 dans le workflow pour le rallumer.
    if os.environ.get("PRIX_ROUGES", "").strip() != "1":
        return [], None

    cle = os.environ.get("KEEPA_API_KEY", "").strip()
    if not cle:
        return [], None

    selection = {
        "categories_include": CATEGORIES_KEEPA,
        "current_LISTPRICE_gte": 500,       # au moins 5 $ de prix conseille
        "current_SALES_lte": 200000,
        "current_RATING_gte": 30,
        "current_COUNT_REVIEWS_gte": 5,
        # Le garde-fou des 90 jours n est PLUS demande ici. Il portait sur la
        # serie « Amazon », absente des articles vendus par un tiers, et vidait
        # le bassin de tout ce qui a justement un prix conseille. Il est
        # applique plus bas, sur la meme serie que le prix retenu.
        "singleVariation": True,
        "sort": [["current_SALES", "asc"]],
        "perPage": ROUGE_CANDIDATS,
        "page": 0,
    }
    try:
        r = requests.get(KEEPA_QUERY_URL, timeout=60,
                         params={"key": cle, "domain": KEEPA_DOMAINE,
                                 "selection": json.dumps(selection)})
        r.raise_for_status()
        asins = [a for a in (r.json().get("asinList") or [])
                 if re.fullmatch(r"[A-Z0-9]{10}", a or "") and a not in exclure]
    except (requests.RequestException, ValueError) as e:
        print(f"  prix rouges : recherche impossible ({type(e).__name__}), section ignoree")
        return [], None

    asins = asins[:ROUGE_CANDIDATS]
    produits = []
    for i in range(0, len(asins), ROUGE_LOT):
        lot = asins[i:i + ROUGE_LOT]
        try:
            r = requests.get(KEEPA_PRODUIT_URL, timeout=90,
                             params={"key": cle, "domain": KEEPA_DOMAINE,
                                     "asin": ",".join(lot), "stats": 90})
            r.raise_for_status()
            reponse = r.json()
            produits.extend(reponse.get("products") or [])
            jetons = reponse.get("tokensLeft")
            if jetons is not None:
                print(f"  prix rouges : {jetons} jetons Keepa restants")
        except requests.HTTPError as e:
            # 429 = jetons epuises. Keepa indique le delai de recharge.
            code = getattr(e.response, "status_code", "?")
            print(f"  prix rouges : lot refuse par Keepa (HTTP {code}) — "
                  f"probable manque de jetons, on garde ce qu on a")
            break
        except (requests.RequestException, ValueError) as e:
            print(f"  prix rouges : lot ignore ({type(e).__name__})")

    # On evalue chaque candidat une fois, puis on choisit le palier le plus
    # exigeant qui donne encore assez de produits. Mieux vaut une section
    # honnete et courte qu une section vide — mais le texte affiche doit
    # toujours dire la verite sur ce qui a ete verifie.
    evalues, ecarte = [], {"prix": 0, "conseille": 0, "rabais": 0}
    for p in produits:
        stats = p.get("stats") or {}
        courant = stats.get("current") or []
        moyennes = stats.get("avg90") or []
        i = _indice_prix(courant)
        if i is None:
            ecarte["prix"] += 1
            continue
        prix = courant[i]
        conseille = courant[KC_PRIX_CONSEILLE] if len(courant) > KC_PRIX_CONSEILLE else -1
        if conseille <= 0 or conseille <= prix:
            ecarte["conseille"] += 1
            continue
        rabais = round(100 * (conseille - prix) / conseille)
        if rabais < ROUGE_RABAIS_MIN:
            ecarte["rabais"] += 1
            continue
        # Meme indice des deux cotes : on compare bien le prix a SA moyenne.
        moyenne = moyennes[i] if len(moyennes) > i else -1
        asin = p.get("asin") or ""
        evalues.append({
            "asin": asin,
            "titre": (p.get("title") or "Aubaine").strip(),
            "rabais": float(rabais),
            "prix": prix / 100.0,
            "conseille": conseille / 100.0,
            "moyenne": moyenne / 100.0 if moyenne > 0 else None,
            "lien": f"https://www.amazon.ca/dp/{asin}?tag={TAG_AFFILIE}",
            "categorie": CATEGORIES.get(str(p.get("rootCategory") or ""), "Aubaines"),
            "image": f"https://images-na.ssl-images-amazon.com/images/P/{asin}.01._SCLZZZZZZZ_.jpg",
        })

    paliers = [
        ("au plus bas depuis 90 jours",
         lambda x: x["moyenne"] is None or x["prix"] <= x["moyenne"]),
        ("a 5 % pres de son plus bas de 90 jours",
         lambda x: x["moyenne"] is None or x["prix"] <= x["moyenne"] * 1.05),
        (None, lambda x: True),          # dernier recours : le rabais seul
    ]
    rouges, mention = [], None
    for libelle, test in paliers:
        retenus = [x for x in evalues if test(x)]
        if len(retenus) >= 6 or libelle is None:
            rouges, mention = retenus, libelle
            break

    print(f"  prix rouges : {len(produits)} candidats — "
          f"{ecarte['prix']} sans prix, {ecarte['conseille']} sans prix conseille, "
          f"{ecarte['rabais']} sous {ROUGE_RABAIS_MIN} %, "
          f"{len(evalues)} au-dessus du seuil, {len(rouges)} retenus "
          f"(palier : {mention or 'rabais seul, garde-fou leve'})")

    rouges.sort(key=lambda x: x["rabais"], reverse=True)
    rouges = garder_avec_photo(rouges)[:ROUGE_MAX]
    rouges = appliquer_traductions(rouges)
    print(f"  prix rouges : {len(rouges)} affiches")
    return rouges, mention


def lire_warehouse(exclure: set) -> list:
    """Aubaines Amazon Warehouse : retours clients revendus par Amazon.

    Le rabais est calcule par rapport au prix du NEUF plutot que par rapport a
    l historique du prix Warehouse : c est la comparaison qui interesse
    l acheteur — « 45 $ au lieu de 80 $ neuf » — et c est verifiable sur la
    fiche Amazon. L etat de l article est affiche sur chaque carte : vendre de
    l occasion sans le dire serait le meilleur moyen de perdre la confiance
    qu on essaie de construire.
    """
    cle = os.environ.get("KEEPA_API_KEY", "").strip()
    if not cle:
        return []
    selection = {
        "page": 0,
        "domainId": KEEPA_DOMAINE,
        "priceTypes": [KC_WAREHOUSE],
        "warehouseConditions": WH_ETATS_VOULUS,
        "deltaPercentRange": [WH_RABAIS_MIN, 100],
        "salesRankRange": [1, 200000],
        "minRating": 30,
        "hasReviews": True,
        "includeCategories": CATEGORIES_KEEPA,
        "sortType": 4,
        "isRangeEnabled": True,
        "isFilterEnabled": True,
    }
    try:
        r = requests.get(KEEPA_DEAL_URL, timeout=60,
                         params={"key": cle, "selection": json.dumps(selection)})
        r.raise_for_status()
        brut = ((r.json().get("deals") or {}).get("dr")) or []
    except (requests.RequestException, ValueError) as e:
        print(f"  warehouse : lecture impossible ({type(e).__name__}), section ignoree")
        return []

    lots = []
    for d in brut:
        asin = (d.get("asin") or "").strip()
        if not re.fullmatch(r"[A-Z0-9]{10}", asin) or asin in exclure:
            continue
        courant = d.get("current") or []
        prix = courant[KC_WAREHOUSE] if len(courant) > KC_WAREHOUSE else -1
        neuf = courant[KC_NEUF] if len(courant) > KC_NEUF else -1
        if prix <= 0:
            continue
        if neuf > prix:
            rabais = round(100 * (neuf - prix) / neuf)
        else:                      # pas de prix neuf connu : on garde le delta Keepa
            deltas = d.get("deltaPercent") or []
            try:
                rabais = int(deltas[1][KC_WAREHOUSE])
            except (IndexError, TypeError, ValueError):
                continue
        if rabais < WH_RABAIS_MIN:
            continue
        etat = WH_ETATS.get(int(d.get("warehouseCondition") or 0), WH_ETATS[0])
        lots.append({
            "asin": asin,
            "titre": (d.get("title") or "Aubaine").strip(),
            "rabais": float(rabais),
            "prix": prix / 100.0,
            "neuf": neuf / 100.0 if neuf > 0 else None,
            "etat": etat,
            "note": (d.get("warehouseConditionComment") or "").strip(),
            "lien": f"https://www.amazon.ca/dp/{asin}?tag={TAG_AFFILIE}",
            "categorie": CATEGORIES.get(str(d.get("rootCat") or ""), "Aubaines"),
            "img_keepa": "",
        })

    lots.sort(key=lambda x: x["rabais"], reverse=True)
    for a in lots:
        a["urls_image"] = urls_image(a)
        a["image"] = a["urls_image"][0]
    lots = garder_avec_photo(lots)[:WH_MAX]
    lots = appliquer_traductions(lots)
    print(f"  warehouse : {len(lots)} retenues sur {len(brut)} annoncees par Keepa")
    return lots


def charger_cache_trad() -> dict:
    """Cache ASIN -> titre francais, conserve dans le depot."""
    try:
        with open(TRAD_FICHIER, encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def traduire_lot(titres: dict, cle: str) -> dict:
    """Traduit un lot de titres avec Claude. Renvoie {asin: titre_fr}."""
    liste = "\n".join(f"{a} :: {t}" for a, t in titres.items())
    consigne = (
        "Tu traduis des titres de produits Amazon en francais quebecois, pour un "
        "site d aubaines. Regles : garde les noms de marque, les modeles, les "
        "chiffres et les unites tels quels ; traduis le reste en francais clair "
        "et naturel ; n invente aucune information absente du titre ; reste sous "
        "150 caracteres ; si le titre est deja en francais, recopie-le tel quel.\n\n"
        "Reponds UNIQUEMENT par un objet JSON {\"ASIN\": \"titre traduit\"}, "
        "sans texte autour et sans bloc de code."
    )
    corps = {
        "model": ANTHROPIC_MODELE,
        "max_tokens": 4000,
        "system": consigne,
        "messages": [{"role": "user", "content": liste}],
    }
    r = requests.post(
        ANTHROPIC_URL, json=corps, timeout=120,
        headers={"x-api-key": cle, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    r.raise_for_status()
    texte = "".join(b.get("text", "") for b in r.json().get("content", [])).strip()
    if texte.startswith("```"):
        texte = texte.split("```")[1]
        texte = texte.split("\n", 1)[1] if texte.lower().startswith("json") else texte
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut < 0 or fin < 0:
        raise ValueError("reponse sans objet JSON")
    obj = json.loads(texte[debut:fin + 1])
    return {a: str(t).strip() for a, t in obj.items()
            if a in titres and str(t).strip()}


def appliquer_traductions(aubaines: list) -> list:
    """Remplace les titres anglais par leur version francaise.

    Trois sources, dans l ordre : le cache du depot, l onglet « Traductions »
    de la feuille (historique), puis Claude pour ce qui manque encore. Tout
    echec est absorbe : un titre non traduit reste en anglais, le site sort
    quand meme. Publier des aubaines en anglais vaut mieux que ne rien publier.
    """
    cache = charger_cache_trad()
    depart = len(cache)
    for asin, fr in lire_traductions().items():
        cache.setdefault(asin, fr)

    cle = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    manquants = {a["asin"]: a["titre"] for a in aubaines if a["asin"] not in cache}
    if manquants and cle:
        a_faire = dict(list(manquants.items())[:MAX_TRADUCTIONS])
        if len(manquants) > MAX_TRADUCTIONS:
            print(f"  traduction : {len(manquants)} titres manquants, "
                  f"{MAX_TRADUCTIONS} traites cette fois (garde-fou de cout)")
        items = list(a_faire.items())
        for i in range(0, len(items), LOT_TRADUCTION):
            lot = dict(items[i:i + LOT_TRADUCTION])
            try:
                cache.update(traduire_lot(lot, cle))
            except Exception as e:                   # noqa: BLE001
                print(f"  traduction : lot ignore ({type(e).__name__}: {e})")
    elif manquants:
        print(f"  traduction : {len(manquants)} titres sans traduction "
              f"(ANTHROPIC_API_KEY absente)")

    for a in aubaines:
        fr = cache.get(a["asin"])
        if fr:
            a["titre"] = fr

    if len(cache) != depart:
        try:
            TRAD_FICHIER.write_text(
                json.dumps(cache, ensure_ascii=False, indent=0, sort_keys=True),
                encoding="utf-8")
        except OSError as e:
            print(f"  traduction : cache non enregistre ({e})")
    print(f"  traductions : {len(cache)} titres en cache, "
          f"{sum(1 for a in aubaines if a['asin'] in cache)}/{len(aubaines)} aubaines en francais")
    return aubaines


def lire_traductions() -> dict:
    """ASIN -> titre francais, depuis l onglet « Traductions ».

    Volontairement tolerant : si l onglet est absent, vide ou injoignable, le
    site se genere quand meme avec les titres d origine. Une traduction
    manquante ne doit jamais empecher la publication des aubaines du matin.
    """
    for url in TRAD_URLS:
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            r.encoding = "utf-8"
            if "<html" in r.text[:200].lower():
                continue
            trad = {}
            for ligne in csv.reader(io.StringIO(r.text)):
                if len(ligne) < 2:
                    continue
                asin, fr = (ligne[0] or "").strip(), (ligne[1] or "").strip()
                if re.fullmatch(r"[A-Z0-9]{10}", asin) and fr:
                    trad.setdefault(asin, fr)
            print(f"  traductions : {len(trad)} titres en francais")
            return trad
        except (requests.RequestException, ValueError, csv.Error):
            continue
    print("  traductions : onglet injoignable, titres d origine conserves")
    return {}


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
        img_keepa = ligne[9].strip() if len(ligne) > 9 else ""
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
            "img_keepa": img_keepa,
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

    # Traduire avant de fabriquer les slugs : les URL sont ainsi en francais.
    retenues = appliquer_traductions(retenues[:NB_AUBAINES])

    for a in retenues:
        a["slug"] = slugifier(a["titre"], a["asin"])
        a["urls_image"] = urls_image(a)
        a["image"] = a["urls_image"][0]

    # 4) LA PHOTO EST OBLIGATOIRE. Une annonce sans image ne s'affiche pas.
    #    Amazon ne renvoie pas d'erreur pour une image absente : il renvoie un
    #    GIF d'un seul pixel, à peine quelques dizaines d'octets. On mesure.
    retenues = garder_avec_photo(retenues)
    return retenues[:NB_AUBAINES]


_NOM_IMAGE = re.compile(r"^[A-Za-z0-9_+-]{6,80}\.(?:jpg|jpeg|png)$", re.IGNORECASE)


def nom_image_keepa(brut: str):
    """Nom de fichier de l image, tel que Keepa le renvoie.

    Keepa transporte ce nom sous forme de tableau d octets. Le scenario Make
    l ecrit donc dans la feuille en codes decimaux separes par des tirets
    (« 52-49-117-... »). On le rend ici a sa forme lisible, « 41uvDx3VrcL.jpg ».
    Une valeur deja lisible est acceptee telle quelle, et tout ce qui ne
    ressemble pas a un nom de fichier est ignore sans bruit.
    """
    brut = (brut or "").strip()
    if not brut:
        return None
    if re.fullmatch(r"\d{1,3}(?:-\d{1,3})+", brut):
        try:
            brut = bytes(int(o) for o in brut.split("-")).decode("ascii")
        except (ValueError, UnicodeDecodeError):
            return None
    return brut if _NOM_IMAGE.match(brut) else None


def urls_image(a) -> list:
    """URL d image a essayer, de la plus fiable a la moins fiable.

    Keepa fournit le vrai nom de fichier de l image du produit ; c est la
    source la plus sure. L URL construite a partir de l ASIN reste en second
    recours : elle fonctionne pour la majorite du catalogue, mais elle echouait
    sur environ 15 % des aubaines, qui etaient alors purement et simplement
    ecartees faute de photo.
    """
    urls = []
    nom = nom_image_keepa(a.get("img_keepa"))
    if nom:
        urls.append(f"https://m.media-amazon.com/images/I/{nom}")
    urls.append(
        f"https://images-na.ssl-images-amazon.com/images/P/{a['asin']}.01._SCLZZZZZZZ_.jpg")
    return urls


def garder_avec_photo(aubaines):
    """Verifie que la photo existe, puis retire les doublons visuels.

    Deux variantes du meme produit (tailles, couleurs) ont des ASIN
    differents, donc des URL d image differentes — mais Amazon leur sert
    exactement le meme fichier. Comparer l empreinte des octets telecharges
    est donc le moyen le plus sur de reperer les doublons que le titre n a
    pas permis de detecter : c est le produit qui decide, pas sa description.

    L image est telechargee une seule fois et sert aux deux usages : preuve
    d existence et empreinte. On s arrete a 32 Ko, largement assez pour
    distinguer deux photos differentes, dix fois moins de bande passante.
    """
    from concurrent.futures import ThreadPoolExecutor
    import hashlib

    INCERTAIN = "?"

    def empreinte(a):
        """Essaie chaque URL candidate ; garde la premiere qui donne une image."""
        reseau_ko = False
        for url in (a.get("urls_image") or [a.get("image")]):
            if not url:
                continue
            try:
                r = requests.get(url, timeout=12, stream=True)
                if r.status_code != 200:
                    r.close()
                    continue
                octets = b""
                for bloc in r.iter_content(8192):
                    octets += bloc
                    if len(octets) >= 32768:
                        break
                r.close()
                # Le GIF « image absente » d Amazon fait une quarantaine d octets.
                if len(octets) <= 1000:
                    continue
                a["image"] = url          # on retient celle qui a repondu
                return hashlib.md5(octets).hexdigest()
            except requests.RequestException:
                reseau_ko = True
        # Reseau qui tousse : on garde l aubaine sans tenter de la dedoublonner.
        # Mieux vaut un doublon qu une aubaine perdue.
        return INCERTAIN if reseau_ko else None

    with ThreadPoolExecutor(max_workers=16) as pool:
        empreintes = list(pool.map(empreinte, aubaines))

    sans_photo = 0
    groupes, incertains = {}, []
    for a, emp in zip(aubaines, empreintes):
        if emp is None:
            sans_photo += 1
        elif emp == INCERTAIN:
            incertains.append(a)
        else:
            groupes.setdefault(emp, []).append(a)

    gardees = [choisir_moins_cher(g) for g in groupes.values()] + incertains
    gardees.sort(key=lambda x: x["rabais"], reverse=True)

    doublons = sum(len(g) - 1 for g in groupes.values())
    if sans_photo:
        print(f"  {sans_photo} aubaine(s) sans photo ecartee(s) — la photo est obligatoire.")
    if doublons:
        print(f"  {doublons} doublon(s) visuel(s) retire(s) — meme photo, on garde le moins cher.")
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
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a> · <a href="/divulgation.html">Divulgation d'affiliation</a><br>En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</footer>
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


def section_eclair_html(offres) -> str:
    """Bandeau des offres eclair, au-dessus de la grille du jour.

    Ces cartes pointent directement vers Amazon, contrairement aux autres :
    une offre eclair vit quelques heures, lui fabriquer une page /aubaine/
    reviendrait a semer des liens morts dans le site et dans l archive.

    Le compte a rebours est calcule dans le navigateur a partir d un horodatage
    Unix. Une offre qui expire pendant la visite disparait d elle-meme, sans
    attendre la prochaine generation.
    """
    if not offres:
        return ""
    cartes = "\n".join(f"""<a class="carte eclair" href="{e(o['lien'])}"
 rel="nofollow sponsored noopener" target="_blank" data-fin="{int(o['fin'])}">
<img src="{e(o['image'])}" alt="{e(o['titre'])}" loading="lazy"
 onload="if(this.naturalWidth<2)this.closest('.carte').remove()"
 onerror="this.closest('.carte').remove()">
<span class="rabais">−{round(o['rabais'])} %</span>
<span class="cat">⚡ Offre éclair</span>
<span class="t">{e(o['titre'][:70])}</span>
<span class="p">{e(prix_txt(o))}</span>
<span class="chrono">—</span></a>""" for o in offres)
    return f"""<section class="bloc-eclair">
<h2>⚡ Offres éclair en cours</h2>
<p class="sous">Des rabais à durée limitée d'Amazon.ca, vérifiés il y a quelques minutes.
Ils se terminent au compte à rebours indiqué — et repartent au prix normal ensuite.</p>
<section class="grille eclairs">{cartes}</section>
<script>
(function(){{
  var cartes=[].slice.call(document.querySelectorAll('.carte.eclair'));
  function tic(){{
    var maintenant=Date.now()/1000;
    cartes.forEach(function(c){{
      var reste=(+c.dataset.fin)-maintenant;
      var z=c.querySelector('.chrono');
      if(reste<=0){{c.style.display='none';return;}}
      var h=Math.floor(reste/3600),m=Math.floor(reste%3600/60),s=Math.floor(reste%60);
      z.textContent=h>0?('finit dans '+h+' h '+(m<10?'0':'')+m):
                        ('finit dans '+m+' min '+(s<10?'0':'')+s);
    }});
  }}
  tic();setInterval(tic,1000);
}})();
</script>
</section>"""


def section_rouge_html(rouges, mention=None) -> str:
    """Bloc « Sous le prix conseillé ».

    Le pourcentage affiché est celui qu'Amazon montre en rouge sur sa fiche,
    donc le visiteur retrouve le même chiffre en arrivant là-bas. La mention
    du prix conseillé est explicite : on ne fait pas passer une remise
    théorique pour une baisse de prix.
    """
    if not rouges:
        return ""
    if mention:
        promesse = ("Les produits affichés en rouge sur Amazon. Le pourcentage est celui "
                    "d'Amazon, calculé sur le prix conseillé du fabricant — et on ne garde "
                    f"que ceux dont le prix est <strong>{e(mention)}</strong>. "
                    "La remise annoncée est là, et le prix est réellement bas en ce moment.")
    else:
        promesse = ("Les produits affichés en rouge sur Amazon. Le pourcentage est celui "
                    "d'Amazon, calculé sur le <strong>prix conseillé du fabricant</strong> — "
                    "un prix auquel beaucoup d'articles ne se vendent jamais. À vérifier "
                    "contre l'historique avant d'acheter : ces rabais-là ne sont pas "
                    "confirmés par l'évolution du prix.")
    cartes = "\n".join(f"""<a class="carte rouge" href="{e(o['lien'])}"
 rel="nofollow sponsored noopener" target="_blank">
<img src="{e(o['image'])}" alt="{e(o['titre'])}" loading="lazy"
 onload="if(this.naturalWidth<2)this.closest('.carte').remove()"
 onerror="this.closest('.carte').remove()">
<span class="rabais">−{round(o['rabais'])} %</span>
<span class="cat">🔻 {e(o['categorie'])}</span>
<span class="t">{e(o['titre'][:70])}</span>
<span class="p">{e(prix_txt(o))}</span>
<span class="conseille">au lieu de {e(f"{o['conseille']:.2f}".replace(".", ","))} $</span></a>"""
        for o in rouges)
    return f"""<section class="bloc-rouge">
<h2>🔻 Sous le prix conseillé</h2>
<p class="sous">{promesse}</p>
<section class="grille rouges">{cartes}</section>
</section>"""


WH_SLUG = "amazon-warehouse"
WH_TITRE = "Amazon Warehouse"


def cartes_warehouse_html(lots) -> str:
    """Cartes Warehouse : etat affiche, prix du neuf rappele barre."""
    morceaux = []
    for o in lots:
        neuf = ""
        if o.get("neuf"):
            montant = f"{o['neuf']:.2f}".replace(".", ",")
            neuf = f'<span class="neuf">au lieu de {e(montant)} $ neuf</span>'
        morceaux.append(f"""<a class="carte entrepot" href="{e(o['lien'])}"
 rel="nofollow sponsored noopener" target="_blank">
<img src="{e(o['image'])}" alt="{e(o['titre'])}" loading="lazy"
 onload="if(this.naturalWidth<2)this.closest('.carte').remove()"
 onerror="this.closest('.carte').remove()">
<span class="rabais">\u2212{round(o['rabais'])} %</span>
<span class="cat">\U0001F4E6 {e(o['etat'])}</span>
<span class="t">{e(o['titre'][:70])}</span>
<span class="p">{e(prix_txt(o))}</span>
{neuf}</a>""")
    return "\n".join(morceaux)


def presentation_warehouse() -> str:
    """Le paragraphe d explication, identique sur l accueil et sur la page."""
    return ("Des articles retournés par d'autres clients, vérifiés et revendus "
            "par Amazon à rabais. <strong>Ce sont de vraies baisses de prix</strong>, "
            "pas des prix conseillés gonflés — l'écart affiché est calculé sur le "
            "prix du neuf. En échange, ce sont des articles d'occasion : l'état est "
            "indiqué sur chaque carte, et la garantie de retour de 30 jours d'Amazon "
            "s'applique quand même. Souvent un seul exemplaire disponible, donc ça "
            "part vite.")


def section_warehouse_html(lots) -> str:
    """Apercu Warehouse sur l accueil : les quatre meilleurs, puis un bouton.

    Vingt-quatre cartes en haut de page repoussaient les aubaines du jour trop
    bas. Quatre suffisent a montrer ce qu on y trouve ; le reste vit sur sa
    propre page, qui a en plus l avantage d etre une URL indexable.
    """
    if not lots:
        return ""
    apercu = lots[:WH_ACCUEIL]
    reste = max(0, len(lots) - len(apercu))
    bouton = (f'<a class="bouton-cat" href="/categorie/{WH_SLUG}.html">'
              f'Voir toute la catégorie Amazon Warehouse'
              + (f' <span>({reste} de plus)</span>' if reste else '') + '</a>')
    return f"""<section class="bloc-entrepot">
<h2>\U0001F4E6 {WH_TITRE} — des retours à petit prix</h2>
<p class="sous">{presentation_warehouse()}</p>
<section class="grille entrepots">{cartes_warehouse_html(apercu)}</section>
{bouton}
</section>"""


def page_warehouse(lots, maj_lisible) -> str:
    """Page de categorie Amazon Warehouse, avec la selection complete."""
    desc = ("Les meilleures aubaines Amazon Warehouse au Québec : des retours "
            "clients vérifiés et revendus à rabais par Amazon. État indiqué, "
            "prix du neuf comparé, mis à jour trois fois par jour.")
    contenu = (f'<section class="grille entrepots">{cartes_warehouse_html(lots)}</section>'
               if lots else
               '<p class="vide">Aucune aubaine Warehouse en ce moment — la '
               'sélection change plusieurs fois par jour, reviens tantôt ! '
               '<a href="/">Voir les aubaines du jour →</a></p>')
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Amazon Warehouse au Québec — retours à petit prix | Chasseurs de Deals</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(DOMAINE)}/categorie/{WH_SLUG}.html">
<meta name="robots" content="index,follow,max-image-preview:large">
<style>{CSS}</style>
{GOOGLE_VERIF}
{ONESIGNAL}
</head>
<body>
<header><a class="logo" href="/">🔥 Chasseurs de Deals Québec</a>
<a class="fb" href="{e(PAGE_FACEBOOK)}" rel="noopener">Suivre la page Facebook</a></header>
<main>
<nav class="fil"><a href="/">Accueil</a> › <span>{WH_TITRE}</span></nav>
<section class="intro">
<h1>\U0001F4E6 Amazon Warehouse au Québec</h1>
<p>{presentation_warehouse()}</p>
</section>
{chips_html(WH_SLUG)}
{bloc_recherche("🔎 Rechercher dans Amazon Warehouse… (nom, marque)")}
{contenu}
{guide_html(WH_SLUG)}
{formulaire_infolettre("aubaines")}
</main>
<footer>Mis à jour le {e(maj_lisible)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a> · <a href="/divulgation.html">Divulgation d'affiliation</a><br>En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</footer>
</body></html>"""


def bloc_recherche(indice: str) -> str:
    """Champ de recherche qui filtre TOUTES les cartes de la page.

    Une seule implementation pour l accueil et pour les pages categorie. Le
    script ne connait pas les sections a l avance : il ramasse chaque .carte
    presente, d ou qu elle vienne — offres eclair, Warehouse, aubaines du jour.
    Une section dont toutes les cartes sont masquees se cache elle-meme, pour
    ne pas laisser un titre orphelin au-dessus du vide.

    Le recensement attend DOMContentLoaded. Sans cette attente, le script
    s executerait a l endroit ou il est ecrit dans la page — donc AVANT la
    grille des aubaines du jour, qu il ne verrait jamais. C est exactement le
    bogue qu on a eu : la recherche ne trouvait que les huit cartes des deux
    bandeaux du haut et annoncait « 0 resultat » sur 1 006 produits.
    """
    return f"""<div class="recherche"><input type="search" id="q"
 placeholder="{e(indice)}" autocomplete="off"><span class="r-nb" id="qn"></span></div>
<p class="r-vide" id="qv" hidden>Aucune aubaine ne correspond. Essaie un mot plus court —
« casque » plutôt que « casque bluetooth sony ».</p>
<script>
(function(){{
  function demarrer(){{
    var q=document.getElementById('q'),n=document.getElementById('qn'),
        v=document.getElementById('qv');
    if(!q)return;
    function plat(s){{return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');}}
    var cartes=[].slice.call(document.querySelectorAll('.carte')).map(function(c){{
      return {{el:c,txt:plat(c.textContent)}};}});
    var sections=[].slice.call(
      document.querySelectorAll('.bloc-eclair,.bloc-entrepot,.bloc-rouge'));
    function filtre(){{
      var t=plat(q.value.trim()),mots=t?t.split(/\s+/):[],vis=0;
      cartes.forEach(function(c){{
        var ok=!mots.length||mots.every(function(m){{return c.txt.indexOf(m)>=0;}});
        c.el.style.display=ok?'':'none';if(ok)vis++;}});
      sections.forEach(function(s){{
        var reste=[].slice.call(s.querySelectorAll('.carte')).some(function(c){{
          return c.style.display!=='none';}});
        s.style.display=(mots.length&&!reste)?'none':'';}});
      n.textContent=mots.length?vis+' résultat'+(vis>1?'s':''):'';
      v.hidden=!mots.length||vis>0;}}
    q.addEventListener('input',filtre);
  }}
  if(document.readyState==='loading'){{
    document.addEventListener('DOMContentLoaded',demarrer);
  }}else{{demarrer();}}
}})();
</script>"""


def chips_html(active_slug: str = "") -> str:
    chips = [f'<a class="chip entrepot{" actif" if active_slug == WH_SLUG else ""}"'
             f' href="/categorie/{WH_SLUG}.html">\U0001F4E6 {WH_TITRE}</a>']
    for nom, slug in CATS_PAGES:
        lib = CATS_LIBELLES.get(nom, nom)
        cls = "chip actif" if slug == active_slug else "chip"
        chips.append(f'<a class="{cls}" href="/categorie/{slug}.html">{e(lib)}</a>')
    return '<nav class="chips">' + "".join(chips) + "</nav>"


def guide_html(slug: str) -> str:
    """Contenu editorial de la page categorie.

    Place sous la grille : les aubaines restent au premier ecran, et Google
    indexe le texte tout de meme. C est ce qui distingue une page categorie
    d une simple liste de produits regeneree chaque matin.
    """
    texte = INTROS.get(slug)
    return f'<section class="guide">{texte}</section>' if texte else ""


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
{bloc_recherche("🔎 Rechercher dans cette catégorie… (nom, marque)")}
{contenu}
{guide_html(slug)}
{formulaire_infolettre("aubaines")}
</main>
<footer>Mis à jour le {e(maj_lisible)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a> · <a href="/divulgation.html">Divulgation d'affiliation</a><br>En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</footer>
</body></html>"""


def page_index(aubaines, maj_iso, maj_lisible, eclairs=(), rouges=(), mention_rouge=None,
               entrepot=()) -> str:
    cartes = cartes_html(aubaines)
    bloc_eclair = section_eclair_html(eclairs)
    bloc_rouge = section_rouge_html(rouges, mention_rouge)
    bloc_entrepot = section_warehouse_html(entrepot)
    desc = ("Les meilleures aubaines Amazon du jour au Québec, mises à jour chaque matin. "
            "Rabais vérifiés, une page par aubaine. Par Chasseurs de Deals Québec.")
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aubaines du jour au Québec — Chasseurs de Deals Québec</title>
<link rel="alternate" type="application/rss+xml" title="Aubaines du jour au Québec" href="/rss.xml">
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
{bloc_eclair}
{bloc_entrepot}
{bloc_rouge}
{chips_html()}
{bloc_recherche("🔎 Rechercher dans tout le site… (nom, marque, catégorie)")}
<section class="grille" id="grille">{cartes}</section>
{formulaire_infolettre("aubaines")}
</main>
<footer>Mis à jour le {e(maj_lisible)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a> · <a href="/divulgation.html">Divulgation d'affiliation</a><br>En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</footer>
</body></html>"""


def sitemap(aubaines, maj_iso, archives=None) -> str:
    urls = [f"<url><loc>{DOMAINE}/</loc><lastmod>{maj_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for _nom, slug in list(CATS_PAGES) + [(WH_TITRE, WH_SLUG)]:
        urls.append(f"<url><loc>{DOMAINE}/categorie/{slug}.html</loc>"
                    f"<lastmod>{maj_iso}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>")
    for a in aubaines:
        urls.append(f"<url><loc>{DOMAINE}/aubaine/{a['slug']}.html</loc>"
                    f"<lastmod>{maj_iso}</lastmod><changefreq>daily</changefreq></url>")
    urls.append(f"<url><loc>{DOMAINE}/divulgation.html</loc><changefreq>monthly</changefreq><priority>0.3</priority></url>")
    vivants = {a["slug"] for a in aubaines}
    for slug, ent in (archives or {}).items():
        if slug in vivants:
            continue
        urls.append(f"<url><loc>{DOMAINE}/aubaine/{slug}.html</loc>"
                    f"<lastmod>{ent.get('dernier', maj_iso)}</lastmod><changefreq>monthly</changefreq><priority>0.4</priority></url>")
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
.bloc-entrepot{margin:26px 0 6px;padding:18px 4px 4px;border-top:1px solid #26303a;border-bottom:1px solid #26303a}
.bloc-entrepot h2{font-size:21px;margin:0 0 6px;color:#7fd1b9}
.bloc-entrepot .sous{margin:0 0 16px;color:#8496a8;font-size:14px;line-height:1.6;max-width:700px}
.bloc-entrepot .sous strong{color:#c9d6e2}
.bouton-cat{display:inline-block;margin:14px 4px 6px;padding:11px 20px;border-radius:999px;
 background:#7fd1b91a;border:1px solid #7fd1b966;color:#7fd1b9;font-weight:600;font-size:14px}
.bouton-cat:hover{background:#7fd1b92e}
.bouton-cat span{font-weight:400;color:#8496a8}
.chip.entrepot{border-color:#7fd1b966;color:#7fd1b9}
.carte.entrepot{box-shadow:0 0 0 1px #7fd1b944}
.carte.entrepot .cat{color:#7fd1b9}
.carte.entrepot .neuf{display:block;margin-top:3px;font-size:12px;color:#8496a8;text-decoration:line-through}
.bloc-rouge{margin:26px 0 6px;padding:18px 4px 4px;border-top:1px solid #26303a;border-bottom:1px solid #26303a}
.bloc-rouge h2{font-size:21px;margin:0 0 6px;color:#ff6b6b}
.bloc-rouge .sous{margin:0 0 16px;color:#8496a8;font-size:14px;line-height:1.6;max-width:680px}
.bloc-rouge .sous strong{color:#c9d6e2}
.carte.rouge{box-shadow:0 0 0 1px #ff6b6b44}
.carte.rouge .cat{color:#ff6b6b}
.carte.rouge .conseille{display:block;margin-top:3px;font-size:12px;color:#8496a8;text-decoration:line-through}
.bloc-eclair{margin:26px 0 6px;padding:18px 4px 4px;border-top:1px solid #26303a;border-bottom:1px solid #26303a}
.bloc-eclair h2{font-size:21px;margin:0 0 6px;color:#ffcc33}
.bloc-eclair .sous{margin:0 0 16px;color:#8496a8;font-size:14px;line-height:1.6;max-width:640px}
.carte.eclair{position:relative;box-shadow:0 0 0 1px #ffcc3355}
.carte.eclair .cat{color:#ffcc33}
.carte.eclair .chrono{display:block;margin-top:4px;font-size:12px;font-weight:600;color:#ff8a5b;
 font-variant-numeric:tabular-nums}
.guide{max-width:760px;margin:34px auto 0;padding:0 4px;line-height:1.75;color:#c9d6e2}
.guide h2{font-size:20px;margin:26px 0 10px;color:#fff}
.guide h3{font-size:16px;margin:20px 0 8px;color:#fff}
.guide p{margin:0 0 14px}
.guide ul{margin:0 0 14px;padding-left:20px}
.guide li{margin:0 0 8px}
.guide strong{color:#fff}
.guide .avis{background:#171d24;border-left:3px solid #ffcc33;border-radius:6px;padding:12px 16px;margin:0 0 14px}
.guide .avis p{margin:0}
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


# ---------------------------------------------------------------------------
# ARCHIVE : les pages d'aubaines restent en ligne apres l'expiration du rabais.
# Chaque page conserve son historique de prix : c'est du contenu unique que
# Google ne trouve nulle part ailleurs, et les epingles / liens ne meurent plus.
# ---------------------------------------------------------------------------
ARCHIVE_FICHIER = Path(__file__).parent / "archive.json"
JOURS_ARCHIVE = 120
MAX_ARCHIVE = 4000
INDEXNOW_CLE = "8f3c1d27a94b4e6fb0c5d2e719a6f480"


def charger_archive() -> dict:
    if ARCHIVE_FICHIER.exists():
        try:
            donnees = json.loads(ARCHIVE_FICHIER.read_text(encoding="utf-8"))
            return donnees if isinstance(donnees, dict) else {}
        except Exception as exc:
            print(f"Archive illisible, on repart a zero : {exc}")
    return {}


def fusionner_archive(arch: dict, aubaines: list, jour: str) -> dict:
    for a in aubaines:
        ent = arch.get(a["slug"]) or {"prix": [], "premier": jour}
        hist = ent.get("prix") or []
        if a["prix"]:
            valeur = round(float(a["prix"]), 2)
            if not hist or hist[-1][1] != valeur:
                hist.append([jour, valeur])
        ent.update({
            "asin": a["asin"], "titre": a["titre"], "image": a["image"],
            "lien": a["lien"], "categorie": a["categorie"],
            "rabais": a["rabais"], "dernier": jour, "prix": hist[-60:],
        })
        ent.setdefault("premier", jour)
        arch[a["slug"]] = ent
    limite = (datetime.now(timezone.utc) - timedelta(days=JOURS_ARCHIVE)).strftime("%Y-%m-%d")
    arch = {k: v for k, v in arch.items() if str(v.get("dernier", "")) >= limite}
    if len(arch) > MAX_ARCHIVE:
        arch = dict(sorted(arch.items(), key=lambda kv: str(kv[1].get("dernier", "")), reverse=True)[:MAX_ARCHIVE])
    return arch


def page_archive(slug: str, ent: dict, connexes: list, maj_lisible: str) -> str:
    hist = ent.get("prix") or []
    dernier = f"{hist[-1][1]:.2f} $".replace(".", ",") if hist else "n/d"
    plus_bas = f"{min(p[1] for p in hist):.2f} $".replace(".", ",") if hist else "n/d"
    cats = dict(CATS_PAGES)
    cat_nom = ent.get("categorie", "Aubaines")
    cat_slug = cats.get(cat_nom, "")
    lien_cat = f"/categorie/{cat_slug}.html" if cat_slug else "/"
    lignes = "".join(
        f"<tr><td style='padding:8px 14px;border-bottom:1px solid #223'>{e(d)}</td>"
        f"<td style='padding:8px 14px;border-bottom:1px solid #223;text-align:right'>"
        f"{('%.2f' % v).replace('.', ',')} $</td></tr>"
        for d, v in reversed(hist[-24:])
    )
    titre_page = f"{ent.get('titre', 'Aubaine')} — historique de prix au Québec"
    desc = (f"Historique de prix de {ent.get('titre', 'cet article')} au Québec. "
            f"Prix le plus bas observé : {plus_bas}. Cette aubaine est terminée — "
            f"voir les rabais en cours.")
    url = f"{DOMAINE}/aubaine/{slug}.html"
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titre_page)} | Chasseurs de Deals Québec</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<style>{CSS}</style>
{GOOGLE_VERIF}
</head>
<body>
<header><a class="logo" href="/">🔥 Chasseurs de Deals Québec</a>
<a class="fb" href="{e(PAGE_FACEBOOK)}" rel="noopener">Suivre la page Facebook</a></header>
<main>
<section class="intro">
<p style="background:#3a2a12;border:1px solid #6b4b16;color:#ffce6a;padding:12px 16px;border-radius:10px;font-weight:700">
⏳ Cette aubaine est terminée. Voici son historique de prix — et les rabais en cours plus bas.</p>
<h1>{e(ent.get('titre', 'Aubaine'))}</h1>
<p>Catégorie : <a href="{e(lien_cat)}">{e(cat_nom)}</a> ·
Repérée pour la première fois le {e(str(ent.get('premier', '')))} ·
Dernière fois en rabais le {e(str(ent.get('dernier', '')))}.</p>
<p><strong>Dernier prix observé : {e(dernier)}</strong> · Prix le plus bas jamais vu : <strong>{e(plus_bas)}</strong></p>
<h2>Historique de prix</h2>
<table style="width:100%;max-width:520px;border-collapse:collapse;font-size:15px">
<tr><th style="text-align:left;padding:8px 14px;border-bottom:2px solid #2c3a4d">Date</th>
<th style="text-align:right;padding:8px 14px;border-bottom:2px solid #2c3a4d">Prix</th></tr>
{lignes}
</table>
<p style="margin-top:22px"><a class="fb" href="{e(lien_cat)}">Voir les aubaines {e(cat_nom.lower())} du jour</a></p>
<h2>Les aubaines en cours dans cette catégorie</h2>
</section>
{cartes_html(connexes)}
</main>
<footer>Mis à jour le {e(maj_lisible)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a> · <a href="/divulgation.html">Divulgation d'affiliation</a><br>En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</footer>
</body></html>"""


def rss_xml(aubaines, maj_iso: str) -> str:
    items = []
    for a in aubaines[:60]:
        lien = f"{DOMAINE}/aubaine/{a['slug']}.html"
        titre = f"{a['titre']} — {round(a['rabais'])} % de rabais ({prix_txt(a)})"
        items.append("<item>"
                     f"<title>{e(titre)}</title>"
                     f"<link>{e(lien)}</link>"
                     f"<guid isPermaLink=\"true\">{e(lien)}</guid>"
                     f"<category>{e(a['categorie'])}</category>"
                     f"<description>{e(titre)}</description>"
                     "</item>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0"><channel>'
            "<title>Aubaines du jour au Quebec - Chasseurs de Deals Quebec</title>"
            f"<link>{DOMAINE}/</link>"
            "<description>Les meilleurs rabais Amazon reperes chaque matin au Quebec.</description>"
            "<language>fr-ca</language>"
            + "".join(items) + "</channel></rss>\n")


def pinger_indexnow(urls: list) -> None:
    try:
        hote = DOMAINE.split("//", 1)[-1].strip("/")
        r = requests.post("https://api.indexnow.org/indexnow",
                          json={"host": hote, "key": INDEXNOW_CLE,
                                "keyLocation": f"{DOMAINE}/{INDEXNOW_CLE}.txt",
                                "urlList": urls[:1000]}, timeout=25)
        print(f"IndexNow : {r.status_code} pour {min(len(urls), 1000)} URL")
    except Exception as exc:
        print(f"IndexNow ignore : {exc}")


def page_divulgation(maj_lisible: str) -> str:
    desc = ("Divulgation d'affiliation de Chasseurs de Deals Quebec : comment le site "
            "gagne une commission sur les achats admissibles effectues sur Amazon.ca.")
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Divulgation d'affiliation — Chasseurs de Deals Québec</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(DOMAINE)}/divulgation.html">
<meta name="robots" content="index,follow">
<style>{CSS}</style>
{GOOGLE_VERIF}
</head>
<body>
<header><a class="logo" href="/">🔥 Chasseurs de Deals Québec</a>
<a class="fb" href="{e(PAGE_FACEBOOK)}" rel="noopener">Suivre la page Facebook</a></header>
<main>
<section class="intro">
<h1>Divulgation d'affiliation</h1>
<p><strong>En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</strong></p>
<p>Chasseurs de Deals Québec participe au Programme Partenaires d'Amazon.ca, un programme d'affiliation qui permet à des sites de percevoir une commission sur les achats admissibles effectués après un clic sur nos liens.</p>
<p>Concrètement : quand tu cliques sur une aubaine et que tu achètes sur Amazon, le prix que tu paies reste exactement le même. Amazon nous verse une petite commission sur la vente. C'est ce qui finance le travail de repérage quotidien des rabais.</p>
<h2>Ce que ça ne change pas</h2>
<p>Les rabais affichés sont réels et vérifiés. Aucun marchand ne paie pour apparaître sur ce site, et aucune commission n'influence le classement des aubaines : elles sont triées par pourcentage de rabais, point.</p>
<h2>Prix et disponibilité</h2>
<p>Les prix et la disponibilité affichés ici sont exacts au moment de la mise à jour (dernière : {e(maj_lisible)}) et peuvent changer à tout moment. Le prix qui fait foi est celui affiché sur Amazon.ca au moment de ton achat.</p>
<h2>Nous joindre</h2>
<p>Une question ? Écris-nous sur notre <a href="{e(PAGE_FACEBOOK)}" rel="noopener">page Facebook</a>.</p>
</section>
</main>
<footer>Mis à jour le {e(maj_lisible)} · <a href="{e(SITE_PRINCIPAL)}">chasseursdedealsqc.com</a>
· <a href="{e(PAGE_FACEBOOK)}">Facebook</a> · <a href="/divulgation.html">Divulgation d'affiliation</a><br>En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.</footer>
</body></html>"""


def main() -> int:
    aubaines = lire_aubaines()

    # Offres eclair : hors du flux habituel, affichees a part sur l accueil.
    eclairs = lire_offres_eclair({a["asin"] for a in aubaines})
    # Prix rouges : sous le prix conseille ET au plus bas depuis 90 jours.
    entrepot = lire_warehouse({a["asin"] for a in aubaines} | {o["asin"] for o in eclairs})
    rouges, mention_rouge = lire_prix_rouges(
        {a["asin"] for a in aubaines} | {o["asin"] for o in eclairs})
    if not aubaines:
        raise SystemExit("ERREUR : aucune aubaine lue — rien n'est généré (le site précédent reste en place).")

    maintenant = datetime.now(FUSEAU)
    maj_iso = maintenant.strftime("%Y-%m-%d")
    maj_lisible = (f"{maintenant.day} {MOIS_FR[maintenant.month - 1]} "
                   f"{maintenant.year} à {maintenant.hour} h {maintenant.minute:02d}")

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

    (SORTIE / "index.html").write_text(page_index(aubaines, maj_iso, maj_lisible, eclairs, rouges, mention_rouge, entrepot), encoding="utf-8")
    (SORTIE / "divulgation.html").write_text(page_divulgation(maj_lisible), encoding="utf-8")
    (SORTIE / "categorie" / f"{WH_SLUG}.html").write_text(
        page_warehouse(entrepot, maj_lisible), encoding="utf-8")
    jour = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    archives = fusionner_archive(charger_archive(), aubaines, jour)
    ARCHIVE_FICHIER.write_text(json.dumps(archives, ensure_ascii=False, sort_keys=True),
                               encoding="utf-8")
    (SORTIE / "sitemap.xml").write_text(sitemap(aubaines, maj_iso, archives), encoding="utf-8")
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

    vivants = {a["slug"] for a in aubaines}
    par_cat = {}
    for a in aubaines:
        par_cat.setdefault(a["categorie"], []).append(a)
    n_arch = 0
    for slug, ent in archives.items():
        if slug in vivants:
            continue
        connexes = par_cat.get(ent.get("categorie", ""), [])[:6]
        (SORTIE / "aubaine" / f"{slug}.html").write_text(
            page_archive(slug, ent, connexes, maj_lisible), encoding="utf-8")
        n_arch += 1
    (SORTIE / "rss.xml").write_text(rss_xml(aubaines, maj_iso), encoding="utf-8")
    (SORTIE / f"{INDEXNOW_CLE}.txt").write_text(INDEXNOW_CLE, encoding="utf-8")
    pinger_indexnow([f"{DOMAINE}/"] + [f"{DOMAINE}/aubaine/{a['slug']}.html" for a in aubaines])
    print(f"  archive : {n_arch} pages conservees, {len(archives)} entrees")
    print(f"OK : {len(aubaines)} aubaines → {SORTIE}")
    print(f"  index.html, sitemap.xml ({len(aubaines)+1} URL), robots.txt, llms.txt, "
          f"{len(aubaines)} pages d'aubaines.")

    envoyer_push(aubaines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
