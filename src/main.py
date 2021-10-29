from population import GeneratePopulation, CloseDB
from propagation import StartSimulation

#Programme principal

GeneratePopulation() #Génère la population et ajoute toutes les données dans la BDD
StartSimulation() #Démarre la simulation et affiche les résultats
CloseDB() #Ferme la connexion de BDD
