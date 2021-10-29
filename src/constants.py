#Constantes communes aux programmes

#phase_infection :
#Constantes des identifiants des différents status de l'infection d'une personne
MORT = -1
NEUTRE = 0
INFECTE = 1
IMMUNISE = 2
SAIN = [NEUTRE, IMMUNISE]
#REMOVED = [IMMUNISE, MORT]

#Constantes des libbelés des états sur le graphe final
NAME = {
MORT : "décédé",
NEUTRE : "neutre",
INFECTE : "infecté",
#SAIN : "sain",
IMMUNISE : "immunisé"
}

#Couleur des points représentatifs de chaque état sur le graphe
COLOR = {
MORT : ['#AB63FA', '#AB63FA'],
NEUTRE : ['#636EFA', '#636EFA'],
INFECTE : ['#EF553B', '#EF553B'],
#SAIN : [],
IMMUNISE : ['#00CC96', '#00CC96']
}

#Durée des phases infectieuses
DUREE = {
INFECTE : 10,
IMMUNISE : 50
}
