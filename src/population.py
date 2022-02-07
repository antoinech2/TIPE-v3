#Fichier pour générer la population
#Objectif : recréer une population représentative de la France par rapport à différents critères.

#Modules internes
from constants import *

#Modules externes
import sqlite3
import numpy as np
from random import random
from sklearn.datasets import make_blobs
from scipy.spatial import distance

DESTROY_TABLE = True #Mettre à True pour regénérer une nouvelle population à chaque nouvelle exécution
CLEAN_TABLE = False
REGENERATE_AGE = True
REGENERATE_POSITION = True
REGENERATE_MALADIE = True

database_loc_data = "../res/population_data.db" #Chemin de la BDD qui contient les informations de génération de la population
database_loc_pop = "../data/population.db" #Chemin de la BDD qui contient la liste des individus, et les états infectieux

#Initialisation des BDD et des curseurs
data_db = sqlite3.connect(database_loc_data)
pop_db = sqlite3.connect(database_loc_pop)
data_cur = data_db.cursor()
pop_cur = pop_db.cursor()

def GeneratePopulation(nb_population, variance_pop):
    """Génère la population en complétant la BDD"""
    print("Génération de la population...")
    if DESTROY_TABLE: #On supprime les anciennes tables pour tout regénérer
        try:
            pop_cur.execute("DROP TABLE population")
            pop_cur.execute("DROP TABLE etat")
            pop_cur.execute("DROP TABLE distance")
        except:
            pass

    #On créer les deux tables.
    # "population" contient la liste des individus, leur âge et présence de maladie chronique
    # "etat" contient l'état infectieux de la population, la durée restante de l'état, le rang vaccinal (nombre d'injections) et le type de vaccin
    pop_cur.execute('CREATE TABLE IF NOT EXISTS "population" ("id_individu" INTEGER NOT NULL,"x_coord" REAL,"y_coord" REAL,"age" INTEGER,\
    "sexe" TEXT NOT NULL DEFAULT "femme", "activité" TEXT, "quintile" INTEGER,"tabac" INTEGER NOT NULL DEFAULT 0,"alcool" INTEGER NOT NULL DEFAULT 0,\
    "obésité" INTEGER NOT NULL DEFAULT 0,"diabète" INTEGER NOT NULL DEFAULT 0,"dyslipidémies" INTEGER NOT NULL DEFAULT 0,\
    "métabolique" INTEGER NOT NULL DEFAULT 0,"hypertension" INTEGER NOT NULL DEFAULT 0,"coronariennes" INTEGER NOT NULL DEFAULT 0,\
    "artériopathie" INTEGER NOT NULL DEFAULT 0,"trouble cardiaque" INTEGER NOT NULL DEFAULT 0,"insuffisance cardiaque" INTEGER NOT NULL DEFAULT 0,\
    "valvulopathies" INTEGER NOT NULL DEFAULT 0,"avc" INTEGER NOT NULL DEFAULT 0,"respiratoire" INTEGER NOT NULL DEFAULT 0,\
    "mucoviscidose" INTEGER NOT NULL DEFAULT 0,"embolie" INTEGER NOT NULL DEFAULT 0,"cancer" INTEGER NOT NULL DEFAULT 0,\
    "inflammatoire" INTEGER NOT NULL DEFAULT 0,"antidépresseur" INTEGER NOT NULL DEFAULT 0,"neuroleptique" INTEGER NOT NULL DEFAULT 0,\
    "parkinson" INTEGER NOT NULL DEFAULT 0,"démence" INTEGER NOT NULL DEFAULT 0,PRIMARY KEY("id_individu" AUTOINCREMENT))')
    pop_cur.execute('CREATE TABLE IF NOT EXISTS "etat" (\
	"id_individu"	INTEGER NOT NULL,\
	"etat_infection"	INTEGER NOT NULL DEFAULT 0,\
	"duree_etat_infection"	INTEGER,\
	"etat_sante"	INTEGER NOT NULL DEFAULT 0,\
	"duree_etat_sante"	INTEGER,\
	"rang_vaccin"	INTEGER NOT NULL DEFAULT 0,\
	"immunite"	REAL NOT NULL DEFAULT 0,\
	PRIMARY KEY("id_individu" AUTOINCREMENT));')
    pop_cur.execute('CREATE TABLE IF NOT EXISTS "distance" ("id_1" INTEGER NOT NULL, "id_2" INTEGER NOT NULL, "distance" REAL NOT NULL, PRIMARY KEY("id_1", "id_2"))')
    pop_db.commit()

    if CLEAN_TABLE:
        pop_cur.execute("DELETE FROM etat")
        for i in range(nb_population):
            pop_cur.execute("INSERT INTO etat DEFAULT VALUES")


    if REGENERATE_AGE:
        print("Attribution de l'âge...")
        #AGE
        #On récupère la répartition des âges dans la BDD
        nb_age = data_cur.execute("SELECT COUNT(age) FROM age_detail").fetchall()[0][0]
        for age in range(nb_age): #On boucle sur tous les âges à attribuer
            #On calcule le nombre d'individu à attribuer cet âge en fonction de la proportion de cet âge dans la population
            if age == 100:
                nb_individu_age = nb_population - pop_cur.execute("SELECT COUNT(id_individu) FROM population").fetchall()[0][0]
            else:
                nb_individu_age = round(data_cur.execute("SELECT proportion FROM age_detail WHERE age = ?", (age,)).fetchall()[0][0] * nb_population)
            for individu in range(nb_individu_age): #On ajoute les individus dans la BDD avec l'âge voulu
                pop_cur.execute("INSERT INTO population (age) VALUES (?)", (age,))
                pop_cur.execute("INSERT INTO etat DEFAULT VALUES")
        pop_db.commit()
    else:
        print("Réutilisation des données d'âge de la simulation précédente")

    if REGENERATE_POSITION :

        print("Attribution des coordonées de chaque individu...")
        x, y = make_blobs(n_samples=nb_population, centers=1, cluster_std=variance_pop) #Génération des coordonées
        for individu_coord in x:
            pop_cur.execute("UPDATE population SET x_coord = ?, y_coord = ? WHERE id_individu = (SELECT id_individu FROM population WHERE x_coord IS NULL ORDER BY RANDOM() LIMIT 1)", (individu_coord[0], individu_coord[1]))

        print("Calcul des distances entre chaque individu...")
        for id_1 in range(1, nb_population+1):
            if (id_1/nb_population*100) % 10 == 0:
                print("Processing... {}/{} ({}%)".format(id_1, nb_population, id_1/nb_population*100))

            for id_2 in range(1, nb_population+1):
                id_1_coords = pop_cur.execute("SELECT x_coord, y_coord FROM population WHERE id_individu = ?", (id_1,)).fetchall()[0]
                id_2_coords = pop_cur.execute("SELECT x_coord, y_coord FROM population WHERE id_individu = ?", (id_2,)).fetchall()[0]
                dist = distance.euclidean([id_1_coords[0],id_1_coords[1]],[id_2_coords[0],id_2_coords[1]])
                pop_cur.execute("INSERT INTO distance (id_1, id_2, distance) VALUES (?, ?, ?)", (id_1, id_2, dist))

        pop_db.commit()
    else:
        print("Réutilisation des données de position de la simulation précédente")

    print("Attribution du sexe...")
    proportion_homme = data_cur.execute("SELECT proportion FROM repartition_sexe WHERE sexe = 'homme'").fetchall()[0][0]
    pop_cur.execute("UPDATE population SET sexe = 'homme' WHERE id_individu IN (SELECT id_individu FROM population ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population) * ?))", (proportion_homme, ))
    pop_db.commit()

    print("Attribution des quintiles sociales...")
    quintiles_prop = data_cur.execute("SELECT quintile, proportion FROM social").fetchall()
    for quintile in quintiles_prop:
        pop_cur.execute("UPDATE population SET quintile = ? WHERE id_individu IN (SELECT id_individu FROM population WHERE quintile IS NULL ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population) * ?))", (quintile[0], quintile[1]))
    pop_db.commit()

    print("Attribution des habitudes de vie...")
    habitudes_prop = data_cur.execute("SELECT carac, proportion FROM habitudes").fetchall()
    prop_15_ans = data_cur.execute("SELECT SUM(proportion) FROM age_detail WHERE age >= 15").fetchall()[0][0]
    for habitude in habitudes_prop:
        prop_ponderee = habitude[1]/prop_15_ans
        pop_cur.execute("UPDATE population SET {} = 1 WHERE id_individu IN (SELECT id_individu FROM population WHERE age >= 15 ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population WHERE age >= 15) * ?))".format(habitude[0]), (prop_ponderee, ))
    pop_db.commit()

    if REGENERATE_MALADIE:
        print("Attribution de la présence de maladies...")
        #MALADIES CHRONIQUES
        # On récupère chaque tranche d'âge avec la proportion de personnes qui ont une maladie chronique
        moyenne_proportion_age = data_cur.execute("SELECT AVG(proportion) FROM repartition_maladie").fetchall()[0][0]
        nb_maladie = data_cur.execute("SELECT COUNT(nom) FROM maladie").fetchall()[0][0]
        avancement = 0
        for (maladie, proportion_maladie) in data_cur.execute("SELECT nom, proportion FROM maladie").fetchall():
            avancement += 1
            print("\x1b[2K\r   Attribution de la maladie {}/{} ({}%) ('{}')".format(avancement, nb_maladie, avancement/nb_maladie*100, maladie))
            avancement_pop = 0
            for (id_individu, age) in pop_cur.execute("SELECT id_individu,age FROM population").fetchall():
                avancement_pop += 1
                if avancement_pop % 5000 == 0:
                    print("\x1b[2K\r      Attribution de la maladie {}/{} ({}%)".format(avancement_pop, nb_population, avancement_pop/nb_population*100), end="")
                proportion_age = data_cur.execute("SELECT proportion FROM repartition_maladie WHERE min <= ? AND max >= ?", (age, age)).fetchall()[0][0]
                if random() < proportion_maladie*proportion_age/moyenne_proportion_age:
                    pop_cur.execute("UPDATE population SET '{}' = 1 WHERE id_individu = ?".format(maladie), (id_individu, ))
        pop_db.commit()
    else:
        print("Réutilisation des données de maladies de la simulation précédente")

    print("Attribution de l'emploi...")
    pop_cur.execute("UPDATE population SET activité = 'études' WHERE age >= 3 AND age < 15")
    for (age_min, age_max, sexe, proportion_emploi) in data_cur.execute("SELECT * FROM repartition_emploi").fetchall():
        for (secteur, proportion_sexe, proportion_age) in data_cur.execute("SELECT emploi_sexe.secteur, emploi_sexe.proportion, emploi_age.proportion FROM emploi_age JOIN emploi_sexe ON emploi_sexe.secteur = emploi_age.secteur WHERE sexe = ? AND min <= ? AND max >= ?", (sexe, age_min, age_max)).fetchall():
            pop_cur.execute("UPDATE population SET activité = ? WHERE id_individu IN (SELECT id_individu FROM population WHERE sexe = ? AND age <= ? AND age >= ? AND activité IS NULL ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population WHERE sexe = ? AND age <= ? AND age >= ?) * ?))", (secteur, sexe, age_max, age_min,sexe, age_max, age_min, proportion_emploi*proportion_age*proportion_sexe))
    pop_db.commit()

    print("Population générée !")

def CloseDB():
    """Ferme les curseur et les BDD"""
    pop_cur.close()
    pop_db.close()
    data_cur.close()
    data_db.close()


class Individu:
    def __init__(self, age, position, sexe, activite, multiplicateur, liste_voisins):
        self.age = age
        self.position = position
        self.sexe = sexe
        self.activite = activite
        self.multiplicateur = multiplicateur
        print(liste_voisins)

maladie_liste = ["obésité", "diabète", "dyslipidémies", "métabolique", "hypertension", "coronariennes", "artériopathie", "trouble cardiaque", "insuffisance cardiaque", "valvulopathies", "avc", "respiratoire", "mucoviscidose", "embolie", "cancer", "inflammatoire", "antidépresseur", "neuroleptique", "parkinson", "démence"]

class Population:
    def __init__(self, nb_individus, variance_pop, min_distance):
        GeneratePopulation(nb_individus, variance_pop)
        pop_db.row_factory = sqlite3.Row
        pop_cur = pop_db.cursor()
        self.individus = []
        for id in range(1, nb_individus+1):
            data = dict(pop_cur.execute("SELECT * from population WHERE id_individu = ?", (id, )).fetchall()[0])
            voisins = np.array(pop_cur.execute("SELECT id_2 from distance WHERE id_1 = ? AND distance > 0.0 AND distance <= ?", (id, min_distance)).fetchall())
            if len(voisins) != 0:
                voisins = voisins[:,0]
            self.individus.append(Individu(data["age"], (data["x_coord"], data["y_coord"]), data["sexe"], data["activité"], self.calcul_risque_multiplicateur(data), voisins))

    def calcul_risque_multiplicateur(self, data):
        multiplicateur = np.array(data_cur.execute("SELECT probar_hopital, probar_deces from age WHERE min <= ? AND max >= ?", (data["age"], data["age"])).fetchall()[0])
        multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from social WHERE quintile = ?", (data["quintile"],)).fetchall()[0])
        if data["tabac"]:
            multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from habitudes WHERE carac = 'tabac'").fetchall()[0])
        if data["alcool"]:
            multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from habitudes WHERE carac = 'alcool'").fetchall()[0])
        for maladie in maladie_liste:
            if data[maladie]:
                multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from maladie WHERE nom = ?", (maladie, )).fetchall()[0])
        return multiplicateur[0], multiplicateur[1]

test = Population(100, 2, 1)


#Getters

def GetAllEtat():
    """Renvoie tous les individus et leur état"""
    return pop_cur.execute("SELECT id_individu, etat FROM etat").fetchall()

def GetNombreEtatInfection(etat):
    """Renvoie le nombre d'invidus qui ont l'état précisé"""
    if type(etat) != list:
        etat = [etat]
    return pop_cur.execute("SELECT COUNT(id_individu) FROM etat WHERE etat IN ({})".format(str(etat)[1:len(str(etat))-1])).fetchall()[0][0]

def GetListEtatInfection(etat):
    """Revoie la liste des id d'individus qui ont l'état précisé"""
    if type(etat) != list:
        etat = [etat]
    return np.array(pop_cur.execute("SELECT id_individu FROM etat WHERE etat IN ({})".format(str(etat)[1:len(str(etat))-1])).fetchall())[:, 0]

def GetEtatInfection(id_individu):
    """Renvoie l'état d'un individu en spécifiant son id"""
    return pop_cur.execute("SELECT etat FROM etat WHERE id_individu = ?", (int(id_individu),)).fetchall()[0][0]

def GetListDureeEtat(type):
    """Renvoie la liste des individus qui ont un état à durée définie, leur état et la durée restante associée"""
    if type == INFECTION:
        return np.array(pop_cur.execute("SELECT id_individu, etat_infection, duree_etat_infection FROM etat WHERE etat_infection != ? AND duree_etat_infection NOT NULL", (MORT, )).fetchall())
    else:
        return np.array(pop_cur.execute("SELECT id_individu, etat_sante, duree_etat_sante FROM etat WHERE duree_etat_sante NOT NULL AND etat_infection != ?", (MORT, )).fetchall())

def GetAllVoisins(min_distance):
    """Retourne la liste des couples d'infecté/sain qui sont suceptibles d'intéragir (propagation possible)"""
    return np.array(pop_cur.execute("SELECT id_1, id_2 FROM distance JOIN etat AS etat_1 ON etat_1.id_individu = id_1 JOIN etat AS etat_2 ON etat_2.id_individu = id_2 WHERE etat_1.etat = ? AND etat_2.etat = ? AND distance <= ?", (NEUTRE, INFECTE, min_distance)).fetchall())

def GetPosition(id_individu):
    """Retourne les coordonnées de l'individu"""
    return np.array(pop_cur.execute("SELECT x_coord, y_coord FROM population WHERE id_individu = ?", (id_individu,)).fetchall())[0]

#Setter

def Infect(id_individu):
    """Infecte un individu et défini son temps d'infection"""
    ChangeEtat(id_individu, INFECTE)
    pop_cur.execute("UPDATE etat SET duree_etat = ? WHERE id_individu = ?", (DUREE[INFECTE], int(id_individu)))

def ReduceDureeEtat(id_individu, type):
    """Réduit d'un jour la durée restante de l'état d'un individu"""
    if type == INFEFCTION:
        pop_cur.execute("UPDATE etat SET duree_etat_infection = duree_etat_infection - 1 WHERE id_individu = ?", (int(id_individu), ))
    else:
        pop_cur.execute("UPDATE etat SET duree_etat_sante = duree_etat_sante - 1 WHERE id_individu = ?", (int(id_individu), ))


def ChangeEtatSante(id_individu, new_etat):
    """Change l'état d'un individu"""
    pop_cur.execute("UPDATE etat SET etat_sante = ?, duree_etat_sante = NULL WHERE id_individu = ?", (new_etat, int(id_individu)))

def ChangeEtatInfection(id_individu, new_etat):
    """Change l'état d'un individu"""
    pop_cur.execute("UPDATE etat SET etat_infection = ?, duree_etat_infection = NULL WHERE id_individu = ?", (new_etat, int(id_individu)))

def Immunite(id_individu):
    """Rend l'individu immunisé"""
    ChangeEtat(id_individu, IMMUNISE)
    pop_cur.execute("UPDATE etat SET duree_etat = ? WHERE id_individu = ?", (DUREE[IMMUNISE], int(id_individu)))

def Neutre(id_individu):
    """Rend l'individu neutre, c'est à dire vulnérable mais non infecté"""
    ChangeEtat(id_individu, NEUTRE)
