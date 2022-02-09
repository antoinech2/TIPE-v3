from population import Population
from propagation import StartSimulation

#Programme principal

population = Population(1000, 2, 1) #Génère la population et ajoute toutes les données dans la BDD
#StartSimulation() #Démarre la simulation et affiche les résultats
CloseDB() #Ferme la connexion de BDD
