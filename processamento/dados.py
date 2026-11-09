"""
Tipos de dados do processamento em lote das viagens.

Todos são imutáveis: depois de criados, nenhum campo pode ser alterado. Quando
uma etapa precisa de um valor diferente, ela cria um objeto novo.

Autor: Antonio Santos
"""

from dataclasses import dataclass
from enum import Enum


class Categoria(Enum):
    """Tipo de veículo e a taxa de consumo, em pontos percentuais por km."""

    VAN = ("Van elétrica", 0.5)
    BICICLETA = ("Bicicleta elétrica", 0.2)

    def __init__(self, rotulo, taxa):
        self.rotulo = rotulo
        self.taxa = taxa


@dataclass(frozen=True)
class Viagem:
    """Dado de entrada: uma viagem registrada pela telemetria."""

    numero: int
    categoria: Categoria
    distancia: float         # km
    bateria_inicial: float   # %


@dataclass(frozen=True)
class ResultadoViagem:
    """Resultado do cálculo de uma viagem."""

    viagem: Viagem
    consumo: float
    bateria_final: float
    critica: bool


@dataclass(frozen=True)
class ResumoCategoria:
    """
    Totais de uma categoria.

    Os valores ficam em números inteiros (distância e consumo em centésimos) para
    que a soma seja exata em qualquer ordem. Com float, somar os mesmos números em
    ordens diferentes pode mudar a última casa decimal, e o resultado paralelo
    deixaria de bater com o sequencial.
    """

    categoria: Categoria
    viagens: int = 0
    distancia_centesimos: int = 0
    consumo_centesimos: int = 0
    alertas: int = 0

    @property
    def distancia(self):
        return self.distancia_centesimos / 100

    @property
    def consumo(self):
        return self.consumo_centesimos / 100
