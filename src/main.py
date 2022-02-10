from population import Population, close_database
from propagation import *

#Programme principal

population = Population(10000, 2, 1) #Génère la population et ajoute toutes les données dans la BDD
strategie = Strategie()
init = SituationInitiale()
param = Parametres()

Simulation(population, strategie, init, param) #Démarre la simulation et affiche les résultats
close_database() #Ferme la connexion de BDD
