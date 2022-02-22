""""Programme principal"""

#Modules internes

from population import Population, close_database
from propagation import *

#Programme principal

if __name__ == "__main__":
    # Définition des objets d'entrée
    population = Population(10000, 10, 1) #Génère la population et ajoute toutes les données dans la BDD
    strategie = Strategie()
    init = SituationInitiale()
    param = Parametres(
        simulation_duree=1000,infection_proba=0.0065, multiplicateur_distance=1, deces_proba=0.001
    )

    # Démarrage la simulation avec les paramètres définis et affichage des résultats
    Simulation(population, strategie, init, param)
    close_database() #Fermeture la connexion à la base de donnée
