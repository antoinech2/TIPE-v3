#Fichier pour générer la population
#Objectif : recréer une population représentative de la France par rapport à différents critères.

#Modules externes
import sqlite3
from random import random

import numpy as np
from scipy.spatial import distance
from sklearn.datasets import make_blobs

#Modules internes
from constantes import *

REGENERATE_POPULATION = True

database_loc_data = "../res/simulation_data.db" #Chemin de la BDD qui contient les informations de génération de la population
database_loc_pop = "../data/population.db" #Chemin de la BDD qui contient la liste des individus, et les états infectieux

#Initialisation des BDD et des curseurs
data_db = sqlite3.connect(database_loc_data)
pop_db = sqlite3.connect(database_loc_pop)
data_cur = data_db.cursor()
pop_cur = pop_db.cursor()

maladie_liste = ["obésité", "diabète", "dyslipidémies", "métabolique", "hypertension", "coronariennes", "artériopathie", "trouble cardiaque", "insuffisance cardiaque", "valvulopathies", "avc", "respiratoire", "mucoviscidose", "embolie", "cancer", "inflammatoire", "antidépresseur", "neuroleptique", "parkinson", "démence"]

class Population:
    def __init__(self, nb_individus, variance_pop, max_distance):
        if REGENERATE_POPULATION:
            self.generer_population(nb_individus)
        pop_db.row_factory = sqlite3.Row
        pop_cur = pop_db.cursor()
        self.individus = []
        alldata = pop_cur.execute("SELECT * from population").fetchall()

        self.population_position, y = make_blobs(n_samples=nb_individus, centers=1, center_box=(0,0), cluster_std=variance_pop) #Génération des coordonées
        self.population_position = self.population_position.astype("float16")

        print("Attribution des voisins de chaque individu...")
        for id in range(nb_individus):
            if id % 1000 == 0:
                print(f"\tCalcul... {id}/{nb_individus} ({(id/nb_individus*100):.2f}%)", end = "\r")
            
            data = dict(alldata[id])
            individu_distance = distance.cdist([self.population_position[id]], self.population_position)
            voisins = np.where(individu_distance < max_distance)[1]
            voisins_valeur = np.extract(individu_distance < max_distance, individu_distance)
            self.individus.append(Individu(data["id_individu"], data["age"], data["sexe"], data["activité"], self.calcul_risque_multiplicateur(data), list(zip(voisins, voisins_valeur))))

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

    def generer_population(self, nb_population):
        """Génère la population en complétant la BDD"""
        print("Génération de la population...")

        pop_cur.execute("DROP TABLE population")
        pop_cur.execute('CREATE TABLE IF NOT EXISTS "population" ("id_individu" INTEGER NOT NULL,"age" INTEGER,\
        "sexe" TEXT NOT NULL DEFAULT "femme", "activité" TEXT, "quintile" INTEGER,"tabac" INTEGER NOT NULL DEFAULT 0,"alcool" INTEGER NOT NULL DEFAULT 0,\
        "obésité" INTEGER NOT NULL DEFAULT 0,"diabète" INTEGER NOT NULL DEFAULT 0,"dyslipidémies" INTEGER NOT NULL DEFAULT 0,\
        "métabolique" INTEGER NOT NULL DEFAULT 0,"hypertension" INTEGER NOT NULL DEFAULT 0,"coronariennes" INTEGER NOT NULL DEFAULT 0,\
        "artériopathie" INTEGER NOT NULL DEFAULT 0,"trouble cardiaque" INTEGER NOT NULL DEFAULT 0,"insuffisance cardiaque" INTEGER NOT NULL DEFAULT 0,\
        "valvulopathies" INTEGER NOT NULL DEFAULT 0,"avc" INTEGER NOT NULL DEFAULT 0,"respiratoire" INTEGER NOT NULL DEFAULT 0,\
        "mucoviscidose" INTEGER NOT NULL DEFAULT 0,"embolie" INTEGER NOT NULL DEFAULT 0,"cancer" INTEGER NOT NULL DEFAULT 0,\
        "inflammatoire" INTEGER NOT NULL DEFAULT 0,"antidépresseur" INTEGER NOT NULL DEFAULT 0,"neuroleptique" INTEGER NOT NULL DEFAULT 0,\
        "parkinson" INTEGER NOT NULL DEFAULT 0,"démence" INTEGER NOT NULL DEFAULT 0,PRIMARY KEY("id_individu" AUTOINCREMENT))')
        pop_db.commit()

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
        pop_db.commit()

        print("\033[KAttribution du sexe...")
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

        print("Attribution de la présence de maladies...")
        #MALADIES CHRONIQUES
        # On récupère chaque tranche d'âge avec la proportion de personnes qui ont une maladie chronique
        moyenne_proportion_age = data_cur.execute("SELECT AVG(proportion) FROM repartition_maladie").fetchall()[0][0]
        nb_maladie = data_cur.execute("SELECT COUNT(nom) FROM maladie").fetchall()[0][0]
        avancement = 0
        for (maladie, proportion_maladie) in data_cur.execute("SELECT nom, proportion FROM maladie").fetchall():
            avancement += 1
            print(f"\tAttribution de la maladie {avancement}/{nb_maladie} ({(avancement/nb_maladie*100):.2f}%) ('{maladie}')", end = "\r")
            avancement_pop = 0
            for (id_individu, age) in pop_cur.execute("SELECT id_individu,age FROM population").fetchall():
                avancement_pop += 1
                if avancement_pop % 5000 == 0:
                    print(f"\t\tAttribution de la maladie {avancement_pop}/{nb_population} ({(avancement_pop/nb_population*100):.2f}%)", end="\r")
                proportion_age = data_cur.execute("SELECT proportion FROM repartition_maladie WHERE min <= ? AND max >= ?", (age, age)).fetchall()[0][0]
                if random() < proportion_maladie*proportion_age/moyenne_proportion_age:
                    pop_cur.execute("UPDATE population SET '{}' = 1 WHERE id_individu = ?".format(maladie), (id_individu, ))
        pop_db.commit()

        print("\033[KAttribution de l'emploi...")
        pop_cur.execute("UPDATE population SET activité = 'études' WHERE age >= 3 AND age < 15")
        for (age_min, age_max, sexe, proportion_emploi) in data_cur.execute("SELECT * FROM repartition_emploi").fetchall():
            for (secteur, proportion_sexe, proportion_age) in data_cur.execute("SELECT emploi_sexe.secteur, emploi_sexe.proportion, emploi_age.proportion FROM emploi_age JOIN emploi_sexe ON emploi_sexe.secteur = emploi_age.secteur WHERE sexe = ? AND min <= ? AND max >= ?", (sexe, age_min, age_max)).fetchall():
                pop_cur.execute("UPDATE population SET activité = ? WHERE id_individu IN (SELECT id_individu FROM population WHERE sexe = ? AND age <= ? AND age >= ? AND activité IS NULL ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population WHERE sexe = ? AND age <= ? AND age >= ?) * ?))", (secteur, sexe, age_max, age_min,sexe, age_max, age_min, proportion_emploi*proportion_age*proportion_sexe))
        pop_db.commit()

        print("\033[92mPopulation générée !\033[0m")

    def get_distance(self, individu_1, individu_2):
        return self.individus_distance[individu_1.id-1][individu_2.id-1]

    def get_individu(self, id):
        return self.individus[id-1]

def close_database():
    """Ferme les curseur et les BDD"""
    pop_cur.close()
    pop_db.close()
    data_cur.close()
    data_db.close()

class Individu:
    def __init__(self, id, age, sexe, activite, multiplicateur, liste_voisins):
        # Caractéristiques
        self.id = id
        self.age = age
        self.sexe = sexe
        self.activite = activite
        self.multiplicateur = multiplicateur
        self.voisins = liste_voisins

        # Etat de santé
        self.sante = NEUTRE
        self.infection = NEUTRE
        self.sante_duree = None
        self.infection_duree = None

        self.vaccin_type = None
        self.vaccin_date = None

        self.infection_immunite_date = None

    def infecter(self, duree):
        self.sante = INFECTE
        self.sante_duree = duree

    def hospitaliser(self, duree):
        self.sante = INFECTE
        self.infection = HOSPITALISE
        self.sante_duree = None
        self.infection_duree = duree

    def guerir(self, jour):
        self.sante = NEUTRE
        self.sante_duree = None
        self.infection = NEUTRE
        self.infection_duree = None
        self.infection_immunite_date = jour

    def deces(self):
        self.sante = DECEDE
        self.sante_duree = None
        self.infection_duree = None

    def get_immunite(self, jour, type):
        if type == INFECTION:
            multiplicateur = 1
        elif type == HOSPITALISATION:
            multiplicateur = self.multiplicateur[0]
        elif type == DECES:
            multiplicateur = self.multiplicateur[1]
        if self.vaccin_type is not None:
            mois_vaccin = (jour - self.vaccin_date)/30.5
            multiplicateur *= (1-data_cur.execute("SELECT efficacite from vaccins WHERE vaccin = ? AND age_min <= ? AND age_max >= ? AND mois_min <= ? AND mois_max >= ? AND etat = ?", (self.vaccin_type, self.age, self.age, mois_vaccin, mois_vaccin, type)).fetchall()[0][0])
        elif self.infection_immunite_date is not None:
            mois_vaccin = (jour - self.infection_immunite_date)/30.5
            result = (1-data_cur.execute("SELECT efficacite from vaccins WHERE vaccin = ? AND age_min <= ? AND age_max >= ? AND mois_min <= ? AND mois_max >= ? AND etat = ?", ("Infection", self.age, self.age, mois_vaccin, mois_vaccin, type)).fetchall()[0][0])
            multiplicateur *= result
        return multiplicateur
