"""
Operações do sistema: valida o que o usuário digitou, aplica as regras usando
as classes do modelo e grava o resultado.

Autor: Antonio Santos
"""

import math
import re
from dataclasses import dataclass, field
from functools import reduce

from .modelo import BATERIA_MAXIMA, BATERIA_MINIMA, TIPOS, VanEletrica
from .repositorio import Repositorio

LIMITE_CRITICO = 20.0          # abaixo disto a bateria é considerada crítica
DISTANCIA_MAXIMA = 1000.0      # maior viagem aceita em um único registro (km)
PLACA_ANTIGA = re.compile(r"^[A-Z]{3}[0-9]{4}$")             # ABC-1234
PLACA_MERCOSUL = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")  # ABC1D23


class ErroValidacao(Exception):
    """Dado informado pelo usuário que não pode ser aceito."""


def normalizar_placa(texto):
    """
    Aceita a placa no formato antigo (3 letras e 4 números, ABC-1234) ou no
    Mercosul (3 letras, número, letra e 2 números, ABC1D23), com ou sem hífen,
    espaço e em letras minúsculas. Devolve a placa padronizada: a antiga com
    hífen e a Mercosul sem hífen, como aparecem nas placas dos veículos.
    """
    placa = str(texto).strip().upper().replace("-", "").replace(" ", "")
    if PLACA_ANTIGA.match(placa):
        return f"{placa[:3]}-{placa[3:]}"
    if PLACA_MERCOSUL.match(placa):
        return placa
    raise ErroValidacao("Placa inválida. Use o formato antigo (ABC-1234) ou o Mercosul (ABC1D23).")


@dataclass
class Resultado:
    """Mensagem principal da operação e avisos para o usuário."""
    mensagem: str
    avisos: list = field(default_factory=list)


def br(valor):
    """Número com uma casa decimal e vírgula, como o usuário digita: 75,0"""
    return f"{valor:.1f}".replace(".", ",")


def bateria_critica(nivel):
    return nivel < LIMITE_CRITICO


# ---------- conversão e validação das entradas ----------

def _numero(texto, campo):
    texto = str(texto).strip().replace(",", ".")
    if not texto:
        raise ErroValidacao(f"Informe {campo}.")
    try:
        valor = float(texto)
    except ValueError:
        raise ErroValidacao(f"{campo.capitalize()} deve ser um número.") from None
    # float() aceita "nan" e "inf"; o NaN escaparia da validação da bateria
    if not math.isfinite(valor):
        raise ErroValidacao(f"{campo.capitalize()} deve ser um número.")
    return valor


def _inteiro_positivo(texto, campo):
    try:
        valor = int(str(texto).strip())
    except ValueError:
        raise ErroValidacao(f"{campo.capitalize()} inválido.") from None
    if valor <= 0:
        raise ErroValidacao(f"{campo.capitalize()} inválido.")
    return valor


class SistemaTelemetria:

    def __init__(self, caminho_banco):
        self.caminho_banco = caminho_banco

    def _repositorio(self):
        return Repositorio(self.caminho_banco)

    def _veiculo(self, repo, veiculo_id):
        veiculo = repo.buscar_veiculo(_inteiro_positivo(veiculo_id, "veículo"))
        if veiculo is None:
            raise ErroValidacao("Veículo não encontrado.")
        return veiculo

    # ---------- veículos ----------

    def cadastrar_veiculo(self, tipo, modelo, capacidade, bateria, placa="", limite=""):
        if tipo not in TIPOS:
            raise ErroValidacao("Escolha o tipo de veículo.")
        modelo = str(modelo).strip()
        if not modelo:
            raise ErroValidacao("Informe o modelo do veículo.")
        if len(modelo) > 60:
            raise ErroValidacao("O modelo deve ter no máximo 60 caracteres.")
        capacidade = _numero(capacidade, "a capacidade de carga")
        if capacidade < 0:
            raise ErroValidacao("A capacidade de carga não pode ser negativa.")
        bateria_informada = _numero(bateria, "o nível de bateria")

        if TIPOS[tipo] is VanEletrica:
            extra = normalizar_placa(placa)
        else:
            extra = _numero(limite, "o limite de velocidade assistida")
            if extra <= 0:
                raise ErroValidacao("O limite de velocidade assistida deve ser maior que zero.")

        # O objeto aplica a validação da bateria no próprio construtor
        veiculo = TIPOS[tipo](0, modelo, capacidade, bateria_informada, extra)
        bateria = veiculo.get_autonomia_bateria()

        with self._repositorio() as repo:
            repo.inserir_veiculo(tipo, modelo, capacidade, bateria,
                                 extra if tipo == "van" else None,
                                 extra if tipo != "van" else None)

        resultado = Resultado(f"{veiculo.ROTULO} \"{modelo}\" cadastrada com bateria em {br(bateria)}%.")
        if bateria != bateria_informada:
            resultado.avisos.append(
                f"O nível informado ({br(bateria_informada)}%) está fora da faixa de 0 a 100; "
                "pela regra de validação, a bateria foi registrada como 0,0%.")
        return resultado

    def excluir_veiculo(self, veiculo_id):
        with self._repositorio() as repo:
            veiculo = self._veiculo(repo, veiculo_id)
            repo.excluir_veiculo(veiculo.id_veiculo)
        return Resultado(f"Veículo \"{veiculo.modelo}\" e o seu histórico foram excluídos.")

    def listar_veiculos(self):
        with self._repositorio() as repo:
            return repo.listar_veiculos()

    # ---------- bateria e viagens ----------

    def ajustar_bateria(self, veiculo_id, nivel):
        nivel_informado = _numero(nivel, "o novo nível de bateria")
        with self._repositorio() as repo:
            veiculo = self._veiculo(repo, veiculo_id)
            anterior = veiculo.get_autonomia_bateria()
            veiculo.set_autonomia_bateria(nivel_informado)
            novo = veiculo.get_autonomia_bateria()
            repo.atualizar_bateria(veiculo.id_veiculo, novo)
            repo.inserir_ajuste(veiculo.id_veiculo, nivel_informado, novo)

        resultado = Resultado(f"Bateria de \"{veiculo.modelo}\" ajustada de {br(anterior)}% para {br(novo)}%.")
        if novo != nivel_informado:
            resultado.avisos.append(
                f"O valor informado ({br(nivel_informado)}%) está fora da faixa de 0 a 100 "
                "e foi registrado como 0,0%.")
        elif bateria_critica(novo):
            resultado.avisos.append(f"Atenção: a bateria continua abaixo de {LIMITE_CRITICO:g}%.")
        return resultado

    def registrar_viagem(self, veiculo_id, distancia):
        distancia = _numero(distancia, "a distância percorrida")
        if distancia <= 0:
            raise ErroValidacao("A distância deve ser maior que zero.")
        if distancia > DISTANCIA_MAXIMA:
            raise ErroValidacao(f"A distância máxima por registro é {br(DISTANCIA_MAXIMA)} km.")

        with self._repositorio() as repo:
            veiculo = self._veiculo(repo, veiculo_id)
            inicial = veiculo.get_autonomia_bateria()
            consumo = distancia * veiculo.TAXA_CONSUMO
            final = veiculo.registrar_viagem(distancia)   # polimorfismo: cada tipo tem a sua taxa
            repo.atualizar_bateria(veiculo.id_veiculo, final)
            repo.inserir_viagem(veiculo.id_veiculo, distancia, inicial, final, consumo)

        resultado = Resultado(
            f"Viagem de {br(distancia)} km registrada para \"{veiculo.modelo}\": "
            f"bateria de {br(inicial)}% para {br(final)}%.")
        if consumo > inicial:
            resultado.avisos.append(
                f"A viagem exigiria {br(consumo)} pontos de bateria, mas havia {br(inicial)}%: "
                "a bateria se esgotou e ficou em 0,0%.")
        elif bateria_critica(final):
            resultado.avisos.append(f"Bateria crítica: abaixo de {LIMITE_CRITICO:g}%. Recarregue o veículo.")
        return resultado

    def historico(self, veiculo_id=None, somente_criticas=False):
        with self._repositorio() as repo:
            filtro = _inteiro_positivo(veiculo_id, "veículo") if veiculo_id else None
            viagens = repo.listar_viagens(filtro)
        if somente_criticas:
            viagens = list(filter(lambda v: bateria_critica(v["bateria_final"]), viagens))
        return viagens

    # ---------- painel ----------

    def resumo(self):
        """Totais do painel, calculados com map, filter e reduce sobre as viagens."""
        with self._repositorio() as repo:
            veiculos = repo.listar_veiculos()
            viagens = repo.listar_viagens()

        km_total = reduce(lambda soma, v: soma + v["distancia"], viagens, 0.0)
        consumo_total = sum(map(lambda v: v["consumo"], viagens))
        viagens_criticas = len(list(filter(lambda v: bateria_critica(v["bateria_final"]), viagens)))
        em_alerta = [v for v in veiculos if bateria_critica(v.get_autonomia_bateria())]

        return {
            "veiculos": len(veiculos),
            "viagens": len(viagens),
            "km_total": km_total,
            "consumo_total": consumo_total,
            "viagens_criticas": viagens_criticas,
            "em_alerta": em_alerta,
        }

    def carregar_exemplo(self):
        """Cadastra os dois veículos do enunciado, para testar o sistema rapidamente."""
        self.cadastrar_veiculo("van", "EcoCargo E-Van 1500", "1500", "100", placa="ECO1A26")
        self.cadastrar_veiculo("bicicleta", "EcoBike Urban 25", "30", "100", limite="25")
        return Resultado("Veículos de exemplo cadastrados: uma van e uma bicicleta com bateria em 100%.")


__all__ = ["SistemaTelemetria", "ErroValidacao", "Resultado", "LIMITE_CRITICO",
           "BATERIA_MINIMA", "BATERIA_MAXIMA"]
