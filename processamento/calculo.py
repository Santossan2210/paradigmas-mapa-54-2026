"""
Regras de cálculo escritas como funções puras: o resultado depende só dos
parâmetros, e nada fora da função é lido ou alterado.

Autor: Antonio Santos
"""

from .dados import ResultadoViagem, ResumoCategoria

LIMITE_CRITICO = 20.0   # abaixo disso a viagem termina em situação crítica


def validar_bateria(nivel):
    """Mesma regra da classe Veiculo: fora de 0 a 100, o nível vira 0."""
    return 0.0 if nivel < 0.0 or nivel > 100.0 else nivel


def eh_critica(bateria_final):
    return bateria_final < LIMITE_CRITICO


def calcular(viagem):
    """MAP: transforma uma viagem em um resultado novo."""
    consumo = viagem.distancia * viagem.categoria.taxa
    bateria_final = validar_bateria(viagem.bateria_inicial - consumo)
    return ResultadoViagem(viagem, consumo, bateria_final, eh_critica(bateria_final))


def resumo_de(resultado):
    """Converte um resultado em um resumo de uma única viagem, pronto para somar."""
    return ResumoCategoria(
        categoria=resultado.viagem.categoria,
        viagens=1,
        distancia_centesimos=round(resultado.viagem.distancia * 100),
        consumo_centesimos=round(resultado.consumo * 100),
        alertas=1 if resultado.critica else 0,
    )


def combinar(a, b):
    """REDUCE: soma dois resumos e devolve um terceiro. É associativa."""
    return ResumoCategoria(
        categoria=a.categoria,
        viagens=a.viagens + b.viagens,
        distancia_centesimos=a.distancia_centesimos + b.distancia_centesimos,
        consumo_centesimos=a.consumo_centesimos + b.consumo_centesimos,
        alertas=a.alertas + b.alertas,
    )
