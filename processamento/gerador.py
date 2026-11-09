"""
Gera um lote simulado de viagens, sempre igual (semente fixa).

Esta parte é imperativa de propósito: o sorteador guarda estado interno e cada
número depende do anterior, então o laço é sequencial. O lote produzido, porém,
é uma tupla imutável que o pipeline só lê.

Autor: Antonio Santos
"""

import random

from .dados import Categoria, Viagem

SEMENTE = 376


def gerar_lote(quantidade, semente=SEMENTE):
    sorteio = random.Random(semente)
    viagens = []
    for numero in range(1, quantidade + 1):
        categoria = Categoria.VAN if sorteio.random() < 0.3 else Categoria.BICICLETA
        distancia = round(sorteio.uniform(5.0, 120.0), 1)
        bateria = round(sorteio.uniform(40.0, 100.0), 1)
        viagens.append(Viagem(numero, categoria, distancia, bateria))
    return tuple(viagens)
