# Sous-site des aubaines — marche à suivre

Ce dossier transforme ta feuille d'aubaines en un mini-site indexable par Google,
Bing **et les IA** (ChatGPT, Claude, Perplexity), hébergé gratuitement, mis à jour
tout seul chaque matin. Ton site Wix reste ta vitrine et pointera dessus.

Adresse visée : **aubaines.chasseursdedealsqc.com**

## Ce qui est déjà fait (par Claude)

- Ta feuille Google « Site_Aubaines » est **publiée en CSV** (lecture seule, données publiques — les mêmes aubaines que ton site affiche déjà).
- Le générateur `generer_site.py` est écrit et **testé** : il lit la feuille, garde les 50 meilleurs rabais, et produit une page par aubaine + `sitemap.xml` + `robots.txt` (ouvert aux IA) + `llms.txt`.
- Le workflow `.github/workflows/site.yml` est prêt : il régénère et republie le site chaque matin à 5 h 20 (20 min après ta reconstruction Make de 5 h).
- La sauvegarde de rollback de ton scénario Make est dans « Sauvegardes Make ».

## Volet 1 — Mettre le site en ligne (≈ 15 min, une seule fois)

1. **Créer le dépôt GitHub.** Sur github.com → New repository → nom `aubaines-chasseurs` → **Public** → Create.
2. **Téléverser les fichiers.** Dans le dépôt : « Add file » → « Upload files » → glisse `generer_site.py` ET le dossier `.github` (avec `workflows/site.yml` dedans) → Commit.
3. **Activer GitHub Pages.** Settings → Pages → Source : **GitHub Actions**.
4. **Lancer une première fois.** Onglet Actions → « Aubaines - generation quotidienne » → « Run workflow ». En 1-2 min, ton site est généré.

## Volet 1b — Brancher le sous-domaine (≈ 10 min + délai DNS)

Le sous-domaine `aubaines.` doit pointer vers GitHub. Où gérer le DNS dépend d'où
est ton domaine (Wix ou un registraire). La règle à ajouter :

```
Type : CNAME
Nom / Hôte : aubaines
Valeur / Cible : <ton-utilisateur-github>.github.io
```

Puis, dans GitHub → Settings → Pages → « Custom domain » : tape
`aubaines.chasseursdedealsqc.com` et coche « Enforce HTTPS ».
(Le fichier `CNAME` est déjà généré automatiquement, GitHub le reconnaîtra.)

> Dis-moi où est géré ton DNS (Wix ou ailleurs) et je te guide écran par écran
> pour cette étape — c'est la seule un peu délicate.

## Volet 2 — La page Facebook sur ton site Wix (guidage à venir)

Bandeau « Suis la page », widget Facebook dans le pied de page, et un bouton
« Voir toutes les aubaines » qui pointe vers ton nouveau sous-domaine.
On le fait ensemble dans l'éditeur Wix quand tu veux.

## Volets 3 et 4 — Notifications push (OneSignal)

Compte OneSignal gratuit + code sur le sous-site (là où c'est permis, contrairement
à Wix Harmony) + un module dans ton scénario Make pour pousser l'aubaine du jour.
On l'attaque après que le sous-site soit en ligne.

## Volet 5 — Référencement Google, Bing et IA

- **Google Search Console** (search.google.com/search-console) : ajoute la propriété `aubaines.chasseursdedealsqc.com`, puis soumets `sitemap.xml`.
- **Bing Webmaster Tools** : même chose (Bing alimente aussi Copilot).
- **Les IA** sont déjà prises en charge : `robots.txt` autorise explicitement GPTBot, ClaudeBot, PerplexityBot, Google-Extended, etc., et `llms.txt` leur résume tes aubaines. Rien de plus à faire.

## En cas de pépin

- Le générateur ne remplace **jamais** le site par du vide : s'il ne lit aucune aubaine, il s'arrête et laisse la version précédente en place.
- Pour revenir en arrière sur Make : le blueprint de secours est dans « Sauvegardes Make ».
- Pour tout arrêter : désactive le workflow dans l'onglet Actions de GitHub.
