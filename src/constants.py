#Paramètres de la simulation

class Error(Exception):
    pass


#Nombre d'individus
nb_population = 1000

#Constantes communes aux programmes

#Constantes des identifiants des différents status de l'infection d'une personne

#Types d'états
SANTE = 1
INFECTION = 0

#Etat santé
DECEDE = -1
NEUTRE = 0
INFECTE = 1

#Etat infection
NEUTRE = 0
ISOLE = 1
HOSPITALISE = 2
REANIMATION = 3

#Situation initiale :
SITUATION_INITIALE = {
"INFECTE" : 0.1,
"HOSPITALISE" : 0.05,
"REANIMATION" : 0.002
}

#Durée des phases infectieuses
DUREE = {
"INFECTE" : [7, 15],
#IMMUNISE : [50, 75]
}



#Constantes des libbelés des états sur le graphe final
NAME = {
"MORT" : "décédé",
"NEUTRE" : "neutre",
"INFECTE" : "infecté",
#SAIN : "sain",
#IMMUNISE : "immunisé"
}

#Couleur des points représentatifs de chaque état sur le graphe
COLOR = {
"MORT" : ['#AB63FA', '#AB63FA'],
"NEUTRE" : ['#636EFA', '#636EFA'],
"INFECTE" : ['#EF553B', '#EF553B'],
#SAIN : [],
#IMMUNISE : ['#00CC96', '#00CC96']
}
