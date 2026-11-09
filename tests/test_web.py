"""Testes da interface web, com o servidor rodando de verdade. Autor: Antonio Santos"""

import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from telemetria.servico import SistemaTelemetria
from telemetria.web import criar_servidor


class TestWeb(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.sistema = SistemaTelemetria(Path(self.pasta.name) / "teste.db")
        self.servidor = criar_servidor(self.sistema, porta=0)   # porta 0: o sistema escolhe uma livre
        self.porta = self.servidor.server_address[1]
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.cookies = {}

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self.pasta.cleanup()

    def pedir(self, metodo, caminho, dados=None, origem=None):
        conexao = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=5)
        cabecalhos = {}
        corpo = None
        if dados is not None:
            corpo = urlencode(dados)
            cabecalhos["Content-Type"] = "application/x-www-form-urlencoded"
        if origem:
            cabecalhos["Origin"] = origem
        if self.cookies:
            cabecalhos["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        conexao.request(metodo, caminho, corpo, cabecalhos)
        resposta = conexao.getresponse()
        texto = resposta.read().decode("utf-8")
        for cookie in resposta.msg.get_all("Set-Cookie") or []:
            nome, valor = cookie.split(";")[0].split("=", 1)
            self.cookies[nome] = valor
        conexao.close()
        return resposta, texto

    def test_painel_vazio(self):
        resposta, texto = self.pedir("GET", "/")
        self.assertEqual(resposta.status, 200)
        self.assertIn("Nenhum veículo cadastrado", texto)

    def test_filtro_por_tipo_fica_guardado(self):
        origem = f"http://127.0.0.1:{self.porta}"
        self.pedir("POST", "/exemplo", {}, origem)

        _, todos = self.pedir("GET", "/")
        self.assertIn("EcoCargo E-Van 1500", todos)
        self.assertIn("EcoBike Urban 25", todos)

        _, vans = self.pedir("GET", "/?tipo=van")
        self.assertIn("EcoCargo E-Van 1500", vans)
        self.assertNotIn("EcoBike Urban 25", vans)
        self.assertIn("Vans elétricas", vans)

        # Depois de uma ação, o painel continua mostrando só as vans
        van_id = self.sistema.listar_veiculos()[0].id_veiculo
        self.pedir("POST", f"/veiculos/{van_id}/viagem", {"distancia": "10"}, origem)
        _, depois = self.pedir("GET", "/")
        self.assertIn("EcoCargo E-Van 1500", depois)
        self.assertNotIn("EcoBike Urban 25", depois)

        _, bikes = self.pedir("GET", "/?tipo=bicicleta")
        self.assertIn("EcoBike Urban 25", bikes)
        self.assertNotIn("EcoCargo E-Van 1500", bikes)

        _, de_novo = self.pedir("GET", "/?tipo=todos")
        self.assertIn("EcoCargo E-Van 1500", de_novo)
        self.assertIn("EcoBike Urban 25", de_novo)

        _, invalido = self.pedir("GET", "/?tipo=<script>")
        self.assertIn("EcoBike Urban 25", invalido)
        self.assertNotIn("<script>", invalido)

    def test_fluxo_completo(self):
        resposta, _ = self.pedir("POST", "/veiculos", {
            "tipo": "van", "modelo": "EcoCargo", "capacidade": "1500", "bateria": "100", "placa": "ECO1A26"})
        self.assertEqual(resposta.status, 303)

        _, painel = self.pedir("GET", "/")
        self.assertIn("cadastrada com bateria em 100,0%", painel)   # recado exibido uma vez
        self.assertIn("EcoCargo", painel)

        veiculo = self.sistema.listar_veiculos()[0]
        self.pedir("POST", f"/veiculos/{veiculo.id_veiculo}/viagem", {"distancia": "50"})
        _, painel = self.pedir("GET", "/")
        self.assertIn("75,0%", painel)

        _, historico = self.pedir("GET", "/viagens")
        self.assertIn("100,0% → 75,0%", historico)

    def test_erro_volta_ao_formulario_preenchido(self):
        resposta, texto = self.pedir("POST", "/veiculos", {
            "tipo": "van", "modelo": "Minha van", "capacidade": "100", "bateria": "50", "placa": "X"})
        self.assertEqual(resposta.status, 422)
        self.assertIn("Placa inválida", texto)
        self.assertIn('value="Minha van"', texto)

    def test_texto_do_usuario_e_escapado(self):
        self.pedir("POST", "/veiculos", {
            "tipo": "bicicleta", "modelo": "<script>alert(1)</script>", "capacidade": "30",
            "bateria": "80", "limite": "25"})
        _, painel = self.pedir("GET", "/")
        self.assertNotIn("<script>alert(1)</script>", painel)
        self.assertIn("&lt;script&gt;", painel)

    def test_recusa_formulario_de_outro_site(self):
        resposta, _ = self.pedir("POST", "/exemplo", {}, origem="http://site-malicioso.com")
        self.assertEqual(resposta.status, 403)
        self.assertEqual(self.sistema.listar_veiculos(), [])

    def test_aceita_formulario_do_proprio_sistema(self):
        resposta, _ = self.pedir("POST", "/exemplo", {}, origem=f"http://127.0.0.1:{self.porta}")
        self.assertEqual(resposta.status, 303)
        self.assertEqual(len(self.sistema.listar_veiculos()), 2)

    def test_estaticos_e_pagina_inexistente(self):
        resposta, _ = self.pedir("GET", "/static/estilo.css")
        self.assertEqual(resposta.status, 200)
        resposta, _ = self.pedir("GET", "/static/../servico.py")
        self.assertEqual(resposta.status, 404)
        resposta, _ = self.pedir("GET", "/nao-existe")
        self.assertEqual(resposta.status, 404)


if __name__ == "__main__":
    unittest.main()
