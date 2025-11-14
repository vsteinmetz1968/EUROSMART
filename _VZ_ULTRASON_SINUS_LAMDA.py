### Créé par JMT en septembre 2025
### =============================================================================
###
###   Acquisition de deux tensions ou de grandeurs physiques variables

###   Acquisition avec récupération de l'ensemble des mesures de la trame avec
###   utilisation de l'instruction LireAcq() du module sysam_campus_py
###
###   Explotation sous forme de tracé des graphes avec matplotlib (sommairement...)
###
###   IMPORTANT :
###       Les données ne sont disponibles qu'à la fin de l'acquisition, il convient donc
###       de ne pas utiliser cette instruction si l'acquisition est "un peu longue", car
###       il ne se passe rien de visuel.
###       Pour les acquisitions qui durent, voir les exemples _D_
###
###
### =============================================================================

import time
import sysam_campus_py as camp
import matplotlib.pyplot as plt
import numpy as np
import sys

from scipy.optimize import curve_fit

# La fonction suivante va être utilisée par curve_fit, qui va ajuster les paramètre a, b, c.
def cos_fitr(x, a , b , c):
    return a + b*np.cos(40000*2*3.14*x+ c)


print()
print()
print("Programme ENREGISTREUR avec SYSAM CAMPUS ET matplotlib   +++++++")
print()


### VERIFICATION DE LA PRESENCE DE LA CENTRALE SYSAM CAMPUS ======================

if camp.Presente():
    print("Vérification de la présence de la centrale SYSAM CAMPUS : Centrale CAMPUS connectée")
else:
    print("Vérification de la présence de la centrale SYSAM CAMPUS : Centrale CAMPUS non connectée, programme interrompu")
    camp.Rangement()
    exit()


print()

per   = 25e-6
### amplitude en V
ampl  = 5.0
### phase en rad
phase = 0  #np.pi/9

### Choix de la sortie à utiliser
SA = camp.SA1
### Nombre de Points Par Période ( ppp ) souhaité
nbppp = 20
### Remarque : réduire ce nombre à peu (par exemple 10 ou 15) permet de visualiser
### l'échantillonnage de l'émission ...



### temps d'échantillonnage correspondant
TeS = per / nbppp

freq  = 1 / per ### ne pas modifier la formule


print("Rappel des choix :")
print("Sortie Analogique utilisée : SA" + str(SA))
print("Période = ",   camp.fmt( per, 4))
print("Fréquence = ", camp.fmf( freq, 4))
print("Amplitude = ", camp.fmInge(ampl, 4 , 2)+ ' V')

print("Nombre de points par période souhaité = ", nbppp)
print("Temps d'échantillonnage de sortie correspondant = ", camp.fmt(TeS, 4))


def fcSin(t):
    global ampl
    global phase
    global per
    return ampl * np.sin( 2 * np.pi * t / per + phase);

def fcComplexe(t):
    global ampl
    global phase
    global per
    AmpH    = [1.00, 0.700]
    PhasesH = [0.00, np.pi/4]
    u1 = 0.0
    for i in range(len(AmpH)):
        u1 = u1 + AmpH[i] * np.sin((i + 1) * 2 * np.pi * t / per + PhasesH[i]);
    u1 = u1 * ampl
    return u1

def fcRampe(t):
    global ampl
    global phase
    global per
    u1 = ampl * t / per
    return u1


def fcTriangle(t):
    global per
    global ampl

    cd = ampl * 4
    pd = t/per - (t/per)//1
    if pd < 0.25 :
        u1 = cd * pd # OK
    elif pd > 0.75 :
        u1 = - 4 * ampl + cd * pd
    else:
        u1 = 2 * ampl  - cd * pd # OK
    return u1


def fcCampRomain(t):
    global per
    global ampl
    u1 = fcTriangle(t)
    if u1 > ampl/4:
        u1 = ampl/4 + 0.15 * (u1 - ampl/4)
    return u1



### On fixe les paramètres d'émission :
### nbppp valeurs à transmettre, correspondant à exactement une période du signal *)
camp.ParametreEmission( SA, per, nbppp);

### résultats après correction technique :
nbppp = camp.NbValSA[ SA - 1]
TeS   = camp.TeSA[ SA - 1]

print("Nombre de points par période retenu = ", nbppp)
print("Temps d'échantillonnage de sortie retenu = ", camp.fmt(TeS,4))

print(" 2. Remplissage du tableau")
for i in range( nbppp ):
    t = i * per / nbppp;
    ### choisir ici la fonction parmi les propositions
    u = fcSin(t)
    ### u = fcComplexe(t)
    ###u = fcRampe(t)
    ###u = fcTriangle(t)
    ###u = fcCampRomain(t) #
    ### Placement de la valeur u dans le tableau à la case i
    camp.PlaceValeur(SA, i, u);
### Remarque: on peut créer d'autres fonctions, mais il faut veiller
### à ce qu'elles soient périodiques de période per

print(" 3. Transmission des valeurs à SYSAM CAMPUS")
camp.TransmetValeurs  (SA);

print(" 4. Déclenchement de l'émission")
camp.DeclencheSA( SA);



print()
print()
print(" PARAMETRAGE DE L'ACQUISITION ")

camp.ActiveCanal ( camp.C1, camp.vdcTension, camp.cal10V)

### mettre cette ligne en commentaire si on ne veut qu'un seul canal actif (C1)
### ou adapter à un autre capteur...
camp.ActiveCanal ( camp.C3, camp.vdcTension, camp.cal10V) ### calibre 40 mA du capteur d'intensité


###  Tension sur canal 1
###  Capteur sur canal 3 (premier mode/calibre disponible )
canalR1 = camp.C1
camp.ActiveCanal (canalR1, camp.vdcTension, camp.cal10V)

### Capteur sur canal 3
canalR3 = camp.C3
# camp.ActiveCanal(canalR2, camp.vdcCapteur, 0)
camp.ActiveCanal (canalR3, camp.vdcTension, camp.cal10V)

print("Récapitulation: ")
print("Premier canal (C1):")
print("   Référence du capteur : ", camp.RefCapteur(canalR1))
print("   Nom du capteur : ", camp.NomCapteur(canalR1))
print("   Unité : ", camp.UniteGP(canalR1))


print("Second canal (C3) :")
print("   Référence du capteur : ", camp.RefCapteur(canalR3))
print("   Nom du capteur : ", camp.NomCapteur(canalR3))
print("   Unité : ", camp.UniteGP(canalR3))

### Réglage de la durée totale et du nombre de points à recueillir
### premier paramètre: durée totale d'acquisition souhaitée
### second paramètre: nombre de points à acquérir
### les valeurs résultant de cet appel ne sont pas forcément celles
### qu'on souhaite pour des raisons techniques.
### La philosophie est d'obtenir de valeurs aussi proches que celles qui sont souhaitée,
### avec une priorité à la durée totale par excès
camp.DureesEtPoints(100E-6, 200)
### Réglage du nombre de points des blocs
### Ce réglage doit être fait, même s'il n'a pas d'impact sur la récupération
### globale des données... ( camp.LireAcq() ci-dessous )
### ici: blocs de 10 points, mais on peut changer...
camp.NbPtsDansBloc(100)


#
# print("RAPPELS des choix (éventuellement corrigés) avant déclenchement ++++++++++++++++++")
# print(" Nombre de canaux actifs = ",    camp.nbCanauxActifs)
# print(" Nombre de points à acquérir  ", camp.NbPts)
# print(" Temps d'échantillonnage =  ",   camp.fmt(camp.Te, 4))
# print(" Nombre points dans le bloc d'acquisition ", camp.NbPtsBlocAcq)

### Exemple 1 : synchro sur C1
### Quelque peu aléatoire, pour voir le début de l'émission d'une salve
### en même temps que le début de la réception. il faut souvent
### Réglage de la syncro, sur la voie, 1
camp.DefModeDeclenchement(camp.mdSeuil) ### mdAucun ou mdSeuil ou mdExterne
camp.DefCanalSynchro(camp.C1)           ### Canal 1
camp.DefTauxPretrig(0) ### en %
camp.DefSensDeclSeuil(camp.sdMontant)
camp.DefSeuilDeclenchement(0.0) ### Synchronisation sur la valeur 1.5 V
#



plt.ion()
plt.figure()
for z in range (200):

    # print("ACQUSITION ET RECUPERATION ++++++++++++++++++++++++++++++++++++++++++");
    # print("Déclenchement")
    camp.DeclencheAcqMonocoup();

    # print("Récupération globale des mesures acquises")
    camp.LireAcq()

    # print("Arrêt de l'acquisition")
    camp.ArreteAcq()
    # print()


    # print("EXPLOITATION SOUS FORME DE GRAPHE MATPLOTLIB")

    ### Création du tableau des valeurs du temps (une valeur par point acquis)
    tabTemps = np.arange(camp.NbPts) * camp.Te

    ### propiétés générales du graphique
    # fig, ax_V1 = plt.subplots(figsize=(10, 8))
    # fig.suptitle('Acquisition ' + camp.NomGP(canalR1) + ' & ' + camp.NomGP(canalR2))
    # fig.figsize = (10, 16)

    coeffA, var_matrixA = curve_fit(cos_fitr, tabTemps  , (camp.gpM[canalR1]) )
    coeffB, var_matrixB = curve_fit(cos_fitr, tabTemps  , (camp.gpM[canalR3]) )
    if coeffA[1]<0:
        coeffA[2]+=3.14
    if coeffB[1]<0:
        coeffB[2]+=3.14
    Phi=coeffB[2]-coeffA[2]
    plt.title(str(Phi))
    ### avec ligne ; le paramètre 'g.-' signifie : couleur green, points et lignes (segments entre les points)
    ### ax_V1.plot(tabTemps, camp.gpM[canalR1], 'g.-', linewidth=1, markersize=1, label=camp.SymboleGP(canalR1) + " (" + camp.UniteGP(canalR1)+")")
    ### sans ligne, juste des points ; le paramètre 'g.' signifie : couleur green, points
    plt.plot(tabTemps, camp.gpM[canalR1],marker="o")
    if abs(Phi)>0.2:
        plt.plot(tabTemps, camp.gpM[canalR3],marker="+")
    else:
        plt.plot(tabTemps, camp.gpM[canalR3],marker="o", lw=10)
    plt.draw()
    plt.pause(0.01)
    plt.clf()

plt.ioff()


### fait apparaître la fenêtre

### Graphe final
plt.plot(tabTemps, camp.gpM[canalR1],marker="o")
plt.plot(tabTemps, camp.gpM[canalR3],marker="o")
plt.show(block=True)

print("Fermer la fenêtre pour terminer le programme")

### indispensable pour bien libérer les mémoires ...
camp.Rangement()

