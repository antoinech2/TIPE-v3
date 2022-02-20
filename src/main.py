from population import Population, close_database
from propagation import *

#Programme principal

population = Population(10000, 10, 1) #Génère la population et ajoute toutes les données dans la BDD
strategie = Strategie()
init = SituationInitiale()
param = Parametres(
    simulation_duree=1000,infection_proba=0.0065, multiplicateur_distance=1, deces_proba=0.001
)

Simulation(population, strategie, init, param) #Démarre la simulation et affiche les résultats
close_database() #Ferme la connexion de BDD
