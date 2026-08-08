#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Textes d'introduction des 8 pages categorie de aubaines.chasseursdedealsqc.com.

POURQUOI CE FICHIER EXISTE
--------------------------
Une page categorie qui ne contient qu'une grille de produits est, aux yeux de
Google, une page « mince » : rien d'original, rien qu'un agregateur ne pourrait
produire en serie. C'est exactement le profil vise par les politiques
« scaled content abuse » et « thin affiliate pages ».

Ces intros reglent ca. Elles apportent trois choses que la grille n'a pas :
un jugement (quel rabais vaut reellement la peine), un calendrier (quand
acheter) et des pieges concrets a eviter. C'est du contenu que Google ne
trouve nulle part ailleurs, et ce qui transforme une page liste en page
qui se classe.

INTEGRATION
-----------
generer_site.py importe INTROS et appelle guide_html(slug), qui insere le
bloc SOUS la grille d'aubaines, juste avant le formulaire d'infolettre. Les
aubaines restent donc au premier ecran et Google indexe le texte tout de meme.

Le HTML n'utilise que <h2>, <h3>, <p>, <ul>, <li> et <strong> : il herite des
styles .guide definis dans la feuille CSS du generateur. Pour modifier un
texte, edite la constante correspondante ci-dessous.
"""

# ---------------------------------------------------------------------------

ELECTRONIQUE = """
<h2>Comment reconnaitre un vrai rabais en electronique</h2>

<p>L'electronique est la categorie ou les prix bougent le plus, et aussi celle
ou les faux rabais sont les plus frequents. Un « prix regulier » barre sur
Amazon n'est pas toujours le prix auquel l'article s'est reellement vendu :
c'est souvent le prix suggere du fabricant, que personne ne paye. Le seul
repere fiable, c'est le prix des 30 a 90 derniers jours.</p>

<p>Comme ordre de grandeur pour Amazon.ca : un rabais de <strong>15 % sur un
televiseur recent</strong> est deja correct, et 25 % est excellent. Pour des
<strong>ecouteurs sans fil de marque</strong>, 20 % arrive regulierement et
35 % merite qu'on se depeche. Les <strong>accessoires</strong> — cables,
chargeurs, supports, cartes memoire — descendent facilement de 40 a 60 % parce
que leur marge est enorme au depart : sous les 50 %, ce n'est pas vraiment une
aubaine, c'est le prix normal du marche.</p>

<h3>Les trois pieges les plus courants</h3>

<ul>
  <li><strong>Le modele de l'an passe vendu comme nouveau.</strong> Les
  fabricants changent une lettre au numero de modele chaque annee. Un gros
  rabais sur un televiseur signifie souvent que le remplacant arrive. Ce n'est
  pas un probleme en soi — c'est meme le bon moment pour acheter — mais il faut
  le savoir.</li>
  <li><strong>Le vendeur tiers.</strong> Verifie qui expedie. « Vendu et
  expedie par Amazon » et « vendu par un tiers » ne donnent pas la meme
  experience de retour, ni les memes garanties. Sur l'electronique, ca compte.</li>
  <li><strong>La garantie canadienne.</strong> Un article importe peut ne pas
  etre couvert par le service apres-vente au Canada. Pour un achat de plus de
  200 $, ca vaut la verification de trente secondes.</li>
</ul>

<h3>Quand acheter</h3>

<p>Trois fenetres se demarquent nettement dans l'annee : le <strong>Prime
Day</strong> en juillet, le <strong>Vendredi fou et le Cyberlundi</strong> a la
fin de novembre, et le <strong>Boxing Day</strong> jusqu'a la mi-janvier. Entre
ces periodes, l'electronique se vend au prix courant, avec des baisses
ponctuelles qui durent parfois quelques heures seulement.</p>

<p>Si tu n'es pas presse, la strategie la plus payante reste la plus simple :
note l'article, attends la prochaine fenetre. Si tu es presse, la page
ci-dessus est mise a jour chaque matin — les baisses de la nuit y sont deja.</p>
"""
MAISON_CUISINE = """
<h2>Maison et cuisine : la categorie ou les rabais sont les plus profonds</h2>

<p>C'est probablement la categorie ou on trouve les meilleures affaires sur
Amazon.ca, pour une raison simple : la concurrence entre marques y est feroce
et les marges de depart sont confortables. Un <strong>petit
electromenager</strong> — friteuse a air, melangeur, autocuiseur, cafetiere —
descend couramment de 30 a 40 %, et de 50 % pendant les grandes periodes de
solde. Sous les 25 %, ce n'est pas une aubaine : c'est le prix habituel.</p>

<p>Les <strong>articles de rangement, la literie et la decoration</strong>
suivent une autre logique : les rabais y sont moins spectaculaires mais plus
constants, autour de 20 a 30 %.</p>

<h3>Ce qu'il faut verifier avant de cliquer</h3>

<ul>
  <li><strong>La quantite.</strong> C'est le piege numero un de cette
  categorie. Un prix qui semble trop beau porte souvent sur une unite alors que
  la photo en montre quatre — ou l'inverse. Lis le titre au complet, pas
  seulement le prix.</li>
  <li><strong>Les dimensions.</strong> Beaucoup de fiches affichent encore les
  mesures en pouces americains. Une etagere « parfaite » qui ne rentre pas dans
  le coin prevu, c'est un retour a organiser.</li>
  <li><strong>Le voltage et la prise.</strong> Rare, mais reel sur les articles
  importes. Au Canada, on veut du 120 V avec une prise nord-americaine.</li>
  <li><strong>Les pieces de remplacement.</strong> Pour une cafetiere ou un
  robot culinaire, verifie que les filtres, joints et accessoires sont
  disponibles separement. Un appareil a 40 % de rabais dont on ne trouve pas le
  panier de rechange finit au placard.</li>
</ul>

<h3>Quand acheter</h3>

<p>Le <strong>Vendredi fou</strong> reste le sommet de l'annee pour le petit
electromenager, suivi du <strong>Boxing Day</strong>. Mais il y a une fenetre
que peu de gens exploitent : <strong>janvier et fevrier</strong>. C'est le
moment des resolutions et du rangement, les marques poussent fort sur les
articles de cuisine sante et d'organisation, et la concurrence fait baisser les
prix hors des periodes officielles de solde.</p>

<p>Pour la literie et les serviettes, vise la <strong>fin aout</strong> : la
rentree scolaire tire les prix vers le bas sur tout ce qui garnit un logement
etudiant.</p>
"""

MODE = """
<h2>Mode : pourquoi 40 % de rabais n'est pas une aubaine</h2>

<p>La mode fonctionne a l'inverse des autres categories. Les rabais y sont
tellement systematiques qu'ils font partie du modele d'affaires : une piece est
mise en marche a un prix que presque personne ne paye, puis demarquee par
paliers jusqu'a ce qu'elle parte. Resultat : <strong>en dessous de 40 %, ce
n'est pas un rabais, c'est le calendrier normal</strong>. Le seuil a partir
duquel ca devient interessant se situe autour de 50 a 60 %, et les vraies
liquidations depassent 70 %.</p>

<p>La consequence pratique : sur un vetement, la question n'est presque jamais
« est-ce que le rabais est bon », mais « est-ce que la taille sera la
bonne ».</p>

<h3>Le seul vrai risque : la taille</h3>

<ul>
  <li><strong>Les tailles varient enormement d'une marque a l'autre.</strong>
  Un medium chez une marque nord-americaine et un medium chez une marque
  asiatique n'ont souvent rien a voir. Cherche le tableau des mesures en
  centimetres dans la fiche — pas la lettre, les centimetres.</li>
  <li><strong>Lis les commentaires qui parlent de taille.</strong> C'est le
  meilleur indicateur disponible. Quand plusieurs personnes ecrivent « taille
  petit », c'est vrai.</li>
  <li><strong>Verifie la politique de retour avant d'acheter</strong>, surtout
  chez un vendeur tiers. Certains articles de mode ne sont pas retournables, et
  un retour paye de sa poche efface tout le rabais.</li>
  <li><strong>Mefie-toi des prix absurdes sur les marques recherchees.</strong>
  Une paire de chaussures de grande marque a 80 % de rabais chez un vendeur
  inconnu, c'est rarement une bonne surprise.</li>
</ul>

<h3>Quand acheter</h3>

<p>La mode suit les saisons, pas les evenements commerciaux. Les meilleures
liquidations tombent en <strong>fin de saison</strong> : les manteaux d'hiver
en <strong>fevrier et mars</strong>, les vetements d'ete en
<strong>aout</strong>. Au Quebec, ca veut dire acheter son parka au moment ou
on n'y pense plus — c'est la qu'il coute la moitie du prix de novembre.</p>

<p>Pour les articles de base qui ne se demodent pas — chaussettes,
sous-vetements, t-shirts unis —, le <strong>Vendredi fou</strong> reste le
meilleur moment pour faire des provisions.</p>
"""
JOUETS_JEUX = """
<h2>Jouets et jeux : le calendrier compte plus que le rabais</h2>

<p>C'est la categorie ou le moment de l'achat fait la plus grande difference,
et la seule ou <strong>attendre a la derniere minute coute systematiquement
plus cher</strong>. Les prix des jouets montent en fleche a partir de la
mi-novembre et restent eleves jusqu'a Noel. Le meme article achete trois
semaines plus tot coute souvent 20 a 30 % de moins.</p>

<p>Pour situer un rabais : les <strong>jeux de societe</strong> descendent
couramment de 30 a 40 %, et c'est un bon moment pour acheter. Les
<strong>ensembles de blocs de construction de grande marque</strong> se
demarquent rarement au-dela de 20 % — quand tu vois 30 % ou plus, c'est un vrai
signal. Les <strong>jeux video</strong> perdent de la valeur par paliers
previsibles apres leur sortie, et les grosses baisses arrivent surtout lors des
evenements de solde.</p>

<h3>Ce qu'il faut verifier</h3>

<ul>
  <li><strong>L'age recommande.</strong> Il figure sur la fiche et il est la
  pour une raison — souvent la presence de petites pieces.</li>
  <li><strong>La langue.</strong> C'est le piege specifique au Quebec. Beaucoup
  de jeux de societe vendus sur Amazon.ca sont en version anglaise seulement.
  Cherche « version francaise » ou « bilingue » dans le titre, et si ce n'est
  pas ecrit, pars du principe que c'est en anglais.</li>
  <li><strong>Les piles.</strong> « Piles non incluses » sur un jouet offert le
  25 decembre au matin, c'est un classique evitable.</li>
  <li><strong>Le vendeur.</strong> Les contrefacons existent sur les marques de
  jouets les plus connues. Privilegie « expedie par Amazon ».</li>
</ul>

<h3>Quand acheter</h3>

<p>La regle est simple et elle vaut de l'argent : <strong>achete les cadeaux de
Noel entre la fin octobre et le 20 novembre</strong>. Le Vendredi fou offre de
bons prix sur les jouets, mais l'inventaire des articles populaires est deja
entame et les prix des semaines qui suivent remontent.</p>

<p>L'autre bonne fenetre, beaucoup plus discrete : <strong>la
mi-janvier</strong>. Les detaillants liquident les surplus des fetes, et c'est
le meilleur moment de l'annee pour acheter a petit prix — pour une fete
d'enfant en mars ou simplement pour prendre de l'avance.</p>
"""

SPORTS_PLEIN_AIR = """
<h2>Sports et plein air : acheter a contretemps</h2>

<p>Au Quebec, cette categorie est presque entierement dictee par la saison, et
c'est une bonne nouvelle : les ecarts de prix entre le pic et le creux sont
enormes, et parfaitement previsibles. <strong>L'equipement se paye le plus cher
au moment ou on en a envie, et le moins cher six mois plus tot.</strong></p>

<p>Concretement : le materiel de camping est a son meilleur prix en
<strong>septembre et octobre</strong>, l'equipement de ski et de patin en
<strong>mars et avril</strong>, les velos et accessoires en <strong>fin
d'ete</strong>, et tout ce qui touche l'entrainement a la maison en
<strong>juin</strong>, quand plus personne n'y pense.</p>

<h3>Ce qui distingue une bonne affaire d'un mauvais achat</h3>

<ul>
  <li><strong>L'equipement de securite ne se magasine pas au rabais.</strong>
  Casque, gilet de sauvetage, harnais : achete la bonne piece au bon prix, pas
  la moins chere. Un casque doit aussi etre remplace apres un impact, peu
  importe son etat apparent.</li>
  <li><strong>Verifie les dimensions et le poids reels.</strong> Une tente
  « 4 personnes » loge quatre personnes sans bagages ni espace pour bouger. La
  regle empirique : enleve une personne au chiffre annonce.</li>
  <li><strong>Attention aux marques inconnues sur l'equipement
  technique.</strong> Sur une chaise pliante, le risque est faible. Sur un
  rechaud, une batterie externe ou un support a velo, la qualite de fabrication
  n'est pas un detail esthetique.</li>
  <li><strong>Les frais d'expedition sur les gros articles.</strong> Un rabais
  de 30 % qui s'evapore en frais de livraison n'est pas un rabais.</li>
</ul>

<h3>Le reflexe qui fait economiser le plus</h3>

<p>Fais ta liste d'equipement <strong>a la fin d'une saison, pas au debut de la
suivante</strong>. C'est en rangeant le materiel de camping en octobre qu'on
sait exactement ce qui manquait — et c'est precisement le moment ou tout est en
liquidation.</p>

<p>Les aubaines ci-dessus sont mises a jour chaque matin, ce qui est utile pour
la deuxieme strategie : les baisses ponctuelles hors saison, qui ne durent
parfois qu'une journee.</p>
"""
OUTILS_BRICOLAGE = """
<h2>Outils et bricolage : le piege de l'outil nu</h2>

<p>Il y a une chose a comprendre dans cette categorie avant tout le reste, et
elle explique 90 % des mauvaises surprises : les outils sans fil se vendent en
deux versions. <strong>L'ensemble complet</strong> comprend l'outil, une ou
deux batteries et le chargeur. <strong>L'outil nu</strong> ne comprend que
l'outil.</p>

<p>Un « rabais spectaculaire » sur une perceuse de grande marque est tres
souvent un outil nu. Ce n'est pas de la tromperie — c'est ecrit dans la fiche,
en petit, sous une mention comme « bare tool » ou « outil seulement » — mais ca
change tout : une batterie coute facilement plus cher que l'outil lui-meme.
L'ensemble n'a de sens que si tu possedes deja des batteries de la meme marque
et de la meme gamme.</p>

<h3>Reperes de prix</h3>

<p>Les <strong>outils electriques de grande marque</strong> descendent
generalement de 20 a 30 %, et 40 % est un excellent rabais. La
<strong>quincaillerie, les fixations et les accessoires</strong> — meches,
lames, embouts — se demarquent bien plus profondement, de 40 a 60 %. Les
<strong>ensembles combo</strong> offerts pendant les grandes periodes de solde
sont souvent la meilleure valeur au dollar de toute la categorie.</p>

<h3>A verifier</h3>

<ul>
  <li><strong>La compatibilite des batteries.</strong> Chaque fabricant a son
  systeme, et ils ne sont pas interchangeables. Choisir une plateforme et s'y
  tenir vaut plus, sur cinq ans, que n'importe quel rabais ponctuel.</li>
  <li><strong>Le voltage et l'amperage-heure.</strong> Deux batteries de meme
  voltage n'ont pas la meme autonomie. L'amperage-heure (Ah) est le chiffre qui
  compte.</li>
  <li><strong>La garantie au Canada.</strong> Les grandes marques offrent des
  garanties longues, mais elles s'appliquent au reseau canadien. Un outil
  importe peut ne pas etre couvert.</li>
</ul>

<h3>Quand acheter</h3>

<p>Trois pointes dans l'annee : la <strong>fete des Peres</strong> en juin, le
<strong>Vendredi fou</strong>, et le <strong>debut du printemps</strong>, quand
la saison des renovations demarre. Pour les projets d'ete, acheter en mars
evite a la fois les prix de pointe et les ruptures de stock de mai.</p>
"""

AUTO = """
<h2>Auto : ce qui compte vraiment, c'est la compatibilite</h2>

<p>Dans cette categorie, le rabais est presque secondaire. La question qui
determine si l'achat est reussi, c'est <strong>est-ce que la piece va sur mon
vehicule</strong>. Une piece a 60 % de rabais qui ne s'installe pas coute le
prix du retour et le temps perdu.</p>

<p>Amazon offre un outil de verification par vehicule — annee, marque, modele,
version. Utilise-le systematiquement, et quand un doute persiste, valide le
numero de piece d'origine plutot que de te fier au tableau de compatibilite :
les fiches de vendeurs tiers contiennent regulierement des erreurs.</p>

<h3>Le calendrier quebecois</h3>

<p>C'est ici que la saison joue le plus fort au Quebec. Les <strong>tapis
d'hiver, grattoirs, balais a neige, liquide lave-glace et survolteurs</strong>
montent en prix des les premieres neiges. Achete-les en
<strong>septembre</strong>, quand personne n'y pense encore — l'ecart avec
decembre est significatif, et le stock est complet.</p>

<p>Meme logique a l'inverse pour les <strong>essuie-glaces d'hiver</strong>
(a acheter en octobre, a remplacer chaque annee) et pour tout ce qui touche la
<strong>climatisation et l'entretien d'ete</strong> (a acheter en fevrier ou
mars).</p>

<h3>Trois verifications qui evitent un retour</h3>

<ul>
  <li><strong>La batterie.</strong> Le groupe de batterie (le code du format)
  doit correspondre exactement. Verifie aussi la date de fabrication : une
  batterie qui a passe un an sur une tablette a deja perdu de la capacite.</li>
  <li><strong>Les huiles et fluides.</strong> La specification exigee par le
  fabricant du vehicule figure dans le manuel du proprietaire. Ce n'est pas
  interchangeable, et l'economie ne vaut jamais le risque.</li>
  <li><strong>Les pneus et le froid.</strong> Rappel utile : au Quebec, les
  pneus d'hiver sont obligatoires du 1er decembre au 15 mars. Les meilleures
  aubaines tombent en <strong>septembre et octobre</strong>, avant la ruee.</li>
</ul>

<p>Pour les accessoires purement pratiques — supports a telephone,
organisateurs de coffre, chargeurs, housses —, les rabais depassent souvent
50 % et le risque est faible. C'est la partie de la categorie ou on peut
acheter sur un coup de tete sans le regretter.</p>
"""
AUTRES = """
<h2>Ce qu'on trouve dans « Autres aubaines »</h2>

<p>Cette page rassemble les rabais qui n'entrent proprement dans aucune des
sept autres categories : produits de beaute et de soins personnels, articles
pour animaux, fournitures de bureau et de papeterie, produits de sante,
epicerie non perissable, livres, articles saisonniers et tout ce qui, un matin
donne, n'a pas de case evidente.</p>

<p>C'est, en pratique, la categorie la plus interessante a parcourir — et la
moins consultee. Comme personne ne vient ici en cherchant quelque chose de
precis, les articles y restent en rabais plus longtemps qu'ailleurs.</p>

<h3>Comment la parcourir efficacement</h3>

<p>Deux approches fonctionnent bien. La premiere : <strong>y jeter un oeil une
fois par semaine sans idee precise</strong>, en visant les articles du quotidien
qu'on rachete de toute facon — savon, dentifrice, papier, nourriture pour
animaux, piles. Un rabais de 40 % sur un produit qu'on va consommer n'est
jamais un achat impulsif : c'est du stock a bon prix.</p>

<p>La seconde : <strong>utiliser la recherche de ton navigateur</strong>
(Ctrl+F, ou Cmd+F sur Mac) directement dans la page pour trouver un mot precis
parmi les aubaines du jour. C'est plus rapide que de faire defiler.</p>

<h3>Deux mises en garde propres a cette categorie</h3>

<ul>
  <li><strong>Les dates de peremption.</strong> Sur les produits de beaute, les
  supplements et l'epicerie, un tres gros rabais signale parfois une date qui
  approche. Ce n'est pas un probleme si tu comptes l'utiliser rapidement — c'en
  est un si tu achetes en quantite.</li>
  <li><strong>Les produits de sante et les supplements.</strong> Verifie la
  presence d'un numero de produit naturel (NPN) ou d'un DIN, qui indique une
  homologation par Sante Canada. Son absence sur un produit importe merite au
  minimum une hesitation.</li>
</ul>

<p>Si tu constates qu'un article est mal classe — ca arrive, le classement est
automatique —, ecris-nous et la correction est faite au prochain cycle de mise
a jour.</p>
"""

JEUX_VIDEO = """
<h2>Jeux vidéo : la patience se paye plus qu'ailleurs</h2>

<p>Aucune autre catégorie ne perd de la valeur aussi vite ni aussi
régulièrement. Un jeu à gros budget sort à 89,99 $, descend à 60 $ après deux
ou trois mois, à 40 $ vers six mois, et finit sous 30 $ dans l'année. Ce n'est
pas du hasard, c'est un calendrier. Si tu n'as pas besoin d'y jouer le jour de
la sortie, attendre douze semaines te fait économiser le tiers du prix.</p>

<p>Repères utiles : sur un jeu récent, <strong>25 % est un bon rabais</strong>
et 40 % est excellent. Sur les jeux plus anciens, les liquidations dépassent
souvent 70 %, mais vérifie que ce n'est pas une édition tronquée.</p>

<h3>Ce qui coûte cher à ignorer</h3>

<ul>
  <li><strong>La plateforme.</strong> Ça paraît évident, et c'est pourtant
  l'erreur la plus fréquente : les boîtiers se ressemblent beaucoup d'une
  console à l'autre.</li>
  <li><strong>Édition standard ou spéciale.</strong> Une « édition deluxe » à
  moitié prix peut coûter plus cher que la standard au prix courant.</li>
  <li><strong>La langue.</strong> Piège québécois classique : la version vendue
  sur Amazon.ca est souvent anglaise seulement. Cherche « français » ou
  « bilingue » dans le titre.</li>
  <li><strong>Le code de téléchargement.</strong> Certaines offres à bas prix
  sont un code, pas un disque — impossible à revendre ou à prêter.</li>
</ul>

<h3>Les accessoires, c'est l'inverse</h3>

<p>Manettes, casques et cartes mémoire se démarquent moins souvent mais plus
franchement. Une manette officielle à 30 % de rabais est une vraie affaire :
elle ne perdra pas de valeur, contrairement à un jeu.</p>

<h3>Quand acheter</h3>

<p>Le <strong>Vendredi fou</strong> reste le sommet, mais les soldes d'été des
boutiques en ligne, en <strong>juillet</strong>, sont souvent aussi
intéressantes et beaucoup moins courues.</p>
"""

EPICERIE = """
<h2>Épicerie : le prix au 100 g, et rien d'autre</h2>

<p>C'est la catégorie où le pourcentage de rabais ment le plus. Un format
géant à 30 % de rabais peut rester plus cher au gramme qu'un format courant au
prix régulier à l'épicerie du coin. <strong>Le seul chiffre qui compte, c'est
le prix ramené à l'unité</strong> — au 100 g, au litre, à la portion. Fais le
calcul, il prend dix secondes et il renverse souvent la décision.</p>

<p>Ce qui vaut vraiment la peine sur Amazon : le <strong>café</strong>, les
<strong>thés et infusions</strong>, les <strong>noix et fruits séchés</strong>,
les <strong>barres et collations en caisse</strong>, les <strong>épices</strong>
et les produits d'importation qu'on ne trouve pas en épicerie. Ce qui vaut
rarement la peine : les conserves, les pâtes et tout ce qui est lourd et
banal — le transport annule l'économie.</p>

<h3>Trois vérifications avant de cliquer</h3>

<ul>
  <li><strong>La date de péremption.</strong> Un très gros rabais sur de
  l'alimentaire signale souvent une date qui approche. Parfait si tu consommes
  vite, mauvais si tu achètes en caisse de vingt-quatre.</li>
  <li><strong>La quantité réelle.</strong> « Paquet de 6 » veut parfois dire six
  boîtes, parfois six unités dans une boîte. Le titre complet le dit.</li>
  <li><strong>L'entreposage.</strong> Le chocolat, les huiles et les produits
  fondants voyagent mal l'été. Commande-les hors canicule.</li>
</ul>

<h3>Le réflexe qui fait économiser</h3>

<p>Vise les produits <strong>que tu rachètes de toute façon</strong>. Un rabais
de 40 % sur ton café habituel n'est jamais un achat impulsif : c'est du stock à
bon prix. Un rabais de 40 % sur une denrée que tu n'as jamais essayée, c'est
souvent une dépense de plus.</p>
"""

BEAUTE = """
<h2>Beauté : vérifie le vendeur avant le prix</h2>

<p>C'est la catégorie où la contrefaçon est la plus répandue sur les places de
marché. Parfums, crèmes de marque et soins capillaires haut de gamme sont
copiés massivement, et un prix anormalement bas est le premier signal. Avant de
regarder le rabais, regarde <strong>qui vend et qui expédie</strong> : privilégie
« vendu et expédié par Amazon » ou le vendeur officiel de la marque.</p>

<p>Pour situer un rabais : les <strong>parfums</strong> descendent couramment de
30 à 50 % parce que leur marge est énorme, donc sous 30 % ce n'est pas une
aubaine. Les <strong>soins et cosmétiques de pharmacie</strong> bougent moins,
autour de 20 à 25 %, et c'est déjà bien. Les <strong>appareils</strong> — fers,
séchoirs, tondeuses — suivent la logique de l'électronique, avec des pointes au
Vendredi fou.</p>

<h3>Ce qu'il faut regarder</h3>

<ul>
  <li><strong>Le format.</strong> Un parfum à 40 $ peut être un 30 ml ou un
  100 ml. Le prix au millilitre change tout.</li>
  <li><strong>La date de péremption et le symbole PAO</strong> — le petit pot
  ouvert avec « 12M » ou « 24M » indique la durée après ouverture. Une crème
  achetée en trois exemplaires peut périmer avant d'être utilisée.</li>
  <li><strong>La teinte.</strong> Les couleurs sur écran ne sont pas fiables.
  Pour un fond de teint, achète la teinte que tu connais déjà.</li>
  <li><strong>L'emballage d'origine.</strong> Un produit « sans boîte » est
  parfois un échantillon professionnel non destiné à la revente.</li>
</ul>

<h3>Quand acheter</h3>

<p>Les <strong>coffrets des fêtes</strong>, mis en marché en novembre, sont
liquidés en <strong>janvier</strong> à 50 % et plus — et ils contiennent souvent
les mêmes produits que ceux vendus à l'unité le reste de l'année. C'est la
meilleure fenêtre de l'année dans cette catégorie.</p>
"""

SANTE_SOINS = """
<h2>Santé et soins : l'homologation avant le rabais</h2>

<p>Dans cette catégorie, la première question n'est pas le prix mais la
conformité. Au Canada, un produit de santé légitime porte un
<strong>numéro DIN, NPN ou NHP</strong> attribué par Santé Canada. Ce numéro
figure sur l'emballage et souvent dans la fiche. Son absence sur un supplément
ou un produit importé mérite au minimum une hésitation : les règles canadiennes
sur les doses et les allégations sont plus strictes qu'ailleurs, et un produit
conçu pour un autre marché peut ne pas les respecter.</p>

<p>Ce qui se démarque bien : les <strong>produits du quotidien</strong> —
papier, savon, dentifrice, pansements, lingettes — avec des rabais de 25 à 40 %
en format familial. Les <strong>appareils</strong> — tensiomètres, thermomètres,
balances, coussins chauffants — suivent la logique de l'électronique.</p>

<h3>À vérifier</h3>

<ul>
  <li><strong>La date de péremption</strong>, surtout sur les suppléments
  vendus en gros format. Un rabais de 50 % sur trois cents comprimés qui
  périment dans quatre mois n'en est pas un.</li>
  <li><strong>Le dosage.</strong> Deux boîtes du même produit peuvent contenir
  des concentrations très différentes. Compare au comprimé, pas à la boîte.</li>
  <li><strong>Le vendeur</strong>, comme en beauté : les suppléments sont
  massivement contrefaits.</li>
</ul>

<div class="avis">
<p><strong>Une évidence qui mérite d'être écrite :</strong> rien ici n'est un
conseil médical. Pour un supplément, un appareil de mesure ou tout produit lié
à une condition de santé, parles-en à ton pharmacien ou à ton médecin. Un bon
prix sur le mauvais produit reste un mauvais achat.</p>
</div>

<h3>Quand acheter</h3>

<p><strong>Janvier</strong> est le mois fort : résolutions obligent, les marques
poussent les vitamines, les appareils de mesure et le matériel d'exercice. Les
articles saisonniers — écrans solaires en septembre, humidificateurs en avril —
se liquident à contretemps, comme partout.</p>
"""

ANIMALERIE = """
<h2>Animalerie : la nourriture d'abord, le reste ensuite</h2>

<p>C'est la catégorie où l'achat récurrent domine tout. La nourriture représente
l'essentiel du budget d'un animal, et c'est là que les rabais comptent
vraiment. Un sac de 15 kg à 30 % de rabais, sur un aliment que ton chien mange
déjà, vaut mieux que dix jouets en solde.</p>

<p>Attention au calcul, comme en épicerie : <strong>compare le prix au
kilo</strong>, pas le prix du sac. Les formats géants ne sont pas
systématiquement plus avantageux, surtout en promotion sur les petits formats.</p>

<h3>Ce qu'il faut savoir</h3>

<ul>
  <li><strong>Ne change pas d'alimentation sur un coup de rabais.</strong> Un
  changement brusque de nourriture cause des troubles digestifs. Si tu changes,
  fais-le progressivement sur une semaine — et achète d'abord un petit format
  pour tester.</li>
  <li><strong>La date de péremption et l'entreposage.</strong> Les croquettes
  rancissent. Un sac de 20 kg pour un petit chien peut se dégrader avant la fin.</li>
  <li><strong>La taille du harnais ou du manteau.</strong> Les tailles varient
  énormément d'une marque à l'autre : fie-toi au tour de poitrail en
  centimètres, jamais au « M ».</li>
  <li><strong>Les jouets à petit prix.</strong> Méfie-toi des pièces qui se
  détachent sur les marques inconnues — un jouet avalé coûte une visite chez le
  vétérinaire.</li>
</ul>

<h3>Ce qui se démarque le plus</h3>

<p>Les <strong>litières</strong>, les <strong>gâteries</strong> et les
<strong>accessoires</strong> descendent facilement de 30 à 50 %. Les
<strong>fontaines, brosses et coupe-griffes</strong> suivent. Les grandes marques
de nourriture bougent moins, autour de 15 à 25 % — ce qui, sur un achat mensuel,
représente quand même la plus grosse économie annuelle de la catégorie.</p>
"""

BEBE = """
<h2>Bébé : la sécurité ne se magasine pas au rabais</h2>

<p>Une règle avant toutes les autres. Pour un <strong>siège d'auto</strong>, au
Québec, l'article doit porter l'<strong>autocollant de conformité de Transports
Canada (CMVSS)</strong>. Un siège acheté aux États-Unis ou importé sans cette
marque est illégal ici, même s'il est neuf et moins cher. Vérifie aussi la
<strong>date d'expiration</strong> — oui, un siège d'auto expire — et n'achète
jamais un siège d'occasion dont tu ne connais pas l'histoire.</p>

<p>Même logique pour les <strong>lits, parcs et porte-bébés</strong> : cherche la
conformité aux normes canadiennes plutôt que le meilleur pourcentage.</p>

<h3>Où sont les vraies économies</h3>

<p>Sur les <strong>consommables</strong>, et elles sont considérables. Couches,
lingettes, préparation et purées représentent une dépense mensuelle lourde et
prévisible : un rabais de 25 % sur une caisse de couches vaut plus, sur une
année, que n'importe quelle aubaine sur un article durable. Vise le prix
<strong>à la couche</strong>, pas au paquet.</p>

<ul>
  <li><strong>Les tailles.</strong> Un bébé change de taille vite. Acheter six
  mois de couches en taille 2 est une fausse économie.</li>
  <li><strong>Les vêtements.</strong> Achète une saison d'avance et une taille
  au-dessus : les liquidations de fin de saison sont à 60-70 %, et l'enfant
  aura grandi juste à temps.</li>
  <li><strong>Le matériel encombrant.</strong> Poussettes, chaises hautes et
  parcs se démarquent surtout au Vendredi fou et en janvier.</li>
</ul>

<h3>Quand acheter</h3>

<p><strong>Janvier</strong> et le <strong>Vendredi fou</strong> pour le matériel
durable. Pour les consommables, il n'y a pas de saison : surveille simplement le
prix à l'unité et fais des provisions quand il descend.</p>
"""

PRODUITS_BUREAU = """
<h2>Bureau et fournitures scolaires : tout se joue en août</h2>

<p>Cette catégorie a un calendrier plus marqué que n'importe quelle autre au
Québec. De la <strong>mi-juillet à la mi-septembre</strong>, la rentrée fait
descendre les prix des cahiers, crayons, sacs à dos, calculatrices et
cartables à des niveaux qu'on ne revoit pas de l'année. Un rabais de 50 % sur
des fournitures en août est courant ; le même article coûtera plein prix en
novembre.</p>

<p>Le reste de l'année, ce qui bouge vraiment : les <strong>cartouches
d'encre</strong>, les <strong>ramettes de papier</strong> en caisse, les
<strong>accessoires de poste de travail</strong> — supports d'écran, tapis,
lampes, repose-pieds — et le <strong>rangement</strong>.</p>

<h3>Le piège de l'encre</h3>

<p>C'est le classique de la catégorie. Vérifie que la cartouche correspond
<strong>exactement</strong> au numéro de modèle de ton imprimante : les
fabricants multiplient les références presque identiques. Et compare le prix
<strong>à la page imprimée</strong> plutôt qu'à la cartouche — une cartouche
« haut rendement » plus chère revient souvent moins cher à l'usage. Les
cartouches compatibles de tiers coûtent une fraction du prix; certaines
imprimantes récentes les refusent par mise à jour logicielle, à vérifier avant
d'acheter en lot.</p>

<h3>Deux autres vérifications</h3>

<ul>
  <li><strong>La quantité.</strong> « Paquet de 12 » ou « boîte de 12 paquets » :
  l'écart est énorme et le prix affiché ne le dit pas toujours.</li>
  <li><strong>La langue du clavier ou des étiquettes</strong> sur le matériel
  informatique et les agendas — la version canadienne-française n'est pas
  toujours celle qui est en solde.</li>
</ul>
"""

TERRASSE_JARDIN = """
<h2>Terrasse et jardin : acheter en septembre ce qu'on utilisera en juin</h2>

<p>Au Québec, cette catégorie a la saisonnalité la plus brutale de tout le
catalogue. Le même barbecue, la même tondeuse, le même ensemble de patio
coûtent le double en mai et se liquident en septembre. <strong>Les meilleures
aubaines de l'année tombent de la fin août à la mi-octobre</strong>, quand les
détaillants vident leurs entrepôts avant l'hiver, avec des rabais de 40 à 60 %
sur du matériel neuf.</p>

<p>L'inverse est vrai aussi : les <strong>souffleuses, pelles et sels de
déglaçage</strong> se paient le plus cher à la première neige et le moins cher
en <strong>mars et avril</strong>.</p>

<h3>Ce qui se démarque, et de combien</h3>

<p>Le <strong>mobilier de patio</strong> descend le plus fort — 50 % et plus en
fin de saison. Les <strong>outils de jardin à main</strong> et les
<strong>accessoires d'arrosage</strong> tournent autour de 30 à 40 %. Les
<strong>barbecues</strong> et les <strong>tondeuses</strong> bougent moins en
pourcentage, mais l'économie en dollars est la plus importante de la catégorie.</p>

<h3>À vérifier avant de commander</h3>

<ul>
  <li><strong>Le poids et les frais de livraison.</strong> C'est la catégorie où
  un rabais s'évapore le plus vite en frais de transport. Un article lourd
  vendu par un tiers peut coûter plus cher rendu chez toi.</li>
  <li><strong>La résistance au gel.</strong> Beaucoup de mobilier et de pots
  conçus pour des climats doux se fissurent à notre premier hiver. Cherche
  « résistant au gel » ou un matériau qui le supporte.</li>
  <li><strong>L'assemblage.</strong> Les grandes structures arrivent en pièces
  détachées; vérifie les commentaires sur la qualité de la notice.</li>
  <li><strong>Les plantes et semences.</strong> Elles voyagent mal l'été et
  gèlent en hiver. Commande au printemps ou achète local.</li>
</ul>
"""

# ---------------------------------------------------------------------------

INTROS = {
    "electronique": ELECTRONIQUE.strip(),
    "maison-cuisine": MAISON_CUISINE.strip(),
    "mode": MODE.strip(),
    "jouets-jeux": JOUETS_JEUX.strip(),
    "sports-plein-air": SPORTS_PLEIN_AIR.strip(),
    "outils-bricolage": OUTILS_BRICOLAGE.strip(),
    "auto": AUTO.strip(),
    "jeux-video": JEUX_VIDEO.strip(),
    "epicerie": EPICERIE.strip(),
    "beaute": BEAUTE.strip(),
    "sante-soins": SANTE_SOINS.strip(),
    "animalerie": ANIMALERIE.strip(),
    "bebe": BEBE.strip(),
    "produits-bureau": PRODUITS_BUREAU.strip(),
    "terrasse-jardin": TERRASSE_JARDIN.strip(),
    "autres-aubaines": AUTRES.strip(),
}


if __name__ == "__main__":
    import re

    total = 0
    for slug, txt in INTROS.items():
        mots = len(re.sub(r"<[^>]+>", " ", txt).split())
        total += mots
        print(f"{slug:22} {mots:6} mots")
    print("-" * 32)
    print(f"{'TOTAL':22} {total:6} mots")
