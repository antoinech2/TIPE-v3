#Paramètres de la simulation

class Error(Exception):
    pass

#Constantes communes aux programmes

#Constantes des identifiants des différents status de l'infection d'une personne

#Types d'états
INFECTION = 1
HOSPITALISATION = 2
DECES = 3

#Etat santé
DECEDE = -1
NEUTRE = 0
INFECTE = 1

#Etat infection
NEUTRE = 0
ISOLE = 1
HOSPITALISE = 2


#Constantes des libbelés des états sur le graphe final
LIBELE = {
DECEDE : "Décédé",
NEUTRE : "Sain",
INFECTE : "Infecté",
HOSPITALISE : "Hospitalisé",
}

#Couleur des points représentatifs de chaque état sur le graphe
COULEUR = {
DECEDE : ['#474747', '#000000'],
NEUTRE : ['#0cf036', '#069420'],
INFECTE : ['#0a4b6e', '#07334a'],
HOSPITALISE : ['#960606', '#690404'],
"IMMUNISE" : ['#fcba03', '#876300'],
"VACCINE" : ['#fc03f4', '#750272']
}
