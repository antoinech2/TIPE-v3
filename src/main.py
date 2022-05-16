""""Programme principal"""

#Modules internes

from population import Population, close_database
from propagation import *

#Programme principal

if __name__ == "__main__":
    # Définition des objets d'entrée
    population = Population(10000, 10, 1) #Génère la population et ajoute toutes les données dans la BDD
    strategie_reelle = Strategie(dates_vaccination=[
    (0, {"age" : 85, "comp" : "sup"}), (6, {"age" : 50, "emploi" : "santé", "comp" : "sup"}), (9, {"age" : 50, "emploi" : "médico-social", "comp" : "sup"}),
    (22, {"age" : 75, "comp" : "sup"}), (90, {"age" : 65, "comp" : "sup"}), (120, {"age" : 50, "comp" : "sup"}), (155, {"age" : 18, "comp" : "sup"}), (170, {"age" : 12, "comp" : "sup"})
    ])
    strategie_comparee = Strategie(dates_vaccination=[
    (0, {"age" : 25, "comp" : "inf"}), 
    (100, {"age" : 40, "comp" : "inf"}), (150, {"age" : 50, "comp" : "inf"}),
    (165, {"age" : 50, "emploi" : "santé", "comp" : "sup"}), 
    (185, {"age" : 50, "emploi" : "médico-social", "comp" : "sup"}),(195, {"age" : 60, "comp" : "inf"}), (210, {"age" : 85, "comp" : "inf"}), (300, {"age" : 85, "comp" : "sup"})
    ])
    init = SituationInitiale()
    param = Parametres(
        simulation_duree=500,infection_proba=0.013, deces_proba=0.001
    )

    # Démarrage la simulation avec les paramètres définis et affichage des résultats
    Simulation(population, strategie_reelle, init, param)
    #population = Population(10000, 10, 1)
    #Simulation(population, strategie_comparee, init, param)
    close_database() #Fermeture la connexion à la base de donnée
