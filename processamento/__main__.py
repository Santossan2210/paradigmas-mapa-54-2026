"""
Demonstração do processamento funcional das viagens.

    python -m processamento

1. Lote de 10 viagens: MAP, FILTER e REDUCE passo a passo.
2. Avaliação preguiçosa: só é calculado o que o resultado pede.
3. Lote de 100.000 viagens: o mesmo pipeline em modo sequencial e em paralelo
   (vários processos), com a conferência de que os totais são idênticos.

Autor: Antonio Santos
"""

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from statistics import mean

from .calculo import LIMITE_CRITICO, calcular
from .gerador import SEMENTE, gerar_lote
from .pipeline import agregar, selecionar_criticas, transformar

RODADAS = 5


def br(valor, casas=1):
    """Número no formato brasileiro: 1.234,5"""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def imprimir_totais(totais):
    for resumo in totais:
        print(f"   {resumo.categoria.rotulo:<19} viagens: {br(resumo.viagens, 0):>7} | "
              f"km: {br(resumo.distancia):>12} | consumo: {br(resumo.consumo):>11} pontos | "
              f"alertas: {br(resumo.alertas, 0):>6}")


def lote_pequeno():
    lote = gerar_lote(10)
    print(f"1) Lote de {len(lote)} viagens (semente {SEMENTE})")
    print("   MAP - cada viagem transformada em resultado:")
    for r in transformar(lote):
        v = r.viagem
        print(f"   #{v.numero:02d} {v.categoria.rotulo:<19} {br(v.distancia):>6} km | "
              f"bateria {br(v.bateria_inicial):>5}% -> {br(r.bateria_final):>5}% | "
              f"consumo {br(r.consumo):>5}{'  CRÍTICA' if r.critica else ''}")

    criticas = tuple(selecionar_criticas(transformar(lote)))
    numeros = ", ".join(f"#{r.viagem.numero:02d}" for r in criticas)
    print(f"   FILTER - viagens abaixo de {LIMITE_CRITICO:g}%: {numeros or 'nenhuma'}")

    print("   REDUCE - totais por categoria:")
    imprimir_totais(agregar(lote))
    return lote


def avaliacao_preguicosa(lote):
    print()
    print("2) Avaliação preguiçosa")

    def calcular_avisando(viagem):
        # O print existe só para mostrar quando o cálculo acontece
        print(f"   calculando a viagem #{viagem.numero:02d}")
        return calcular(viagem)

    fluxo = selecionar_criticas(map(calcular_avisando, lote))
    print("   Fluxo montado (map + filter). Nenhuma viagem foi calculada ainda.")
    primeira = next(fluxo, None)
    if primeira is None:
        print("   Nenhuma viagem crítica no lote.")
    else:
        print(f"   Primeira viagem crítica: #{primeira.viagem.numero:02d}. "
              f"As demais viagens não foram calculadas.")


def cronometrar(funcao):
    tempos, resultado = [], None
    for _ in range(RODADAS):
        inicio = time.perf_counter()
        resultado = funcao()
        tempos.append((time.perf_counter() - inicio) * 1000)
    return resultado, mean(tempos)


def lote_grande():
    print()
    lote = gerar_lote(100_000)
    nucleos = os.cpu_count() or 1
    print(f"3) Lote de {br(len(lote), 0)} viagens - sequencial x paralelo "
          f"({nucleos} núcleos, média de {RODADAS} rodadas)")

    sequencial, tempo_seq = cronometrar(lambda: agregar(lote, map, nucleos))

    with ProcessPoolExecutor(max_workers=nucleos) as executor:
        agregar(lote, executor.map, nucleos)   # aquece os processos antes de medir
        paralelo, tempo_par = cronometrar(lambda: agregar(lote, executor.map, nucleos))

    print("   Sequencial:")
    imprimir_totais(sequencial)
    print("   Paralelo:")
    imprimir_totais(paralelo)
    print(f"   Tempo médio sequencial: {br(tempo_seq)} ms")
    print(f"   Tempo médio paralelo:   {br(tempo_par)} ms")
    print(f"   Resultados idênticos: {'SIM' if sequencial == paralelo else 'NÃO'}")
    return sequencial == paralelo


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== EcoFleet - Processamento funcional das viagens ===")
    lote = lote_pequeno()
    avaliacao_preguicosa(lote)
    iguais = lote_grande()
    return 0 if iguais else 1


if __name__ == "__main__":
    sys.exit(main())
