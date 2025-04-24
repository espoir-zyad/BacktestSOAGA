1. Classe Asset
•	Rôle : Charger les données historiques depuis un fichier Excel et calculer les performances des titres.
Fonctions clés :
•	Charger les données historiques depuis un fichier Excel : Les données contiennent des colonnes pour la date, les titres (avec leurs codes ISIN), et un benchmark "BRMV C" à ignorer dans les calculs.
•	Calculer la performance des titres sur les 6 derniers mois avant une date donnée : À l'exception des titres "ORAC" et "SNTS".
•	Retourner le Top 18 des titres (hors "ORAC" et "SNTS") selon la performance sur 6 mois, triés par performance décroissante.
•	Retourner les cours actuels des titres au jour donné.
________________________________________
2. Classe Stratégie
•	Paramètres d'initialisation :
o	Cash initial : Montant d'argent disponible au début.
o	Valeur Liquidative initiale : La valeur totale du portefeuille au début.
o	Date de début et date de fin du backtest : Plage de dates sur laquelle le backtest sera effectué.
o	Dictionnaire Portfolio : Structure contenant les informations du portefeuille pour chaque jour du backtest ayant pour clé : Date : Liste de dates correspondant à chaque jour du backtest. Etat : Liste de DataFrames représentant l'état du portefeuille (titres, quantités, valorisation, pondération) à chaque date. Valeur Liquidative : Liste des valeurs liquidatives à chaque date. Valorisation Totale : Liste des valorisations totales du portefeuille à chaque date. Transactions : Liste de DataFrames des transactions (achats/ventes) effectuées chaque jour.
________________________________________
3. Procédure de gestion du portefeuille (Jour 1)
Initialisation :
1.	Sélection des titres :
o	Les 2 titres fixes "ORAC" et "SNTS" sont ajoutés avec une pondération de 20% chacun.
o	Les 18 titres ayant les meilleures performances sur les 6 derniers mois (excluant ORAC et SNTS) sont sélectionnés.
o	Ces 18 titres reçoivent une pondération égale de 3.33% chacun, soit 60% du portefeuille répartis entre les 18 titres.
2.	Calcul de la quantité :
o	La quantité de chaque titre est calculée en fonction de sa valorisation et de son prix actuel :
Quantiteˊ=ValorisationCours actuel du titre\text{Quantité} = \frac{\text{Valorisation}}{\text{Cours actuel du titre}}Quantiteˊ=Cours actuel du titreValorisation 
3.	Mise à jour des transactions :
o	Enregistrer toutes les acquisitions d'actions pour le premier jour.
o	Type de transaction : Acquisition pour les titres achetés.
________________________________________
4. Procédure de gestion du portefeuille (Jour suivant)
Mise à jour du portefeuille :
1.	Récupérer l'état du portefeuille du jour précédent.
2.	Mise à jour de la date : Ajouter la date du jour suivant.
3.	Mise à jour des cours : Récupérer les cours de marché des titres pour la nouvelle date.
4.	Recalcul des valorisations : Pour chaque titre, la valorisation est recalculée :
Valorisation=Quantiteˊ×Cours\text{Valorisation} = \text{Quantité} \times \text{Cours}Valorisation=Quantiteˊ×Cours 
5.	Recalcul des pondérations : La pondération est recalculée en fonction de la nouvelle valorisation :
Pondeˊration=ValorisationSomme totale des valorisations\text{Pondération} = \frac{\text{Valorisation}}{\text{Somme totale des valorisations}}Pondeˊration=Somme totale des valorisationsValorisation 
Rééquilibrage de ORAC et SNTS :
•	Si l'un des deux titres (ORAC ou SNTS) dépasse 20% de la valorisation totale, il doit être rééquilibré à 20%.
•	Répartition :
o	Valorisation de ORAC = 20% de la valorisation totale.
o	Valorisation de SNTS = 20% de la valorisation totale.
Mise à jour des quantités :
•	Recalculer la quantité de chaque titre à partir de sa nouvelle valorisation et de son prix actuel :
Quantiteˊ=ValorisationCours du jour\text{Quantité} = \frac{\text{Valorisation}}{\text{Cours du jour}}Quantiteˊ=Cours du jourValorisation 
Sélection du Top 18 :
•	Sélectionner les 18 titres ayant les meilleures performances sur les 6 derniers mois, en excluant ORAC et SNTS.
•	Trier les titres par performance décroissante.
Mise à jour des titres du portefeuille :
•	Vérification des titres dans le portefeuille : Avant d'ajouter un titre, on vérifie s'il y a des titres dans le portefeuille qui ne sont pas dans le Top 18.
o	Si tous les titres sont dans le Top 18, on ne retire aucun titre et on réajuste uniquement leurs pondérations pour que chacun représente 3.33% de la valorisation totale du portefeuille.
o	Si des titres ne font pas partie du Top 18, on retire ces titres et on les remplace par des titres qui sont dans le Top 18, avec une pondération de 3.33% chacun.
Ajout et retrait des titres :
•	Ajout d'un titre : Lorsqu'un titre est ajouté, il est ajouté avec une valorisation de 3.33% de la valorisation totale du portefeuille.
•	Retrait d'un titre : Le titre retiré est celui qui n'est pas dans le Top 18.
o	Cela garantit que le portefeuille reste composé de 20 titres (2 titres fixes : ORAC et SNTS, et 18 autres titres du Top 18).
Calcul des transactions :
•	Vérifier les variations de quantité pour chaque titre :
o	Acquisition : Si un titre est ajouté au portefeuille.
o	Cession : Si un titre est retiré du portefeuille.
o	Ajustement : Si la quantité d’un titre est modifiée (augmentation ou diminution).
•	Pour chaque transaction, calculer la valorisation de la transaction :
Valorisation de la transaction=Variation de la quantiteˊ×Cours du titre\text{Valorisation de la transaction} = \text{Variation de la quantité} \times \text{Cours du titre}Valorisation de la transaction=Variation de la quantiteˊ×Cours du titre 
•	Enregistrer la transaction dans le DataFrame des transactions du jour.
________________________________________
5. Mise à jour des métriques du portefeuille :
•	Valeur Liquidative : La valeur liquidative du portefeuille est mise à jour chaque jour en fonction de la valorisation totale :
Valeur Liquidative (VL)=VL preˊceˊdente×(Valorisation Totale actuelleValorisation Totale preˊceˊdente)\text{Valeur Liquidative (VL)} = \text{VL précédente} \times \left( \frac{\text{Valorisation Totale actuelle}}{\text{Valorisation Totale précédente}} \right)Valeur Liquidative (VL)=VL preˊceˊdente×(Valorisation Totale preˊceˊdenteValorisation Totale actuelle) 
•	Valorisation Totale : La valorisation totale du portefeuille est recalculée chaque jour.
•	Transactions : Un DataFrame est mis à jour avec les détails des transactions effectuées chaque jour (achat/vente/ajustement).
________________________________________
6. Répétition du processus pour chaque jour du backtest :
Chaque jour, le processus décrit ci-dessus est répété avec les données de marché mises à jour, ce qui permet d'ajuster le portefeuille en fonction des nouvelles performances des titres et des conditions du marché.
________________________________________
7. Résultats finaux :
•	À la fin du backtest, le portefeuille contient 20 titres :
o	2 titres (ORAC et SNTS) pondérés à 20% chacun.
o	18 autres titres pondérés à 3.33% chacun.
•	Les transactions effectuées pendant le backtest sont disponibles.
•	La valeur liquidative et la valorisation totale du portefeuille sont à jour pour chaque jour du backtest.
Ce processus garantit que le portefeuille est régulièrement réajusté et optimisé en fonction des performances des titres sur la période de backtest, tout en s'assurant qu'il contient toujours 20 titres. Les titres non performants sont retirés et remplacés par des titres du Top 18, assurant ainsi une gestion dynamique du portefeuille.


A la fin, je veux une petite interface me permettant de voir l’historique du portefeuille pour chaque Date
