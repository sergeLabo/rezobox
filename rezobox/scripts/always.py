#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

########################################################################
# This file is part of rezobox.
#
# rezobox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rezobox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
########################################################################

"""
Lancé à chaque frame durant tout le jeu.
"""

import sys
from time import time

import numpy as np
import cv2
    
from bge import logic as gl
import scripts.blendergetobject


def droiteAffine(x1, y1, x2, y2):
    """
    Retourne les valeurs de a et b de y=ax+b
    à partir des coordonnées de 2 points.
    """

    a = (y2 - y1) / (x2 - x1)
    b = y1 - (a * x1)
    return a, b

# 0 à 20 => 1.55, 94 => -1.5
A, B = droiteAffine(20, 1.55, 94, -1.48)
print(A, B)

def get_server_message():
    # 0.050 s
    t0 = time()
    gl.clt.re_connect_sock()
    try:
        data = gl.clt.listen(16384)
        print("\nMessage reçu: taille =", str(sys.getsizeof(data)))
        # Prends beucoup trop de temps
        #gl.clt.clear_buffer(16384)
    except:
        data = None
        print("Pas de réception sur le client TCP")
    print("    en {0:.2f} seconde".format(time() - t0))
    print("Durée d' un cycle = {0:.2f} seconde".format(time() - gl.tzero))
    print("    soit un FPS de {0:.0f}".format(51/(time() - gl.tzero)))
    gl.tzero = time()
    return data

def get_image(data):
    h, w = gl.y, gl.x
    nparray = np.fromstring(data, np.uint8)
    
    print("Taille du array de l'image reçue:", nparray.size)
    print("x =", gl.x, "y =", gl.y, "x*y =", gl.y*gl.x)
    
    if nparray.size == gl.size:
        image = nparray.reshape(h, w)
    else:
        image = gl.image
    return image

def add_object(obj, position, life, all_obj, game_scn):
    """
    Ajoute obj à la place de Empty
    position liste de 3
    
    addObject(object, reference, time=0)
    Adds an object to the scene like the Add Object Actuator would.
    Parameters:	
        object (KX_GameObject or string) – The (name of the) object to add.
        reference (KX_GameObject or string) – The (name of the) object which
        position, orientation, and scale to copy (optional), if the object
        to add is a light and there is not reference the light’s layer will be
        the same that the active layer in the blender scene.
        time (integer) – The lifetime of the added object, in frames. A time
        of 0 means the object will last forever (optional).

    Returns: The newly added object.
    Return type: KX_GameObject
    """
    empty = all_obj['Empty']
    empty.worldPosition = position
    game_scn.addObject(obj, empty, life)
    
def hide_tampon(all_obj):
    all_obj["tampon"].visible = False

def add_one_row_planes(image, row, all_obj, game_scn):
    """
        Ajout les plans d'une image de 1 colonne en position x = row
        largeur du box = 11
        un plan = 11/100 = 0,110

    """
    lp = gl.largeur_plan
    
    for h in range(gl.y):
        # plan de coté = pas de 11/128 = 0,0859375, 96*0,0859375=8.25

        # row de 0 à 63 ( row pas + demi pas - demi hauteur de box )
        x = row*lp + lp/2 - 5.5

        # -( h pas + demi pas - demi hauteur de box )
        y = - (h*lp + lp/2 - 4.125)
                
        # image[h][0] de 0 à 94
        p = image[h][0]

        # 0 à 20 => 1.55, 94 => -1.5
        if p <= 20:
            z = 1.55
        else:
            a, b = -0.04094, 2.3689
            z = a * p + b
  
        # Ajout
        add_object("Plane", (x, y, z), gl.life, all_obj, game_scn)

def add_planes():
    """ Ajout des plans par 2 colonnes
    """
    # nombre de colonne par frame = 2
    ncpf = 2
    
    # Compte de 0 à 50 compris, 51 repasse à 0
    cycle = gl.tempoDict["cycle"].tempo
    
    # cycle = 0 récup réseau, puis de 1 à 50 et row de 0 à 99, gl.cycle=50
    for row in range(1, 100, 2):
        # row = 98 0 2 4 6 .... 96 98 0 2 
        # tempo = 0 1 2 ........50
        row -= 1
        if 2*cycle == row and gl.image is not None:
            
            all_obj = scripts.blendergetobject.get_all_objects()
            game_scn = scripts.blendergetobject.get_scene_with_name('Labomedia')
            
            # Tranche verticale d'image de 1 colonne
            image_parts = gl.image[0:gl.y, row:row+1]
            # ajout de la colonne
            add_one_row_planes(image_parts, row, all_obj, game_scn)
            
            # Tranche verticale d'image de 1 colonne
            image_parts = gl.image[0:gl.y, row+1:row+2]
            # ajout de la colonne
            add_one_row_planes(image_parts, row+1, all_obj, game_scn)

def main():
    """
    frame 0 update réseau
    frame 1 à 65 affichage des 64 rows
    """
    # Update des tempo
    gl.tempoDict.update()
    
    if gl.tempoDict["cycle"].tempo == 0:
        
        print("Update game with data server")
        data = get_server_message()
        
        if data:
            gl.image = get_image(data)

    # Ajout des plans pour cycle de 1 à 50 compris
    add_planes()

    # Effacement du tampon au début
    if gl.tempoDict["360"].tempo == 60:
        all_obj = scripts.blendergetobject.get_all_objects()
        #hide_tampon(all_obj)
