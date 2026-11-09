"""
Modelo orientado a objetos da frota EcoFleet.

Veiculo é abstrata e guarda o que vans e bicicletas têm em comum. A bateria é
um atributo privado: só pode ser lida por get_autonomia_bateria() e alterada
por set_autonomia_bateria(), que valida o valor recebido.

Autor: Antonio Santos
"""

from abc import ABC, abstractmethod

try:
    # Equivalente ao @Override do Java (Python 3.12 ou mais recente)
    from typing import override
except ImportError:
    def override(metodo):
        return metodo

BATERIA_MINIMA = 0.0
BATERIA_MAXIMA = 100.0


class Veiculo(ABC):
    """Modelo geral de veículo. Não pode ser instanciado diretamente."""

    TIPO = ""
    ROTULO = ""
    TAXA_CONSUMO = 0.0   # pontos percentuais de bateria por km, definida em cada subclasse

    def __init__(self):
        # Atributos protegidos (convenção do Python: um sublinhado)
        self._id_veiculo = 0
        self._modelo = ""
        self._capacidade_carga = 0.0
        # Atributo privado (dois sublinhados): fora da classe só é acessível pelos métodos
        self.__autonomia_bateria = 0.0

    # ---- bateria ----

    def get_autonomia_bateria(self):
        return self.__autonomia_bateria

    def set_autonomia_bateria(self, bateria):
        """Fora da faixa de 0.0 a 100.0, o valor é inválido e a bateria fica em 0.0."""
        if bateria < BATERIA_MINIMA or bateria > BATERIA_MAXIMA:
            self.__autonomia_bateria = 0.0
        else:
            self.__autonomia_bateria = float(bateria)

    @abstractmethod
    def registrar_viagem(self, distancia):
        """Desconta da bateria o consumo da viagem, mostra o resultado no console e devolve o nível restante."""

    # ---- leitura dos demais dados ----

    @property
    def id_veiculo(self):
        return self._id_veiculo

    @property
    def modelo(self):
        return self._modelo

    @property
    def capacidade_carga(self):
        return self._capacidade_carga

    def autonomia_estimada_km(self):
        """Quantos km ainda dá para rodar com a bateria atual."""
        return self.get_autonomia_bateria() / self.TAXA_CONSUMO

    def detalhe(self):
        """Informação própria de cada tipo, para exibição."""
        return ""


class VanEletrica(Veiculo):
    """Van elétrica de carga: consome 0.5 ponto percentual por km."""

    TIPO = "van"
    ROTULO = "Van elétrica"
    TAXA_CONSUMO = 0.5

    def __init__(self, id_veiculo, modelo, capacidade_carga, autonomia_bateria, placa_identificacao):
        super().__init__()
        self._id_veiculo = id_veiculo
        self._modelo = modelo
        self._capacidade_carga = capacidade_carga
        self.set_autonomia_bateria(autonomia_bateria)
        self.__placa_identificacao = placa_identificacao

    @property
    def placa_identificacao(self):
        return self.__placa_identificacao

    @override
    def registrar_viagem(self, distancia):
        nova_bateria = self.get_autonomia_bateria() - distancia * self.TAXA_CONSUMO
        self.set_autonomia_bateria(nova_bateria)
        print(f"[{self.ROTULO}] Distância percorrida: {distancia:.1f} km | "
              f"Bateria restante: {self.get_autonomia_bateria():.1f}%")
        return self.get_autonomia_bateria()

    def detalhe(self):
        return f"Placa {self.__placa_identificacao}"


class BicicletaEletrica(Veiculo):
    """Bicicleta elétrica de entrega: consome 0.2 ponto percentual por km."""

    TIPO = "bicicleta"
    ROTULO = "Bicicleta elétrica"
    TAXA_CONSUMO = 0.2

    def __init__(self, id_veiculo, modelo, capacidade_carga, autonomia_bateria, limite_velocidade_assistida):
        super().__init__()
        self._id_veiculo = id_veiculo
        self._modelo = modelo
        self._capacidade_carga = capacidade_carga
        self.set_autonomia_bateria(autonomia_bateria)
        self.__limite_velocidade_assistida = limite_velocidade_assistida

    @property
    def limite_velocidade_assistida(self):
        return self.__limite_velocidade_assistida

    @override
    def registrar_viagem(self, distancia):
        nova_bateria = self.get_autonomia_bateria() - distancia * self.TAXA_CONSUMO
        self.set_autonomia_bateria(nova_bateria)
        print(f"[{self.ROTULO}] Distância percorrida: {distancia:.1f} km | "
              f"Bateria restante: {self.get_autonomia_bateria():.1f}%")
        return self.get_autonomia_bateria()

    def detalhe(self):
        return f"Assistência até {self.__limite_velocidade_assistida:g} km/h"


TIPOS = {classe.TIPO: classe for classe in (VanEletrica, BicicletaEletrica)}
