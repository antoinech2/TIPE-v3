""""Programme principal"""

#Modules internes

from population import Population, ferme_bdd
from propagation import *

#Programme principal

if __name__ == "__main__":
    # Définition des objets d'entrée
    population = Population(10000, 10, 5, True) #Génère la population et ajoute toutes les données dans la BDD
    
    # Définition des stratégies
    strategie_reelle = Strategie(dates_vaccination=[
    (0, {"age" : 85, "comp" : "sup"}), (6, {"age" : 50, "emploi" : "santé", "comp" : "sup"}), (9, {"age" : 50, "emploi" : "médico-social", "comp" : "sup"}),
    (22, {"age" : 75, "comp" : "sup"}), (75, {"age" : 65, "comp" : "sup"}), (100, {"age" : 50, "comp" : "sup"}), (130, {"age" : 18, "comp" : "sup"}), (170, {"age" : 12, "comp" : "sup"})
    ])
    strategie_comparee = Strategie(dates_vaccination=[
    (0, {"age" : 25, "comp" : "inf"}), 
    (100, {"age" : 40, "comp" : "inf"}), (145, {"age" : 50, "comp" : "inf"}),
    (165, {"age" : 50, "emploi" : "santé", "comp" : "sup"}), 
    (175, {"age" : 50, "emploi" : "médico-social", "comp" : "sup"}),(183, {"age" : 60, "comp" : "inf"}), (200, {"age" : 85, "comp" : "inf"}), (300, {"age" : 85, "comp" : "sup"})
    ])
    
    # Situation initiale
    init = SituationInitiale(nombre_infectes = 16, nombre_hospitalises = 4)
    param = Parametres(simulation_duree=500,infection_proba=0.004, hopital_proba=0.0442, deces_proba=0.001)

    # Démarrage la simulation avec les paramètres définis et affichage des résultats
    Simulation(population, strategie_reelle, init, param, "Stratégie réelle")
    population = Population(10000, 10, 5, False)
    Simulation(population, strategie_comparee, init, param, "Stratégie comparée")
    ferme_bdd() #Fermeture la connexion à la base de donnée
