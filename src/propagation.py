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
        #print(f"Probabilité dépassée : {proba}")
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
    hopital_duree: tuple[float, float] = (30, 1.5)

    infection_proba: float = 4.1e-4
    hopital_proba: float = 0.0442
    deces_proba: float = 0.2

    multiplicateur_distance: float = 0.5

    jour_debut_vaccination : int = 1
    taille_population_vaccination : int = 67000000


class Simulation:
    def __init__(self, population, strategie, situation_init, parametres):
        self.population = population
        self.strategie = strategie
        self.init = situation_init
        self.param = parametres

        self.stats = {
            "total_infectes": [self.init.nombre_infectes],
            "total_hospitalises": [self.init.nombre_hospitalises],
            "total_decedes": [0],
            "nouveaux_infectes": [0],
            "nouveaux_hospitalises": [0],
            "nouveaux_decedes": [0],
            "nouveaux_gueris": [0],
            "vaccines" : [0]
        }

        self.start_simulation()

    def start_simulation(self):
        liste_infectes = []
        liste_hospitalises = []
        liste_decedes = []
        liste_vaccines = []
        liste_non_vaccines = [individu for individu in self.population.individus if individu.age >= 12]

        # Jour 0 : mise en place de la situation initiale
        infectes_initialisation = random.sample(
            self.population.individus, self.init.nombre_infectes)
        infectes_durees = np.random.normal(
            *self.param.infection_duree, self.init.nombre_infectes)
        for id, individu in enumerate(infectes_initialisation):
            individu.infecter(round(infectes_durees[id]))
            liste_infectes.append(individu)

        hospitalises_initialisation = random.sample(
            self.population.individus, self.init.nombre_hospitalises)
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
            #print(f"Simulation du jour {jour}")
            if len(liste_infectes) == 0:
                break

            nouveaux_infectes = 0
            nouveaux_hospitalises = 0
            nouveaux_decedes = 0
            nouveaux_gueris = 0

            # Traitement des individus qui ont un état à durée limitée
            for individu in liste_hospitalises:  # Individus hospitalisés
                if individu.infection_duree == 0:
                    # On décide si l'individu redevient sain, ou décède
                    if probabilite(self.param.deces_proba, individu.get_immunite(jour, DECES)):
                        individu.deces()
                        liste_decedes.append(individu)
                        nouveaux_decedes += 1
                    else:
                        individu.guerir(jour)
                        nouveaux_gueris += 1
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
                        nouveaux_hospitalises += 1
                    else:
                        individu.guerir(jour)
                        liste_infectes.remove(individu)
                        nouveaux_gueris += 1

                elif individu.sante_duree is not None:
                    individu.sante_duree -= 1
                    for (voisin_id, voisin_distance) in individu.voisins:
                        voisin = self.population.get_individu(voisin_id)
                        if voisin.sante == NEUTRE and probabilite(self.param.infection_proba, voisin.get_immunite(jour, INFECTION)*self.param.multiplicateur_distance/max(voisin_distance**2, 0.2)):
                            voisin.infecter(
                                round(np.random.normal(*self.param.infection_duree)))
                            liste_infectes.append(voisin)
                            nouveaux_infectes += 1

            # Vaccination
            if jour >= self.param.jour_debut_vaccination:
                for (vaccin_type, nombre_doses) in self.population.get_nombre_vaccination(jour-self.param.jour_debut_vaccination+1):
                    nombre_doses = round(nombre_doses*len(self.population.individus)/self.param.taille_population_vaccination)
                    vaccines = random.sample(liste_non_vaccines, nombre_doses)
                    for individu in vaccines:
                        liste_non_vaccines.remove(individu)
                        liste_vaccines.append(individu)
                        individu.vacciner(vaccin_type, jour)

            print(
                f"\033[KRapport du jour {jour} : Infectés : {len(liste_infectes)}, Hospitalisés : {len(liste_hospitalises)}, Décédés : {len(liste_decedes)}, Vaccinés : {len(liste_vaccines)}")

            self.stats["total_infectes"].append(len(liste_infectes))
            self.stats["total_hospitalises"].append(len(liste_hospitalises))
            self.stats["total_decedes"].append(len(liste_decedes))
            self.stats["nouveaux_infectes"].append(nouveaux_infectes)
            self.stats["nouveaux_hospitalises"].append(nouveaux_hospitalises)
            self.stats["nouveaux_decedes"].append(nouveaux_decedes)
            self.stats["nouveaux_gueris"].append(nouveaux_gueris)
            self.stats["vaccines"].append(len(liste_vaccines))

        print("=== Fin de la simulation ===")

        self.afficher_resultats()

    def get_couleur(self, individu):
        if individu.sante != NEUTRE:
            return COULEUR[individu.sante]
        elif individu.vaccin_date is not None:
            return COULEUR["VACCINE"]        
        elif individu.infection_immunite_date is not None:
            return COULEUR["IMMUNISE"]
        else:
            return COULEUR[individu.infection]

    def afficher_resultats(self):
        jours_liste = list(np.arange(0, len(self.stats["total_infectes"])))
        self.stats["total_neutres"] = []
        for jour in jours_liste:
            self.stats["total_neutres"].append(len(
                self.population.individus)-self.stats["total_infectes"][jour]-self.stats["total_decedes"][jour])

        figure = make_subplots(rows=2, cols=2)

        liste_couleur = np.array([self.get_couleur(individu) for individu in self.population.individus])
        figure.add_trace(
            graph.Scattergl(x=self.population.population_position[:, 0], y=self.population.population_position[:, 1], mode='markers', marker=dict(color=liste_couleur[:,0], line=dict(color=liste_couleur[:,1]))), 1, 2)
        figure.update_traces(hoverinfo="x+y", showlegend=False, row=1)

        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["total_neutres"], mode='markers+lines', name="Total sains", legendgroup="totaux"), 2, 1)
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["total_infectes"], mode='markers+lines', name="Total infectés", legendgroup="totaux"), 2, 1)
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["total_hospitalises"], mode='markers+lines', name="Total hospitalisés", legendgroup="totaux"), 2, 1)
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["total_decedes"], mode='markers+lines', name="Total décédés", legendgroup="totaux"), 2, 1)
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["vaccines"], mode='markers+lines', name="Vaccinés", legendgroup="totaux"), 2, 1)

        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["nouveaux_gueris"], mode='markers+lines', name="Nouveaux guéris", legendgroup="journalier"), 2, 2)
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["nouveaux_infectes"], mode='markers+lines', name="Nouveaux infectés", legendgroup="journalier"), 2, 2)
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["nouveaux_hospitalises"], mode='markers+lines', name="Nouveaux hospitalisés", legendgroup="journalier"), 2, 2)
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["nouveaux_decedes"], mode='markers+lines', name="Nouveaux décédés", legendgroup="journalier"), 2, 2)

        figure.update_xaxes(title_text="Jours de simulation", row=2)
        figure.update_yaxes(title_text="Nombre d'individus", row=2)
        figure.update_layout(
            hovermode="x", title_text="Simulation de la propagation du CoViD-19", title_font_color='#EF553B')
        figure.update_traces(
            hoverinfo="name+x+y",
            line={"width": 1.3},
            marker={"size": 4},
            mode="lines+markers",
            row=2)
        figure.update_layout(legend=dict(orientation = "h", yanchor="bottom"))

        figure.show()
