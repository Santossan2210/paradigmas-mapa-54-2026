"""
Pipeline funcional: dados de entrada -> MAP -> FILTER -> REDUCE -> resultado.

map e filter do Python são preguiçosos: devolvem um iterador e só calculam um
item quando alguém pede por ele. reduce (functools) combina os itens em um só.

Autor: Antonio Santos
"""

from functools import partial, reduce

from .calculo import calcular, combinar, resumo_de
from .dados import Categoria, ResumoCategoria


def transformar(viagens):
    """MAP: cada viagem vira um ResultadoViagem. Nada é calculado ainda."""
    return map(calcular, viagens)


def selecionar_criticas(resultados):
    """FILTER: fica só o que terminou abaixo do limite crítico."""
    return filter(lambda resultado: resultado.critica, resultados)


def da_categoria(categoria, resultado):
    return resultado.viagem.categoria is categoria


def resumir(categoria, viagens):
    """MAP + FILTER + REDUCE de uma categoria sobre um conjunto de viagens."""
    resultados = filter(partial(da_categoria, categoria), transformar(viagens))
    return reduce(combinar, map(resumo_de, resultados), ResumoCategoria(categoria))


def resumir_bloco(viagens):
    """Totais de todas as categorias de um bloco. Roda inteiro dentro de um processo."""
    return tuple(resumir(categoria, viagens) for categoria in Categoria)


def somar_totais(a, b):
    """Junta os totais de dois blocos, categoria por categoria."""
    return tuple(map(combinar, a, b))


def dividir(viagens, blocos):
    """Divide o lote em blocos contíguos (tuplas: também imutáveis)."""
    tamanho = -(-len(viagens) // blocos)   # divisão arredondada para cima
    return tuple(viagens[i:i + tamanho] for i in range(0, len(viagens), tamanho))


def agregar(viagens, mapear=map, blocos=1):
    """
    REDUCE do lote inteiro.

    mapear é uma função recebida como parâmetro (ordem superior). Com o map do
    Python, os blocos são resumidos um depois do outro; com o map de um
    ProcessPoolExecutor, cada bloco vai para um processo diferente. O resto do
    pipeline é o mesmo nos dois casos.
    """
    vazio = tuple(ResumoCategoria(categoria) for categoria in Categoria)
    parciais = mapear(resumir_bloco, dividir(viagens, blocos))
    return reduce(somar_totais, parciais, vazio)
