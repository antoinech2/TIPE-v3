"""Modèle de propagation de la simulation"""

# Modules externes

import random
from dataclasses import dataclass
from math import ceil
from time import time

import numpy as np
import plotly.graph_objects as graph
from plotly.subplots import make_subplots

# Module interne
from constantes import *


def probabilite(base, multiplicateur):
    """Renvoie vrai ou faux selon une probabilité de base et un multiplicateur"""
    return base*multiplicateur >= random.random()


@dataclass
class Strategie:
    """Représente une stratégie vaccinale"""

    # Liste des clauses de vaccination qui incluent une date de mise en place et un public ciblé
    dates_vaccination: list[tuple[int, dict]]

    # Jour du début de la campagne de vaccination
    jour_debut_vaccination: int = 1

    # Population de référence pour les données de vaccination
    taille_population_vaccination: int = 67813396  # Source : Insee 2022


@dataclass
class SituationInitiale:
    """Représente la situation initiale de l'état de santé de la population au jour 0"""
    # Nombre d'infectés et hospitalisés initialement (jour 0)
    nombre_infectes: int = 16
    nombre_hospitalises: int = 4


@dataclass
class Parametres:
    """Représente les paramètres de la simulation"""
    # Durée maximale de la simulation (en jour)
    simulation_duree: int

    # Durée d'une infection et d'une hospitalisation ((moyenne, écart type) selon une loi de distibution normale)
    infection_duree: tuple[float, float] = (7, 1.5)
    hopital_duree: tuple[float, float] = (30, 1.5)

    # Probabilité de base d'infection, hospitalisation et décès
    infection_proba: float = 4.1e-4
    hopital_proba: float = 0.0442
    deces_proba: float = 0.2


class Simulation:
    """Moteur de la simulation"""

    def __init__(self, population, strategie, situation_init, parametres, nom):
        self.population = population
        self.strategie = strategie
        self.init = situation_init
        self.param = parametres
        self.nom = nom

        # Dictionnaire des statistiques de la courbe finale
        self.stats = {
            "total_infectes": [self.init.nombre_infectes],
            "total_hospitalises": [self.init.nombre_hospitalises],
            "total_decedes": [0],
            "nouveaux_infectes": [0],
            "nouveaux_hospitalises": [0],
            "nouveaux_decedes": [0],
            "nouveaux_gueris": [0],
            "vaccines": [0]
        }

        self.start_simulation()

    def start_simulation(self):
        temps_depart = time()

        # Initialisation des listes et variables
        liste_infectes = []
        liste_hospitalises = []
        liste_decedes = []
        liste_vaccines = []
        liste_non_vaccines = [
            individu for individu in self.population.individus if individu.age >= 12]
        doses_a_distribuer = 0

        # Jour 0 : mise en place de la situation initiale
        # Infectés
        infectes_initialisation = random.sample(
            self.population.individus, self.init.nombre_infectes)  # Sélection de l'échantillon
        infectes_durees = np.random.normal(
            *self.param.infection_duree, self.init.nombre_infectes)  # Choix de la durée
        for id, individu in enumerate(infectes_initialisation):
            individu.infecter(round(infectes_durees[id]))
            liste_infectes.append(individu)

        # Hospitalisés
        hospitalises_initialisation = random.sample(
            self.population.individus, self.init.nombre_hospitalises)
        hospitalises_durees = np.random.normal(
            *self.param.hopital_duree, self.init.nombre_hospitalises)
        for id, individu in enumerate(hospitalises_initialisation):
            individu.hospitaliser(round(hospitalises_durees[id]))
            liste_hospitalises.append(individu)
            if individu not in liste_infectes:
                liste_infectes.append(individu)

        print("=== Début de la simulation ===")

        for jour in range(1, self.param.simulation_duree + 1):
            # Nouveau jour
            if len(liste_infectes) == 0:  # Condition d'arrêt de la simulation
                break

            # Initialisation des variables du jour
            nouveaux_infectes = 0
            nouveaux_hospitalises = 0
            nouveaux_decedes = 0
            nouveaux_gueris = 0

            # Traitement des individus qui ont un état à durée limitée
            # Individus hospitalisés
            for individu in liste_hospitalises:
                if individu.infection_duree == 0:
                    # On décide si l'individu redevient sain, ou décède
                    if probabilite(self.param.deces_proba, individu.get_immunite(jour, DECES)):
                        individu.deces()
                        liste_decedes.append(individu)
                        nouveaux_decedes += 1
                        #print(f"Décès : {individu.age}, vaccin : {jour - individu.vaccin_date if individu.vaccin_date is not None else -1}")
                    else:
                        individu.guerir(jour)
                        nouveaux_gueris += 1
                    liste_infectes.remove(individu)
                    liste_hospitalises.remove(individu)
                elif individu.infection_duree is not None:
                    individu.infection_duree -= 1

            # Individus infectés
            for individu in liste_infectes:
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
                    # Infection potentielle des voisins
                    for (voisin_id, voisin_distance) in individu.voisins:
                        voisin = self.population.get_individu(voisin_id)
                        if voisin.sante == NEUTRE and probabilite(self.param.infection_proba, voisin.get_immunite(jour, INFECTION)/max(voisin_distance, 0.2)):
                            # Infection du voisin
                            voisin.infecter(
                               round(np.random.normal(*self.param.infection_duree)))
                            liste_infectes.append(voisin)
                            nouveaux_infectes += 1

            # Vaccination
            if jour >= self.strategie.jour_debut_vaccination:
                for (vaccin_type, nombre_doses) in self.population.get_nombre_vaccination(jour-self.strategie.jour_debut_vaccination+1):
                    # Calcul du nombre de doses effective sur la taille de la population de la simulation
                    doses_a_distribuer += round(nombre_doses*len(
                        self.population.individus)/self.strategie.taille_population_vaccination)
                    random.shuffle(liste_non_vaccines)
                    for individu in liste_non_vaccines:
                        if doses_a_distribuer <= 0:
                            break
                        if individu.sante == NEUTRE and individu.eligible_vaccin(jour-self.strategie.jour_debut_vaccination+1, self.strategie):
                            # Vaccination de l'individu s'il est éligible
                            liste_non_vaccines.remove(individu)
                            liste_vaccines.append(individu)
                            individu.vacciner(vaccin_type, jour)
                            doses_a_distribuer -= 1

            print(
                f"\033[KRapport du jour {jour} : Infectés : {len(liste_infectes)}, Hospitalisés : {len(liste_hospitalises)}, Décédés : {len(liste_decedes)}, Vaccinés : {len(liste_vaccines)}, Temps d'éxécution : {round(time() - temps_depart)}s")

            # Mise à jour des statistiques
            self.stats["total_infectes"].append(len(liste_infectes))
            self.stats["total_hospitalises"].append(len(liste_hospitalises))
            self.stats["total_decedes"].append(len(liste_decedes))
            self.stats["nouveaux_infectes"].append(nouveaux_infectes)
            self.stats["nouveaux_hospitalises"].append(nouveaux_hospitalises)
            self.stats["nouveaux_decedes"].append(nouveaux_decedes)
            self.stats["nouveaux_gueris"].append(nouveaux_gueris)
            self.stats["vaccines"].append(len(liste_vaccines))

        print(
            f"=== Fin de la simulation (en {round(time() - temps_depart)} secondes) ===")

        self.afficher_resultats()

    def get_couleur(self, individu):
        """Renvoie la couleur d'affichage sur le graphique d'un individu"""
        if individu.sante != NEUTRE:
            return COULEUR[individu.sante]
        elif individu.vaccin_date is not None:
            return COULEUR["VACCINE"]
        elif individu.infection_immunite_date is not None:
            return COULEUR["IMMUNISE"]
        else:
            return COULEUR[individu.infection]

    def afficher_resultats(self):
        """Affiche les graphiques des résultats"""

        # Abscisse des jours
        jours_liste = list(np.arange(0, len(self.stats["total_infectes"])))

        # Calcul du nombre d'individus neutres chaque jour
        self.stats["total_neutres"] = []
        for jour in jours_liste:
            self.stats["total_neutres"].append(len(
                self.population.individus)-self.stats["total_infectes"][jour]-self.stats["total_decedes"][jour])

        # Figure 1 : Répartition géographique des individus
        figure = graph.Figure()

        liste_couleur = np.array([self.get_couleur(individu)
                                 for individu in self.population.individus])
        figure.add_trace(
            graph.Scattergl(x=self.population.population_position[:, 0], y=self.population.population_position[:, 1], mode='markers', marker=dict(color=liste_couleur[:, 0], line=dict(color=liste_couleur[:, 1]))))
        figure.update_traces(hoverinfo="x+y", showlegend=False)
        figure.update_layout(title_text=self.nom, title_font_color='#EF553B')
        figure.show()

        # Figure 2 : Courbes de l'état de santé des individus au cours du temps
        figure = graph.Figure()

        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["total_neutres"], mode='markers+lines', name="Total sains", legendgroup="totaux"))
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["total_infectes"], mode='markers+lines', name="Total infectés", legendgroup="totaux"))
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["total_hospitalises"], mode='markers+lines', name="Total hospitalisés", legendgroup="totaux"))
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["total_decedes"], mode='markers+lines', name="Total décédés", legendgroup="totaux"))
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["vaccines"], mode='markers+lines', name="Vaccinés", legendgroup="totaux"))

        figure.update_xaxes(title_text="Jours de simulation")
        figure.update_yaxes(title_text="Nombre d'individus")
        figure.update_layout(hovermode="x", title_text=self.nom, title_font_color='#EF553B')
        figure.update_traces(
            hoverinfo="name+x+y",
            line={"width": 1.3},
            marker={"size": 4},
            mode="lines+markers")
        figure.show()

        # Figure 3 : Courbes des nouveaux états de santé au cours du temps
        figure = graph.Figure()

        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["nouveaux_gueris"], mode='markers+lines', name="Nouveaux guéris", legendgroup="journalier"))
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["nouveaux_infectes"], mode='markers+lines', name="Nouveaux infectés", legendgroup="journalier"))
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["nouveaux_hospitalises"], mode='markers+lines', name="Nouveaux hospitalisés", legendgroup="journalier"))
        figure.add_trace(graph.Scatter(
            x=jours_liste, y=self.stats["nouveaux_decedes"], mode='markers+lines', name="Nouveaux décédés", legendgroup="journalier"))

        figure.update_xaxes(title_text="Jours de simulation")
        figure.update_yaxes(title_text="Nombre d'individus")
        figure.update_layout(hovermode="x", title_text=self.nom, title_font_color='#EF553B')
        figure.update_traces(
            hoverinfo="name+x+y",
            line={"width": 1.3},
            marker={"size": 4},
            mode="lines+markers")
        figure.show()
