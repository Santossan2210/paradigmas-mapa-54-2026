"""Testes das regras do modelo orientado a objetos. Autor: Antonio Santos"""

import io
import unittest
from contextlib import redirect_stdout

from telemetria.modelo import BicicletaEletrica, VanEletrica, Veiculo


def van(bateria=100.0):
    return VanEletrica(1, "Van teste", 1500.0, bateria, "ABC1D23")


def bicicleta(bateria=100.0):
    return BicicletaEletrica(2, "Bike teste", 30.0, bateria, 25.0)


class TestValidacaoBateria(unittest.TestCase):
    """Fora da faixa de 0.0 a 100.0 a bateria fica em 0.0; os limites são válidos."""

    def test_valores(self):
        casos = [(-5, 0.0), (120, 0.0), (0, 0.0), (50, 50.0), (100, 100.0), (100.1, 0.0)]
        for informado, esperado in casos:
            with self.subTest(informado=informado):
                veiculo = van()
                veiculo.set_autonomia_bateria(informado)
                self.assertEqual(veiculo.get_autonomia_bateria(), esperado)

    def test_construtor_passa_pela_validacao(self):
        self.assertEqual(van(150).get_autonomia_bateria(), 0.0)
        self.assertEqual(bicicleta(-1).get_autonomia_bateria(), 0.0)


class TestViagens(unittest.TestCase):

    def test_van_50_km(self):
        veiculo = van()
        self.assertEqual(veiculo.registrar_viagem(50.0), 75.0)

    def test_bicicleta_50_km(self):
        veiculo = bicicleta()
        self.assertEqual(veiculo.registrar_viagem(50.0), 90.0)

    def test_bateria_esgotada_vira_zero(self):
        veiculo = van(10.0)
        self.assertEqual(veiculo.registrar_viagem(100.0), 0.0)

    def test_viagens_acumulam(self):
        veiculo = bicicleta()
        veiculo.registrar_viagem(50.0)
        veiculo.registrar_viagem(50.0)
        self.assertAlmostEqual(veiculo.get_autonomia_bateria(), 80.0)

    def test_autonomia_estimada(self):
        self.assertEqual(van(50.0).autonomia_estimada_km(), 100.0)
        self.assertEqual(bicicleta(50.0).autonomia_estimada_km(), 250.0)


class TestEstrutura(unittest.TestCase):

    def test_veiculo_e_abstrata(self):
        with self.assertRaises(TypeError):
            Veiculo()

    def test_bateria_privada(self):
        veiculo = van()
        self.assertFalse(hasattr(veiculo, "__autonomia_bateria"))
        self.assertFalse(hasattr(veiculo, "autonomia_bateria"))

    def test_heranca(self):
        self.assertIsInstance(van(), Veiculo)
        self.assertIsInstance(bicicleta(), Veiculo)


class TestMensagemViagem(unittest.TestCase):
    """O próprio registrar_viagem mostra no console a distância e a bateria restante."""

    def test_mensagem_no_console(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            van().registrar_viagem(50.0)
            bicicleta().registrar_viagem(50.0)
        texto = saida.getvalue()
        self.assertIn("[Van elétrica] Distância percorrida: 50.0 km | Bateria restante: 75.0%", texto)
        self.assertIn("[Bicicleta elétrica] Distância percorrida: 50.0 km | Bateria restante: 90.0%", texto)


if __name__ == "__main__":
    unittest.main()
