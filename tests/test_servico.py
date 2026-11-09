"""Testes das operações do sistema, com um banco temporário. Autor: Antonio Santos"""

import tempfile
import unittest
from pathlib import Path

from telemetria.servico import ErroValidacao, SistemaTelemetria, normalizar_placa


class BaseSistema(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.sistema = SistemaTelemetria(Path(self.pasta.name) / "teste.db")

    def tearDown(self):
        self.pasta.cleanup()

    def cadastrar_van(self, bateria="100"):
        self.sistema.cadastrar_veiculo("van", "Van teste", "1500", bateria, placa="abc-1d23")
        return self.sistema.listar_veiculos()[-1]


class TestCadastro(BaseSistema):

    def test_cadastra_e_normaliza_placa(self):
        veiculo = self.cadastrar_van()
        self.assertEqual(veiculo.placa_identificacao, "ABC1D23")
        self.assertEqual(veiculo.get_autonomia_bateria(), 100.0)

    def test_formatos_de_placa(self):
        casos = [("abc1234", "ABC-1234"), ("ABC-1234", "ABC-1234"), ("abc 1234", "ABC-1234"),
                 ("abc1d23", "ABC1D23"), ("ABC-1D23", "ABC1D23"), (" eco1a26 ", "ECO1A26")]
        for informada, esperada in casos:
            with self.subTest(placa=informada):
                self.assertEqual(normalizar_placa(informada), esperada)

    def test_bateria_fora_da_faixa_vira_zero_com_aviso(self):
        resultado = self.sistema.cadastrar_veiculo("bicicleta", "Bike", "30", "120", limite="25")
        self.assertEqual(self.sistema.listar_veiculos()[0].get_autonomia_bateria(), 0.0)
        self.assertTrue(resultado.avisos)

    def test_aceita_virgula_decimal(self):
        self.sistema.cadastrar_veiculo("bicicleta", "Bike", "30,5", "87,5", limite="25")
        self.assertEqual(self.sistema.listar_veiculos()[0].get_autonomia_bateria(), 87.5)

    def test_entradas_invalidas(self):
        casos = [
            ("carro", "X", "1", "50", "ABC1234", ""),          # tipo inexistente
            ("van", "", "1", "50", "ABC1234", ""),             # sem modelo
            ("van", "X", "-1", "50", "ABC1234", ""),           # carga negativa
            ("van", "X", "1", "abc", "ABC1234", ""),           # bateria não numérica
            ("van", "X", "1", "nan", "ABC1234", ""),           # NaN escaparia da validação
            ("van", "X", "1", "50", "12345", ""),              # placa inválida
            ("van", "X", "1", "50", "ABC1D2X", ""),            # Mercosul com letra no fim
            ("van", "X", "1", "50", "ABCD1E20", ""),           # 4 letras: não existe
            ("van", "X", "1", "50", "AB12345", ""),            # 2 letras
            ("van", "X", "1", "50", "ABC12D3", ""),            # letra na posição errada
            ("bicicleta", "X", "1", "50", "", "0"),            # limite zero
        ]
        for caso in casos:
            with self.subTest(caso=caso), self.assertRaises(ErroValidacao):
                self.sistema.cadastrar_veiculo(*caso)
        self.assertEqual(self.sistema.listar_veiculos(), [])

    def test_exemplo_do_enunciado(self):
        self.sistema.carregar_exemplo()
        van, bicicleta = self.sistema.listar_veiculos()
        self.sistema.registrar_viagem(van.id_veiculo, "50")
        self.sistema.registrar_viagem(bicicleta.id_veiculo, "50")
        van, bicicleta = self.sistema.listar_veiculos()
        self.assertEqual(van.get_autonomia_bateria(), 75.0)
        self.assertEqual(bicicleta.get_autonomia_bateria(), 90.0)


class TestViagensEBateria(BaseSistema):

    def test_viagem_grava_historico(self):
        veiculo = self.cadastrar_van()
        self.sistema.registrar_viagem(veiculo.id_veiculo, "20")
        viagem = self.sistema.historico()[0]
        self.assertEqual((viagem["bateria_inicial"], viagem["bateria_final"], viagem["consumo"]),
                         (100.0, 90.0, 10.0))

    def test_bateria_persiste_entre_operacoes(self):
        veiculo = self.cadastrar_van()
        self.sistema.registrar_viagem(veiculo.id_veiculo, "50")
        self.sistema.registrar_viagem(veiculo.id_veiculo, "50")
        self.assertEqual(self.sistema.listar_veiculos()[0].get_autonomia_bateria(), 50.0)

    def test_viagem_que_esgota_a_bateria(self):
        veiculo = self.cadastrar_van("10")
        resultado = self.sistema.registrar_viagem(veiculo.id_veiculo, "100")
        self.assertEqual(self.sistema.listar_veiculos()[0].get_autonomia_bateria(), 0.0)
        self.assertIn("esgotou", resultado.avisos[0])

    def test_alerta_critico(self):
        veiculo = self.cadastrar_van("30")
        resultado = self.sistema.registrar_viagem(veiculo.id_veiculo, "30")   # 30 - 15 = 15%
        self.assertIn("crítica", resultado.avisos[0])
        self.assertEqual(len(self.sistema.historico(somente_criticas=True)), 1)
        self.assertEqual(len(self.sistema.resumo()["em_alerta"]), 1)

    def test_distancias_invalidas(self):
        veiculo = self.cadastrar_van()
        for distancia in ("0", "-5", "", "dez", "1001", "inf"):
            with self.subTest(distancia=distancia), self.assertRaises(ErroValidacao):
                self.sistema.registrar_viagem(veiculo.id_veiculo, distancia)
        self.assertEqual(self.sistema.historico(), [])

    def test_veiculo_inexistente(self):
        with self.assertRaises(ErroValidacao):
            self.sistema.registrar_viagem(999, "10")

    def test_ajuste_de_bateria(self):
        veiculo = self.cadastrar_van("10")
        self.sistema.ajustar_bateria(veiculo.id_veiculo, "95")
        self.assertEqual(self.sistema.listar_veiculos()[0].get_autonomia_bateria(), 95.0)
        resultado = self.sistema.ajustar_bateria(veiculo.id_veiculo, "150")
        self.assertEqual(self.sistema.listar_veiculos()[0].get_autonomia_bateria(), 0.0)
        self.assertTrue(resultado.avisos)

    def test_excluir_remove_historico(self):
        veiculo = self.cadastrar_van()
        self.sistema.registrar_viagem(veiculo.id_veiculo, "10")
        self.sistema.excluir_veiculo(veiculo.id_veiculo)
        self.assertEqual(self.sistema.listar_veiculos(), [])
        self.assertEqual(self.sistema.historico(), [])

    def test_resumo(self):
        self.sistema.carregar_exemplo()
        van, bicicleta = self.sistema.listar_veiculos()
        self.sistema.registrar_viagem(van.id_veiculo, "50")
        self.sistema.registrar_viagem(bicicleta.id_veiculo, "30")
        resumo = self.sistema.resumo()
        self.assertEqual((resumo["veiculos"], resumo["viagens"]), (2, 2))
        self.assertEqual(resumo["km_total"], 80.0)
        self.assertAlmostEqual(resumo["consumo_total"], 25.0 + 6.0)


if __name__ == "__main__":
    unittest.main()
