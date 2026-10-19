# U-Park — Cadrage (soutenance mensuelle 1)

Document de référence pour la soutenance d'octobre : diagnostic du besoin, personas, parcours, périmètre du MVP, organisation et risques. Le détail des fonctionnalités est dans le [backlog](backlog.md), les choix motivés dans le [journal de décisions](journal-de-decisions.md).

Les passages marqués **[à compléter]** dépendent de l'équipe (résultats du questionnaire, entretiens, noms).

## 1. Diagnostic du besoin

### Contexte

Le campus de Marne-la-Vallée (Cité Descartes) compte plusieurs parkings, d'environ 1 050 places au total d'après la page « Accès aux bâtiments » de l'université, avec des publics différents : certains parkings sont ouverts à tous, d'autres réservés aux personnels. Aucun outil ne permet aujourd'hui de savoir à l'avance s'il reste de la place, ni de réserver.

### Problèmes constatés (hypothèses à confirmer)

| Problème | Qui est touché | Conséquence |
|---|---|---|
| On ne sait pas s'il reste des places avant d'arriver | Étudiants, personnels | Temps perdu, retards en cours, stress |
| Saturation le matin, places vides l'après-midi | Tous | Capacité mal utilisée |
| Règles d'accès (zones personnels, PMR) peu visibles | Tous | Places réservées occupées à tort |
| Accueil des visiteurs organisé au cas par cas | Visiteurs, services d'accueil | Démarches longues, aucune garantie de place |
| Aucune donnée d'occupation | Administration | Décisions (travaux, événements) prises sans visibilité |

### Sources

| Source | État | Ce qu'on en retient |
|---|---|---|
| Cahier des charges | ✅ | Périmètre MVP, 4 profils, 4 critères d'acceptation |
| Échanges avec l'enseignant | ✅ | [à compléter : points clarifiés] |
| Données publiques de l'université | ✅ | Parkings réels et capacités (repris dans le jeu de démonstration) |
| Questionnaire en ligne | 🟡 | [à compléter : nombre de réponses, résultats ci-dessous] |
| Entretiens (3) | 🟡 | [à compléter] |

### Questionnaire

À diffuser (Google Forms ou équivalent) auprès des étudiants et personnels qui viennent en voiture, sans collecter de nom ni d'email (anonyme, conforme au RGPD).

1. Vous êtes : étudiant · personnel · intervenant extérieur
2. À quelle fréquence venez-vous en voiture ? jamais · moins d'une fois par semaine · 1 à 3 jours · 4 jours ou plus
3. À quelle heure arrivez-vous le plus souvent ? avant 8 h · 8 h – 9 h · 9 h – 10 h · après 10 h
4. Combien de temps mettez-vous en moyenne à trouver une place ? moins de 5 min · 5 à 10 min · 10 à 20 min · plus de 20 min
5. Avez-vous déjà été en retard ou renoncé à venir faute de place ? jamais · rarement · souvent
6. Quel parking utilisez-vous le plus ? (liste des parkings)
7. Réserveriez-vous une place la veille si c'était possible ? oui · peut-être · non
8. Annuleriez-vous votre réservation si vous ne venez pas ? oui, toujours · parfois · non
9. Avez-vous besoin d'une place PMR ? oui · non · ne souhaite pas répondre
10. Qu'est-ce qui vous ferait gagner le plus de temps ? (réponse libre)

Chaque résultat chiffré doit être relié à une fonctionnalité, par exemple :

| Résultat | Valeur | Fonctionnalité qui y répond |
|---|---|---|
| Temps moyen pour se garer | [à compléter] | R-02 disponibilités par créneau |
| Part ayant déjà renoncé ou été en retard | [à compléter] | R-03 réservation |
| Part prête à réserver la veille | [à compléter] | Validation du concept |
| Part qui annulerait | [à compléter] | R-04 annulation, T-02 no-show |
| Pic d'arrivée | [à compléter] | Simulateur (T-03), extension prévision (X-03) |

## 2. Personas

**Alice, 20 ans, étudiante en BUT.** Elle vient en voiture trois jours par semaine, à 35 min de route, avec des cours à 8 h.
- Besoin : savoir avant de partir s'il reste une place, et la réserver.
- Frustration : la saturation du matin, qui la met en retard.
- Ce qu'U-Park lui apporte : le choix d'un créneau, la réservation en un clic, l'annulation.

**Marc, 46 ans, gestionnaire de scolarité.** Il arrive chaque jour à 8 h et part à 17 h.
- Besoin : une place garantie dans la zone réservée aux personnels.
- Frustration : des places réservées occupées par d'autres.
- Ce qu'U-Park lui apporte : des zones réservées par rôle et la détection des no-show.

**Julie, 38 ans, ingénieure invitée en jury.** Elle vient une seule fois et ne connaît pas le campus.
- Besoin : demander une place pour une date précise et avoir vite une réponse.
- Frustration : des démarches d'accès longues et opaques.
- Ce qu'U-Park lui apporte : une demande en ligne, une place attribuée par l'administration et un suivi du statut.

**Sofia, 41 ans, responsable logistique.** Elle gère les parkings du campus.
- Besoin : fermer une zone pour des travaux, valider les visiteurs, suivre l'occupation.
- Frustration : aucune donnée pour décider.
- Ce qu'U-Park lui apporte : les blocages avec annulation automatique, le traitement des demandes et des incidents, le tableau de bord.

Ces personas sont **fictifs**. Ils seront ajustés après les entretiens. Les comptes de démonstration reprennent leurs prénoms pour faciliter la démo.

## 3. Parcours principaux

**Parcours 1 : l'étudiant réserve.** Choisir un jour et une plage horaire → voir les zones et les places libres → réserver une place → recevoir la confirmation → la retrouver dans « Mes réservations » → annuler si besoin.

**Parcours 2 : l'administrateur bloque une zone.** Choisir la zone → indiquer le motif et la période → les réservations concernées sont annulées → la zone n'offre plus de place sur la période, pour tous les usagers → le tableau de bord reflète les annulations.

**Parcours 3 : le visiteur demande une place.** Saisir la date, les horaires et le motif → l'administrateur valide (place choisie ou attribuée automatiquement) ou refuse avec un motif → le visiteur voit la réponse et sa réservation.

## 4. Périmètre

| Indispensable (MVP) | Souhaitable | Extension | Hors périmètre |
|---|---|---|---|
| Catalogue des parkings et zones ; réservation, annulation, historique ; rôles et règles d'accès ; blocage de zone et de place ; validation des visiteurs ; tableau de bord ; jeu de données sur au moins 3 profils | Incidents ; passage et no-show simulés ; journal des actions ; droits RGPD ; places PMR | QR code ; liste d'attente ; prévision de saturation ; carte interactive | Capteurs, barrières, caméras ; paiement ; données réelles ; SSO |

**Critères d'acceptation** (cahier des charges), tous couverts par des tests automatisés :
1. Un étudiant peut réserver une place libre, recevoir une confirmation et annuler sa réservation.
2. Un administrateur peut bloquer une zone et voir l'impact sur les disponibilités.
3. Le tableau de bord reflète correctement les réservations et annulations du jeu de données.
4. Les droits empêchent un utilisateur simple de modifier les règles de parking.

## 5. Organisation de l'équipe

| Rôle | Responsabilités | Membre |
|---|---|---|
| Chef de projet / Product owner | Planning, arbitrage du backlog, réunions, contact enseignant | [à compléter] |
| Référent fonctionnel et UX | Questionnaire, entretiens, personas, maquettes, tests utilisateurs | [à compléter] |
| Lead front-end | Interface web et mobile, intégration des maquettes, accessibilité | [à compléter] |
| Lead back-end / API | Modèle métier, API, règles de gestion, authentification | [à compléter] |
| Data / DevOps / qualité | Base de données, Docker, jeu de données, tests automatisés | [à compléter] |
| Documentation et validation | Rapports, comptes rendus, guide utilisateur, cahier de recette | [à compléter] |

**Fonctionnement :**
- une réunion interne par semaine, avec un compte rendu ;
- un ticket par story du backlog ;
- une branche et une pull request relue par un autre membre pour chaque changement ;
- les décisions sont notées dans le journal de décisions ;
- le chef de projet centralise les échanges avec l'enseignant (questions envoyées au moins 48 h avant la séance de suivi).

Chaque membre doit avoir une contribution visible dans Git, dans les livrables et lors des soutenances.

## 6. Risques

| Risque | Probabilité | Impact | Parade |
|---|---|---|---|
| Pas de données réelles de fréquentation | Certaine | Moyen | Simulateur de fréquentation crédible ; capacités réelles issues de sources publiques |
| Règles de priorité trop complexes | Moyenne | Élevé | Une règle = une zone réservée à des rôles ; PMR géré par type de place |
| Ambiguïté sur les droits | Moyenne | Élevé | Rôles documentés ; tests automatisés des refus d'accès |
| Contributions inégales dans l'équipe | Moyenne | Élevé | Rôles nominatifs, tâches attribuées chaque semaine, revue de code croisée |
| Peu de réponses au questionnaire | Moyenne | Moyen | Diffusion par plusieurs canaux (groupes de promo, Discord, affichage) ; entretiens en complément |
| Prototype construit avant la validation du besoin | Avérée | Moyen | Le présenter comme une preuve de concept ; ajuster après les tests de maquettes |

## 7. Demandes d'arbitrage à l'enseignant

1. Un visiteur doit-il créer un compte, ou un simple formulaire de demande suffit-il ?
2. Peut-on afficher les capacités réelles des parkings, issues du site de l'université ?
3. Une zone réservée à des rôles suffit-elle comme règle de priorité, ou faut-il une priorité du personnel sur les zones ouvertes ?
4. Quelle durée de conservation pour le journal des actions (proposition : 12 mois) ?

## 8. Planning jusqu'au 9 mars

| Date | Jalon | Livrables visés |
|---|---|---|
| Octobre | Soutenance mensuelle 1 | Ce document, backlog, rôles, démo du prototype |
| Novembre | Soutenance mensuelle 2 | Maquettes validées, tests rapides avec 3 à 5 utilisateurs, modèle de données, architecture |
| Décembre | Soutenance mensuelle 3 | Parcours intégré démontré, plan de tests, base de test isolée, CI |
| Janvier | Soutenance intermédiaire | POC évalué, rapport intermédiaire, planning réaliste |
| Février | Soutenance mensuelle 4 | Tests utilisateurs, corrections, stabilisation |
| 9 mars | Soutenance finale | Produit final, rapport complet, démonstration, bilan critique |
