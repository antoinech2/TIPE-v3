#Modélisation de la propagation et affichage des graphiques avec plotly

#Modules externes
from sklearn.datasets import make_blobs
import random as rd
import time
from scipy.spatial import distance
from plotly.offline import plot
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

#Modules internes
from population import *
from constants import *

def distance_e(x, y):  # distance entre 2 points du plan cartésien
    return distance.euclidean([x[0],x[1]],[y[0],y[1]])

max_jour = 1000

#Variables de simulation [TEMPORAIRE]
variance_pop = 1  # recommandé : 1
rayon_contamination = 0.5  # recommandé : 0.5
infectiosite = 0.01  # recommandé : 10%
p = 0.15  # recommandé : 10% : IMMUNITE
d = 0.02  # recommandé : 5% : MORT

#Fonctions temporaires pour déterminer la propagation du virus
#A modifier pour prendre en compte les caractéristiques de chaque individu

def ChanceInfection(individu):  # return True si il devient infecté avec une proba p
    return rd.random() <= infectiosite

def ChanceImmunite(individu):  # l: infectés; l2: immunisés précédents
    return rd.random() <= p

def ChanceMort(individu):  # l: infectés; l2: décès précédents; l3: immunisés
    return rd.random() <= d

def StartSimulation():
    """Simulation de l'épidémie"""
    print('Début de la simulation ... \n')
    start = time.time()

    # NOTE : si les courbes restent constantes, augmentez le rayon de contamination
    # si le virus est trés mortel il n'y aura pas beaucoup de propagation

    if nb_population < 10 or rayon_contamination <= 0:
        return 'error, nb_population and var_population and rayon_contamination must be >=10 and > 0'
    if infectiosite < 0 or infectiosite > 1:
        return 'error, infectiosité must be in [0,1]'
    if p < 0 or p > 1:
        return 'error, p must be in [0,1]'
    if d < 0 or p > 1:
        return 'error, d must be in [0,1]'

    # création des figures
    fig = make_subplots(rows=2, cols=2, column_widths=[0.8, 0.2], row_heights=[0.5, 0.5],
                        subplot_titles=["population", "", ""],
                        specs=[[{'type': 'xy'}, {'type': 'domain'}], [{'type': 'xy', 'colspan': 2}, None]],
                        horizontal_spacing=0.05, vertical_spacing=0.05)

    # création des courbes finales et listes des coordonnées
    data = dict(courbe_neutres = [],courbe_infectes = [],courbe_immunises = [],courbe_deces = [],courbe_sains = [])

    id_patient_0 = rd.randint(0, nb_population - 1)  # on choisit le premier individu infecté au hasard
    #On infecte le patient 0
    Infect(id_patient_0)

    # Remplissage des listes initialement
    data['courbe_neutres'].append(nb_population-1)
    data['courbe_infectes'].append(1)
    data['courbe_immunises'].append(0)
    data['courbe_deces'].append(0)
    data['courbe_sains'].append(nb_population-1)

    jour = 2
    # Jours 2 à n

    #On boucle sur chaque jour de simulation jusqu'à une condition d'arrêt (plus d'infection ou plus de neutre)
    while jour <= max_jour and (GetNombreEtatInfection(IMMUNISE) > 0 or GetNombreEtatInfection(INFECTE) > 0): #condition d'arrêt
        print("Jour {}...".format(jour))

        #Traitement des individus ayant un état à durée limitée
        #On régupère tous les individus concernés
        for id_individu, etat, duree_etat in GetListDureeEtat():
            if duree_etat != 0:
                #Si la durée restante est non nulle, on la diminue d'un jour
                ReduceDureeEtat(id_individu)
            else:
                #Lorsque l'on atteint la fin de l'état
                if etat == INFECTE:
                    #A la fin d'une infection, on détermine avec les fonctions de probas si l'individus guérit, meurt ou redevient neutre
                    if ChanceMort(id_individu):
                        Mort(id_individu)
                    elif ChanceImmunite(id_individu):
                        Immunite(id_individu)
                    else:
                        Neutre(id_individu)
                elif etat == IMMUNISE:
                    #A la fin d'une immunité, l'individu redevient neutre
                    Neutre(id_individu)

        #On boucle sur tous les infectés pour éventuellement infecter des nouvelles personnes
        for (id_sain, id_infecte) in GetAllVoisins(rayon_contamination):
            #On vérifie si l'individu est encore sain à cet endroit de la boucle
            if GetEtatInfection(id_sain) == NEUTRE:
                if ChanceInfection(id_sain):
                    #On infecte l'individu sain
                    Infect(id_sain)

        #On applique les modifications et on passe au jour suivant
        pop_db.commit()
        jour += 1

        #On ajoute les données du jour aux listes des graphiques
        data['courbe_neutres'].append(GetNombreEtatInfection(NEUTRE))
        data['courbe_infectes'].append(GetNombreEtatInfection(INFECTE))
        data['courbe_immunises'].append(GetNombreEtatInfection(IMMUNISE))
        data['courbe_deces'].append(GetNombreEtatInfection(MORT))
        data['courbe_sains'].append(GetNombreEtatInfection(SAIN))

    #On calule le rendu du graphique final et on l'affiche
    for (id_individu, etat) in GetAllEtat():
        if (id_individu/nb_population*100) % 10 == 0:
            print("Rendering... {}/{} ({}%)".format(id_individu, nb_population, id_individu/nb_population*100))
        x, y = GetPosition(id_individu)
        fig.add_trace(go.Scatter(x=(x,), y=(y,), name=NAME[etat], mode="markers",
                                 marker=dict(
                                     color=COLOR[etat][0],
                                     size=5,
                                     line=dict(
                                         width=0.4,
                                         color=COLOR[etat][1])
                                 ),marker_line=dict(width=1), showlegend=False), 1, 1)
    fig.update_traces(hoverinfo="name")
    fig.update_xaxes(showgrid=False, visible=False, row=1, col=1)
    fig.update_yaxes(showgrid=False, visible=False, row=1, col=1)
    labels = ["neutres", "infectés", "immunisés", "décédés"]
    fig.add_trace(go.Pie(values=[GetNombreEtatInfection(NEUTRE), GetNombreEtatInfection(INFECTE), GetNombreEtatInfection(IMMUNISE), GetNombreEtatInfection(MORT)], labels=labels, sort=False), 1, 2)

    x_courbe = list(np.arange(0, len(data['courbe_neutres'])))
    fig.add_trace(go.Scatter(x=x_courbe, y=data['courbe_neutres'], marker=dict(color='#636EFA'), marker_line=dict(width=0.5),showlegend=False, name="neutres",yaxis="y", ), 2, 1)
    fig.add_trace(go.Scatter(x=x_courbe, y=data['courbe_infectes'], marker=dict(color='#EF553B'), marker_line=dict(width=0.5),showlegend=False, name="infectés",yaxis="y2", ), 2, 1)
    fig.add_trace(go.Scatter(x=x_courbe, y=data['courbe_immunises'], marker=dict(color='#00CC96'), marker_line=dict(width=0.5),showlegend=False, name="immunisés",yaxis="y3", ), 2, 1)
    fig.add_trace(go.Scatter(x=x_courbe, y=data['courbe_deces'], marker=dict(color='#AB63FA'), marker_line=dict(width=0.5),showlegend=False, name="décédés",yaxis="y4", ), 2, 1)
    fig.add_trace(go.Scatter(x=x_courbe, y=data['courbe_sains'], marker=dict(color='#000000'), marker_line=dict(width=0.5), showlegend=False, name="sains",yaxis="y5", ), 2, 1)
    fig.update_xaxes(title_text="jours", row=2, col=1)
    fig.update_yaxes(title_text="nombre d'individus", row=2, col=1)
    fig.add_annotation(text="Maximum d'infectés", x=data['courbe_infectes'].index(max(data['courbe_infectes'])),# ajouter un texte avec une flèche
                       y=max(data['courbe_infectes']) + 0.03 * nb_population, arrowhead=1, showarrow=True, row=2, col=1)
    fig.update_traces(
        hoverinfo="name+x+y",
        line={"width": 1.3},
        marker={"size": 2},
        mode="lines+markers",
        showlegend=False, row=2, col=1)

    fig.update_layout(hovermode="x",title_text="simulation virus",title_font_color='#EF553B')
    t = (time.time()-start)
    min = int(round(t,2)//60)
    sec = round(t-min*60,1)
    print('Simulation terminée en '+str(min)+' minutes \net '+str(sec)+' secondes')
    plot(fig)
    pop_db.commit()
