import random
from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as graph
from plotly.subplots import make_subplots

from constantes import *


def probabilite(base, multiplicateur):
    proba = base*multiplicateur
#    assert proba <= 1, f"Probabilité supérieure à 1 : {proba}"
    if proba > 1:
        pass
    return proba >= random.random()


@dataclass
class Strategie:
    pass


@dataclass
class SituationInitiale:
    nombre_infectes: int = 16
    nombre_hospitalises: int = 4


@dataclass
class Parametres:
    simulation_duree: int = 300

    infection_duree: tuple[float, float] = (7, 1.5)
    hopital_duree: tuple[float, float] = (40, 1.5)

    infection_proba: float = 4.1e-4
    hopital_proba: float = 0.0442
    deces_proba: float = 0.2

    multiplicateur_distance: float = 0.5


class Simulation:
    def __init__(self, population, strategie, situation_init, parametres):
        self.population = population
        self.strategie = strategie
        self.init = situation_init
        self.param = parametres
        self.start_simulation()

    def start_simulation(self):
        liste_infectes = []
        liste_hospitalises = []
        liste_decedes = []

        # Jour 0 : mise en place de la situation initiale
        infectes_initialisation = random.choices(
            self.population.individus, k=self.init.nombre_infectes)
        infectes_durees = np.random.normal(
            *self.param.infection_duree, self.init.nombre_infectes)
        for id, individu in enumerate(infectes_initialisation):
            individu.infecter(round(infectes_durees[id]))
            liste_infectes.append(individu)

        hospitalises_initialisation = random.choices(
            self.population.individus, k=self.init.nombre_hospitalises)
        hospitalises_durees = np.random.normal(
            *self.param.hopital_duree, self.init.nombre_hospitalises)
        for id, individu in enumerate(hospitalises_initialisation):
            individu.hospitaliser(round(hospitalises_durees[id]))
            liste_hospitalises.append(individu)
            liste_infectes.append(
                individu) if individu not in liste_infectes else liste_infectes

        print("=== Début de la simulation ===")

        for jour in range(1, self.param.simulation_duree + 1):
            # Nouveau jour
            print(f"Simulation du jour {jour}")
            if len(liste_infectes) == 0:
                break

            # Traitement des individus qui ont un état à durée limitée
            for individu in liste_hospitalises:  # Individus hospitalisés
                if individu.infection_duree == 0:
                    # On décide si l'individu redevient sain, ou décède
                    if probabilite(self.param.deces_proba, individu.get_immunite(jour, DECES)):
                        individu.deces()
                        liste_decedes.append(individu)
                    else:
                        individu.guerir(jour)
                    liste_infectes.remove(individu)
                    liste_hospitalises.remove(individu)
                elif individu.infection_duree is not None:
                    individu.infection_duree -= 1

            for individu in liste_infectes:  # Individus infectés
                if individu.sante_duree == 0:
                    # On décide si l'individu redevient sain, ou est hospitalisé
                    if probabilite(self.param.hopital_proba, individu.get_immunite(jour, HOSPITALISATION)):
                        individu.hospitaliser(
                            round(np.random.normal(*self.param.hopital_duree)))
                        liste_hospitalises.append(individu)
                    else:
                        individu.guerir(jour)
                        liste_infectes.remove(individu)
                elif individu.sante_duree is not None:
                    individu.sante_duree -= 1
                    for (voisin_id, voisin_distance) in individu.voisins:
                        voisin = self.population.get_individu(voisin_id)
                        if voisin.sante == NEUTRE and probabilite(self.param.infection_proba, voisin.get_immunite(jour, HOSPITALISATION)*self.param.multiplicateur_distance/max(voisin_distance, 0.31)):
                            voisin.infecter(
                                round(np.random.normal(*self.param.infection_duree)))
                            liste_infectes.append(voisin)

            print(
                f"\033[KRapport du jour {jour} : Infectés : {len(liste_infectes)}, Hospitalisés : {len(liste_hospitalises)}, Décédés : {len(liste_decedes)}")
        self.afficher_resultats()

    def afficher_resultats(self):
        figure = graph.Figure()
        figure.add_trace(graph.Scatter(
            x=self.population.population_position[:, 0], y=self.population.population_position[:, 1], mode='markers'))
        figure.show()
