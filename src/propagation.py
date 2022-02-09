from constantes import *
from dataclasses import dataclass
import random
import numpy as np

def probabilite(base, multiplicateur):
    return base*multiplicateur <= random.random()

@dataclass
class Strategie:
    pass

@dataclass
class SituationInitiale:
    nombre_infectes : int = 1
    nombre_hospitalises : int = 1

@dataclass
class Parametres:
    simulation_duree : int = 300

    infection_duree : tuple[float, float] = (7, 1.5)
    hopital_duree : tuple[float, float] = (40, 1.5)

    hopital_proba = 0.001
    deces_proba = 7.8e-6

class Simulation:
    def __init__(self, population, strategie, situation_init, parametres):
        self.population = population
        self.strategie = strategie
        self.init = situation_init
        self.param = parametres

    def start_simulation(self):
        liste_infectes = []
        liste_hospitalises = []

        # Jour 0 : mise en place de la situation initiale
        infectes_initialisation = random.choices(self.population.individus, k=self.init.nombre_infectes)
        infectes_durees = np.random.normal(*self.param.infection_duree, self.init.nombre_infectes)
        for id, individu in enumerate(infectes_initialisation):
            individu.infecter(round(infectes_durees[id]))
            liste_infectes.append(individu)

        hospitalises_initialisation = random.choices(self.population.individus, k=self.init.nombre_hospitalises)
        hospitalises_durees = np.random.normal(*self.param.hopital_duree, self.init.nombre_hospitalises)
        for id, individu in enumerate(hospitalises_initialisation):
            individu.infecter(round(hospitalises_durees[id]))
            liste_hospitalises.append(individu)

        for jour in range(1, self.param.simulation_duree + 1):
            # Nouveau jour
            print(f"Simulation du jour {jour}")

            # Traitement des individus qui ont un état à durée limitée
            for individu in liste_hospitalises: #Individus hospitalisés
                if individu.infection_duree == 0:
                    # On décide si l'individu redevient sain, ou décède
                    if probabilite(self.param.deces_proba, individu.get_immunite(jour, DECES)):
                        individu.deces()
                    else:
                        individu.guerir(jour)
                    liste_infectes.remove(individu)
                    liste_hospitalises.remove(individu)
                elif individu.infection_duree is not None:
                    individu.infection_duree -= 1

            for individu in liste_infectes: #Individus infectés
                if individu.sante_duree == 0:
                    # On décide si l'individu redevient sain, ou est hospitalisé
                    if probabilite(self.param.hopital_proba, individu.get_immunite(jour, HOSPITALISATION)):
                        individu.hospitaliser(np.random.normal(*self.param.hopital_duree))
                        liste_hospitalises.append(individu)
                    else:
                        individu.guerir(jour)
                        liste_infectes.remove(individu)
                elif individu.sante_duree is not None:
                    individu.sante_duree -= 1
