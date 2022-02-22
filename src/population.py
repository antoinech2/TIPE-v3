""""Génère une population utilisée pour la simulation"""

#Objectif : recréer une population représentative de la population française par rapport à différents critères.

#Modules externes
import sqlite3
from random import random
import numpy as np
from scipy.spatial import distance
from sklearn.datasets import make_blobs

#Modules internes
from constantes import *

REGENERATE_POPULATION = True # Regénérer ou non une nouvelle population lors de l'éxécution de la simulation

database_loc_data = "res/simulation_data.db" #Chemin de la base de donnée qui contient les données réelle sur la répartition de la population, les probabilités d'hospitalisation et de décés, ainsi que l'efficacité des vaccins
database_loc_pop = "data/population.db" #Chemin de la base de donnée qui contient la liste des individus de la population générée, et les états infectieux

#Initialisation des bases de données et des curseurs
data_db = sqlite3.connect(database_loc_data)
pop_db = sqlite3.connect(database_loc_pop)
data_cur = data_db.cursor()
pop_cur = pop_db.cursor()

# Liste des maladies prises en compte
MALADIE_LISTE = ["obésité", "diabète", "dyslipidémies", "métabolique", "hypertension", "coronariennes", "artériopathie", "trouble cardiaque", "insuffisance cardiaque", "valvulopathies", "avc", "respiratoire", "mucoviscidose", "embolie", "cancer", "inflammatoire", "antidépresseur", "neuroleptique", "parkinson", "démence"]

class Population:
    """Représente une population d'individus"""
    def __init__(self, nb_individus, variance_pop, max_distance):
        if REGENERATE_POPULATION:
            self.generer_population(nb_individus) # Génère la population dans la base de donnée.

        pop_db.row_factory = sqlite3.Row
        pop_cur = pop_db.cursor()
        
        self.individus = [] # Liste qui contient les individus
        alldata = pop_cur.execute("SELECT * from population").fetchall()

        # Génération de la répartition spatiale de la population
        self.population_position, y = make_blobs(n_samples=nb_individus, centers=1, center_box=(0,0), cluster_std=variance_pop) #Génération des coordonées
        self.population_position = self.population_position.astype("float16")

        print("Attribution des voisins de chaque individu...")
        for id in range(nb_individus):
            if id % 1000 == 0:
                print(f"\tCalcul... {id}/{nb_individus} ({(id/nb_individus*100):.2f}%)", end = "\r")
            
            data = dict(alldata[id]) # On récupère les données concernant l'individu
            individu_distance = distance.cdist([self.population_position[id]], self.population_position) # Calcul des distance entre l'individu et les autres
            # On ne sauvegarde que la liste des individus proches, ainsi que la distance associée.
            voisins = np.where(individu_distance < max_distance)[1]
            voisins_valeur = np.extract(individu_distance < max_distance, individu_distance)
            # On ajoute l'individu généré à partir des données
            self.individus.append(Individu(data["id_individu"], data["age"], data["sexe"], data["activité"], self.calcul_risque_multiplicateur(data), list(zip(voisins, voisins_valeur))))

    def calcul_risque_multiplicateur(self, data):
        """"Calcule et renvoie les risques relatifs d'hospitalisation et de décès en fonction des données d'un individu"""
        # Risque relatif du à l'âge
        multiplicateur = np.array(data_cur.execute("SELECT probar_hopital, probar_deces from age WHERE min <= ? AND max >= ?", (data["age"], data["age"])).fetchall()[0])
        # Risque relatif du au sexe
        multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from repartition_sexe WHERE sexe = ?", (data["sexe"],)).fetchall()[0])
        # Risque relatif du aux quintiles sociales
        multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from social WHERE quintile = ?", (data["quintile"],)).fetchall()[0])
        # Risque relatif du aux habitudes de vie (tabac et alcool)
        if data["tabac"]:
            multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from habitudes WHERE carac = 'tabac'").fetchall()[0])
        if data["alcool"]:
            multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from habitudes WHERE carac = 'alcool'").fetchall()[0])
        # Risque relatif du à chaque maladie
        for maladie in MALADIE_LISTE:
            if data[maladie]:
                multiplicateur *= np.array(data_cur.execute("SELECT probar_hopital, probar_deces from maladie WHERE nom = ?", (maladie, )).fetchall()[0])
        return multiplicateur[0], multiplicateur[1] # On renvoie le tuple multiplicateur (hospitalisation, décès)

    def generer_population(self, nb_population):
        """Génère la population dans la base de donnée"""
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

        #On récupère la répartition des âges dans la base de donnée
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
        # Récupération et attribution du sexe des individus
        proportion_homme = data_cur.execute("SELECT proportion FROM repartition_sexe WHERE sexe = 'homme'").fetchall()[0][0]
        pop_cur.execute("UPDATE population SET sexe = 'homme' WHERE id_individu IN (SELECT id_individu FROM population ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population) * ?))", (proportion_homme, ))
        pop_db.commit()

        print("Attribution des quintiles sociales...")
        # Récupération et attribution des quintiles sociales des individus
        quintiles_prop = data_cur.execute("SELECT quintile, proportion FROM social").fetchall()
        for quintile in quintiles_prop:
            pop_cur.execute("UPDATE population SET quintile = ? WHERE id_individu IN (SELECT id_individu FROM population WHERE quintile IS NULL ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population) * ?))", (quintile[0], quintile[1]))
        pop_db.commit()

        print("Attribution des habitudes de vie...")
        # Récupération et attribution des habitudes de vie des individus
        habitudes_prop = data_cur.execute("SELECT carac, proportion FROM habitudes").fetchall()
        prop_15_ans = data_cur.execute("SELECT SUM(proportion) FROM age_detail WHERE age >= 15").fetchall()[0][0]
        for habitude in habitudes_prop:
            prop_ponderee = habitude[1]/prop_15_ans # On pondère la proportion pour n'appliquer les habitudes de vie seulement aux plus de 15 ans
            pop_cur.execute("UPDATE population SET {} = 1 WHERE id_individu IN (SELECT id_individu FROM population WHERE age >= 15 ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population WHERE age >= 15) * ?))".format(habitude[0]), (prop_ponderee, ))
        pop_db.commit()

        print("Attribution de la présence de maladies...")
        # On récupère chaque tranche d'âge avec la proportion de personnes qui ont une maladie chronique
        moyenne_proportion_age = data_cur.execute("SELECT AVG(proportion) FROM repartition_maladie").fetchall()[0][0]
        nb_maladie = len(MALADIE_LISTE)

        # On boucle sur toutes les maladie, avec leur proportion dans la population
        for (avancement, (maladie, proportion_maladie)) in enumerate(data_cur.execute("SELECT nom, proportion FROM maladie").fetchall()):
            print(f"\tAttribution de la maladie {avancement+1}/{nb_maladie} ({(avancement+1/nb_maladie*100):.2f}%) ('{maladie}')", end = "\r")
            
            # On boucle sur les individus
            for (avancement_pop, (id_individu, age)) in enumerate(pop_cur.execute("SELECT id_individu,age FROM population").fetchall()):
                if avancement_pop % 5000 == 0:
                    print(f"\t\tAttribution de la maladie {avancement_pop+1}/{nb_population} ({(avancement_pop+1/nb_population*100):.2f}%)", end="\r")
                
                proportion_age = data_cur.execute("SELECT proportion FROM repartition_maladie WHERE min <= ? AND max >= ?", (age, age)).fetchall()[0][0]
                # On attribue aléatoirement la maladie à l'individu en fonction de la probabilité pondérée par la répartition selon l'âge
                if random() < proportion_maladie*proportion_age/moyenne_proportion_age:
                    pop_cur.execute("UPDATE population SET '{}' = 1 WHERE id_individu = ?".format(maladie), (id_individu, ))
        pop_db.commit()

        print("\033[KAttribution de l'emploi...")
        # On récupère et attribue une catégorie d'activité professionnelle aux individus en fonction de l'âge et du sexe
        pop_cur.execute("UPDATE population SET activité = 'études' WHERE age >= 3 AND age < 15")
        # On boucle sur chaque groupe d'âge de la répartition des secteurs d'activité
        for (age_min, age_max, sexe, proportion_emploi) in data_cur.execute("SELECT * FROM repartition_emploi").fetchall():
            # On boucle sur chaque cesteur d'activité pour attribuer l'activité en fonction de sa proportion
            for (secteur, proportion_sexe, proportion_age) in data_cur.execute("SELECT emploi_sexe.secteur, emploi_sexe.proportion, emploi_age.proportion FROM emploi_age JOIN emploi_sexe ON emploi_sexe.secteur = emploi_age.secteur WHERE sexe = ? AND min <= ? AND max >= ?", (sexe, age_min, age_max)).fetchall():
                pop_cur.execute("UPDATE population SET activité = ? WHERE id_individu IN (SELECT id_individu FROM population WHERE sexe = ? AND age <= ? AND age >= ? AND activité IS NULL ORDER BY RANDOM() LIMIT ROUND ((SELECT COUNT(id_individu) FROM population WHERE sexe = ? AND age <= ? AND age >= ?) * ?))", (secteur, sexe, age_max, age_min,sexe, age_max, age_min, proportion_emploi*proportion_age*proportion_sexe))
        pop_db.commit()

        print("\033[92mPopulation générée !\033[0m")

    def get_individu(self, id):
        """Renvoie un individu à partir de son identifiant"""
        return self.individus[id-1]

    def get_nombre_vaccination(self, jour_vaccination):
        """Renvoie le nombre de personnes à vacciner selon chaque vaccin en fonction du jour de vaccination"""
        return data_cur.execute("SELECT vaccin, doses from doses_vaccination WHERE jour = ?", (jour_vaccination, )).fetchall()

def close_database():
    """Ferme les curseurs et les connexions aux bases de données"""
    pop_cur.close()
    pop_db.close()
    data_cur.close()
    data_db.close()

class Individu:
    """Représente un individu et ses caractéristiques"""
    def __init__(self, id, age, sexe, activite, multiplicateur, liste_voisins):
        # Caractéristiques de l'individu
        self.id = id
        self.age = age
        self.sexe = sexe
        self.activite = activite
        self.multiplicateur = multiplicateur
        self.voisins = liste_voisins

        # Etat de santé et d'infection
        self.sante = NEUTRE
        self.infection = NEUTRE
        self.sante_duree = None
        self.infection_duree = None

        # Etat de vaccination
        self.vaccin_type = None
        self.vaccin_date = None

        # Etat d'immunité suite à une infection
        self.infection_immunite_date = None

    def infecter(self, duree):
        """Infecte l'individu"""
        self.sante = INFECTE
        self.sante_duree = duree

    def hospitaliser(self, duree):
        """Hospitalise d'individu"""
        self.sante = INFECTE
        self.infection = HOSPITALISE
        self.sante_duree = None
        self.infection_duree = duree

    def guerir(self, jour):
        """Guérit l'individu suite à une infection"""
        self.sante = NEUTRE
        self.sante_duree = None
        self.infection = NEUTRE
        self.infection_duree = None
        self.infection_immunite_date = jour

    def deces(self):
        """Rend l'individu décédé suite à une hospitalisation"""
        self.sante = DECEDE
        self.sante_duree = None
        self.infection_duree = None

    def vacciner(self, vaccin_type, jour):
        """Vaccine l'individu avec un vaccin spécifié"""
        self.vaccin_type = vaccin_type
        self.vaccin_date = jour

    def get_immunite(self, jour, type):
        """Renvoie l'immunité de l'individu en fonction du type de risque"""
        if type == INFECTION:
            multiplicateur = 1
        # Dans le cas d'une hospitalisation ou d'un décès, on se base sur le risque établi en fonction des caractéristiques de l'individu
        elif type == HOSPITALISATION:
            multiplicateur = self.multiplicateur[0]
        elif type == DECES:
            multiplicateur = self.multiplicateur[1]
        
        if self.vaccin_type is not None: # Immunité due au vaccin
            mois_vaccin = (jour - self.vaccin_date)/30.5
            if mois_vaccin <= 12:
                # On récupère l'efficacité de la vaccination en fonction du vaccin et de la durée depuis la vaccination
                multiplicateur *= (1-data_cur.execute("SELECT efficacite from vaccins WHERE vaccin = ? AND age_min <= ? AND age_max >= ? AND mois_min <= ? AND mois_max >= ? AND etat = ?", (self.vaccin_type, self.age, self.age, mois_vaccin, mois_vaccin, type)).fetchall()[0][0])
        
        elif self.infection_immunite_date is not None: #Immunité due à une infection
            mois_vaccin = (jour - self.infection_immunite_date)/30.5
            result = (1-data_cur.execute("SELECT efficacite from vaccins WHERE vaccin = ? AND age_min <= ? AND age_max >= ? AND mois_min <= ? AND mois_max >= ? AND etat = ?", ("Infection", self.age, self.age, mois_vaccin, mois_vaccin, type)).fetchall()[0][0])
            multiplicateur *= result
        return multiplicateur
