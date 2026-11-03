# Frontend restant - Machinati

## Objectif

Construire un seul site Machinati, avec une navigation et des vues differentes selon le role : client, cooperative ou equipe Machinati. Il ne faut pas creer un site distinct pour chaque role.

Ce document concerne uniquement les maquettes frontend. Les API, les integrations et le stockage reel sont hors perimetre. Les annonces, demandes et donnees IoT sont fictives; aucune location reelle n'est creee.

Machinati coordonne la location entre le client et la cooperative. Le site ne doit pas encourager le client a contacter directement un autre agriculteur.

# Machinati - Etat du prototype frontend

## Organisation des pages

Le frontend utilise `index.html` comme entree Vite et shell de navigation React. Le shell relie les vues suivantes :

- `public/catalogue.html` : catalogue client de demonstration.
- `cooperative.html` : espace cooperative de demonstration.
- `equipe-machinati.html` : espace operations de demonstration.
- Vue `Demandes` : tableau de bord React connecte aux endpoints de demandes et de materiel du backend.

Les vues HTML restent accessibles directement et leurs donnees de demonstration ne sont pas protegees par role. La navigation ne constitue pas un controle d'acces securise.

## Espace client - `public/catalogue.html`

- Consulter et filtrer un catalogue de machines de demonstration.
- Voir les caracteristiques, la region, le tarif et la cooperative partenaire.
- Preparer une demande de location avec une estimation indicative.
- Continuer une prise de contact avec Machinati via WhatsApp.
- Voir un apercu des donnees de suivi IoT.

Les annonces sont fictives. Une demande ne cree pas de location reelle.

## Espace cooperative - `cooperative.html`

- Voir l'etat de verification et les indicateurs principaux.
- Traiter les demandes transmises par Machinati : accepter, refuser ou proposer d'autres dates.
- Consulter le materiel, son tarif et son etat; ajouter une machine de demonstration.
- Consulter les prochaines remises et les retours.
- Voir le statut du boitier IoT, son utilisation et une alerte d'entretien.

## Espace operations - `equipe-machinati.html`

- Consulter les indicateurs et graphiques des demandes par statut et par jour.
- Gerer une file de 36 demandes fictives avec recherche, filtres par statut, region, machine et date, et tri par priorite ou date.
- Parcourir les resultats par pages de 10, 25 ou 50 lignes et ouvrir le detail d'une demande.
- Attribuer une cooperative, confirmer les dates, faire avancer un statut ou signaler un incident.
- Verifier une cooperative et moderer une annonce.
- Consulter l'etat IoT et les alertes de boitier.

## Limites du prototype

- Les donnees, indicateurs et mesures IoT des pages HTML sont fictifs.
- La vue React `Demandes` lit les demandes et le materiel depuis le backend et permet d'approuver ou refuser une demande; l'API ne dispose toutefois pas d'authentification.
- Les actions sont locales a la page et ne sont pas enregistrees apres rechargement.
- Il n'y a pas d'API, de stockage, de compte utilisateur ni de verification de role.
- La separation des fichiers HTML ne protege pas l'acces : chaque page peut etre ouverte directement.
- Les demandes WhatsApp sont preparees pour la demonstration; aucune location n'est confirmee par le site.

## Travail restant avant une mise en production

- Ajouter une authentification et des autorisations reelles pour chaque role.
- Connecter les pages aux API et enregistrer les demandes, machines et changements de statut.
- Remplacer les donnees fictives par les donnees reelles et traiter les erreurs, chargements et listes vides.
- Connecter les mesures IoT et preciser les donnees visibles par role.
- Tester l'accessibilite, le responsive et les parcours complets avec des donnees reelles.
## Les 2 autres espaces du site


### Cooperative : gerer le materiel et les demandes

- Presenter la cooperative et son etat de verification.
- Ajouter et modifier les machines (photos, categorie, caracteristiques, region, tarif et disponibilites), puis consulter leur etat : disponible, louee, en maintenance ou suspendue.
- Traiter les demandes transmises par Machinati : consulter le detail, accepter, refuser ou proposer d'autres dates.
- Consulter le calendrier, les remises et retours, ainsi que l'etat du materiel.
- Suivre l'utilisation et les alertes IoT des machines de la cooperative, avec des filtres par machine et par periode.

### Equipe Machinati : coordonner les locations

- Suivre les demandes, locations en cours, retards, incidents et cooperatives a verifier.
- Rechercher et trier les demandes par statut, region, machine, date ou priorite; consulter le detail, les notes et l'historique.
- Attribuer une cooperative, confirmer les dates, mettre a jour le statut et signaler un incident.
- Verifier les cooperatives et moderer les annonces.
- Consulter les donnees IoT et les alertes utiles au suivi des locations.

## Regles communes

- Adapter la navigation et les informations affichees au role connecte, tout en gardant un seul site et une presentation coherente.
- Reutiliser les memes boutons, champs, tableaux, filtres, badges, cartes machine, modales et notifications.
- Prevoir les etats vide, chargement, succes, erreur et formulaire invalide; pour l'IoT, indiquer aussi si le boitier est hors ligne ou si des donnees manquent.
- Assurer un affichage mobile lisible, des contrastes suffisants, des commandes utilisables au clavier et des messages accessibles.
- Identifier clairement les donnees de demonstration et garder les informations coherentes entre les trois espaces.

## Ordre de realisation

1. Espace client : catalogue, fiche machine, demande et suivi.
2. Espace cooperative : materiel, demandes et calendrier.
3. Espace Machinati : coordination, verification et moderation.
4. Ajouter le suivi IoT dans les espaces concernes, puis harmoniser l'affichage mobile et les etats d'interface.

## Decisions a confirmer

- Quels statuts et indicateurs chaque role doit-il voir ?
- Quelles donnees IoT sont visibles pour chaque role ?
- Quelles informations doivent apparaitre sur les fiches machine ?
- Quelles langues faut-il proposer au lancement ?