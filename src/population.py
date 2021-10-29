#Fichier pour générer la population
#Objectif : recréer une population représentative de la France par rapport à différents critères.

#Modules internes
from constants import *

#Modules externes
import sqlite3
import numpy as np
from sklearn.datasets import make_blobs
from scipy.spatial import distance

DESTROY_TABLE = True #Mettre à True pour regénérer une nouvelle population à chaque nouvelle exécution
CLEAN_TABLE = False
REGENERATE_AGE = True
REGENERATE_POSITION = True
REGENERATE_MALADIE = True

database_loc_data = "../data/population_data.db" #Chemin de la BDD qui contient les informations de génération de la population
database_loc_pop = "../data/population.db" #Chemin de la BDD qui contient la liste des individus, et les états infectieux

nb_population = 1000 #Nombre d'individus de la simulation
variance_pop = 1  # recommandé : 1

#Initialisation des BDD et des curseurs
data_db = sqlite3.connect(database_loc_data)
pop_db = sqlite3.connect(database_loc_pop)
data_cur = data_db.cursor()
pop_cur = pop_db.cursor()

def GeneratePopulation():
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
    pop_cur.execute('CREATE TABLE IF NOT EXISTS "population" (	"id_individu"	INTEGER NOT NULL, "x_coord" REAL, "y_coord" REAL, "age"	INTEGER NOT NULL,	"maladie_chronique"	INTEGER NOT NULL DEFAULT 0,	PRIMARY KEY("id_individu" AUTOINCREMENT))')
    pop_cur.execute('CREATE TABLE IF NOT EXISTS "etat" ("id_individu" INTEGER NOT NULL, "etat" INTEGER NOT NULL DEFAULT {} , "duree_etat" INTEGER DEFAULT NULL, "phase_vaccin" INTEGER NOT NULL DEFAULT 0, "id_vaccin" INTEGER DEFAULT NULL, PRIMARY KEY("id_individu" AUTOINCREMENT))'.format(NEUTRE))
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
        nb_age = data_cur.execute("SELECT COUNT(age) FROM age").fetchall()[0][0]
        for age in range(nb_age): #On boucle sur tous les âges à attribuer
            #On calcule le nombre d'individu à attribuer cet âge en fonction de la proportion de cet âge dans la population
            if age == 100:
                nb_individu_age = nb_population - pop_cur.execute("SELECT COUNT(id_individu) FROM population").fetchall()[0][0]
            else:
                nb_individu_age = round(data_cur.execute("SELECT proportion FROM age WHERE age = ?", (age,)).fetchall()[0][0] * nb_population)
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

    if REGENERATE_MALADIE:
        print("Attribution de la présence de maladies chroniques...")
        #MALADIES CHRONIQUES
        # On récupère chaque tranche d'âge avec la proportion de personnes qui ont une maladie chronique
        for (age_min, age_max, proportion) in data_cur.execute("SELECT * FROM maladie_chronique").fetchall():
            #On attribut aléatoirement la bonne proportion de maladie pour chaque âge
            pop_cur.execute("UPDATE population SET maladie_chronique = True WHERE id_individu IN (SELECT id_individu FROM population WHERE age >= ? AND age <= ? ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population WHERE age >= ? AND age <= ?) * ?))", (age_min, age_max, age_min, age_max, proportion))
        pop_db.commit()
    else:
        print("Réutilisation des données de maladies de la simulation précédente")


    print("Population générée !")

def CloseDB():
    """Ferme les curseur et les BDD"""
    pop_cur.close()
    pop_db.close()
    data_cur.close()
    data_db.close()

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

def GetListDureeEtat():
    """Renvoie la liste des individus qui ont un état à durée définie, leur état et la durée restante associée"""
    return np.array(pop_cur.execute("SELECT id_individu, etat, duree_etat FROM etat WHERE duree_etat NOT NULL").fetchall())

def GetAllVoisins(min_distance):
    """Retourne la liste des couples d'infecté/sain qui sont suceptibles d'intéragir (propagation possible)"""
    #return np.array(pop_cur.execute("SELECT infectep.id_individu, sainp.id_individu FROM population AS infectep JOIN etat AS infectee ON infectep.id_individu = infectee.id_individu, population AS sainp JOIN etat AS saine ON sainp.id_individu = saine.id_individu WHERE saine.etat = ? AND infectee.etat = ? AND (SELECT distance FROM distance WHERE id_1 = sainp.id_individu AND id_2 = infectee.id_individu) <= ?", (NEUTRE, INFECTE, min_distance)).fetchall())
    return np.array(pop_cur.execute("SELECT id_1, id_2 FROM distance JOIN etat AS etat_1 ON etat_1.id_individu = id_1 JOIN etat AS etat_2 ON etat_2.id_individu = id_2 WHERE etat_1.etat = ? AND etat_2.etat = ? AND distance <= ?", (NEUTRE, INFECTE, min_distance)).fetchall())

def GetPosition(id_individu):
    """Retourne les coordonnées de l'individu"""
    return np.array(pop_cur.execute("SELECT x_coord, y_coord FROM population WHERE id_individu = ?", (id_individu,)).fetchall())[0]

#Setter

def Infect(id_individu):
    """Infecte un individu et défini son temps d'infection"""
    ChangeEtat(id_individu, INFECTE)
    pop_cur.execute("UPDATE etat SET duree_etat = ? WHERE id_individu = ?", (DUREE[INFECTE], int(id_individu)))

def ReduceDureeEtat(id_individu):
    """Réduit d'un jour la durée restante de l'état d'un individu"""
    pop_cur.execute("UPDATE etat SET duree_etat = duree_etat - 1 WHERE id_individu = ?", (int(id_individu), ))

def ChangeEtat(id_individu, new_etat):
    """Change l'état d'un individu"""
    pop_cur.execute("UPDATE etat SET etat = ?, duree_etat = NULL WHERE id_individu = ?", (new_etat, int(id_individu)))

def Mort(id_individu):
    """Tue l'individu"""
    ChangeEtat(id_individu, MORT)

def Immunite(id_individu):
    """Rend l'individu immunisé"""
    ChangeEtat(id_individu, IMMUNISE)
    pop_cur.execute("UPDATE etat SET duree_etat = ? WHERE id_individu = ?", (DUREE[IMMUNISE], int(id_individu)))

def Neutre(id_individu):
    """Rend l'individu neutre, c'est à dire vulnérable mais non infecté"""
    ChangeEtat(id_individu, NEUTRE)
