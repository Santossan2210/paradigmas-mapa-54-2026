"""Testes do processamento funcional (Parte II). Autor: Antonio Santos"""

import dataclasses
import unittest
from concurrent.futures import ProcessPoolExecutor

from processamento.calculo import calcular, combinar, eh_critica, resumo_de
from processamento.dados import Categoria, Viagem
from processamento.gerador import gerar_lote
from processamento.pipeline import agregar, selecionar_criticas, transformar


def viagem(categoria=Categoria.VAN, distancia=50.0, bateria=100.0, numero=1):
    return Viagem(numero, categoria, distancia, bateria)


class TestFuncoesPuras(unittest.TestCase):

    def test_mesmas_taxas_da_parte_oo(self):
        self.assertEqual(calcular(viagem(Categoria.VAN)).bateria_final, 75.0)
        self.assertEqual(calcular(viagem(Categoria.BICICLETA)).bateria_final, 90.0)

    def test_mesma_entrada_mesma_saida(self):
        entrada = viagem(distancia=33.3, bateria=61.7)
        self.assertEqual(calcular(entrada), calcular(entrada))

    def test_bateria_esgotada_vira_zero(self):
        self.assertEqual(calcular(viagem(distancia=300.0)).bateria_final, 0.0)

    def test_limite_critico(self):
        self.assertTrue(eh_critica(19.9))
        self.assertFalse(eh_critica(20.0))

    def test_combinar_associativo(self):
        a, b, c = (resumo_de(calcular(viagem(distancia=d))) for d in (10.0, 20.5, 33.3))
        self.assertEqual(combinar(combinar(a, b), c), combinar(a, combinar(b, c)))


class TestImutabilidade(unittest.TestCase):

    def test_dados_nao_podem_ser_alterados(self):
        entrada = viagem()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            entrada.distancia = 1.0
        with self.assertRaises(dataclasses.FrozenInstanceError):
            calcular(entrada).bateria_final = 100.0

    def test_entrada_continua_igual_apos_o_pipeline(self):
        lote = gerar_lote(50)
        copia = tuple(lote)
        agregar(lote)
        self.assertEqual(lote, copia)


class TestPipeline(unittest.TestCase):

    def test_lote_sempre_igual(self):
        self.assertEqual(gerar_lote(20), gerar_lote(20))

    def test_avaliacao_preguicosa(self):
        calculadas = []

        def calcular_registrando(v):
            calculadas.append(v.numero)
            return calcular(v)

        lote = (viagem(bateria=100.0, numero=1), viagem(bateria=30.0, numero=2),
                viagem(bateria=100.0, numero=3))
        fluxo = selecionar_criticas(map(calcular_registrando, lote))
        self.assertEqual(calculadas, [])
        self.assertEqual(next(fluxo).viagem.numero, 2)
        self.assertEqual(calculadas, [1, 2])

    def test_totais_conferem_com_calculo_direto(self):
        lote = gerar_lote(300)
        totais = {r.categoria: r for r in agregar(lote, blocos=7)}
        for categoria in Categoria:
            resultados = [r for r in transformar(lote) if r.viagem.categoria is categoria]
            self.assertEqual(totais[categoria].viagens, len(resultados))
            self.assertEqual(totais[categoria].alertas, sum(r.critica for r in resultados))

    def test_paralelo_igual_ao_sequencial(self):
        lote = gerar_lote(5_000)
        sequencial = agregar(lote, map, 4)
        with ProcessPoolExecutor(max_workers=2) as executor:
            paralelo = agregar(lote, executor.map, 4)
        self.assertEqual(sequencial, paralelo)


if __name__ == "__main__":
    unittest.main()
