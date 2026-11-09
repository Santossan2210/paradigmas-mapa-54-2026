"""
Servidor web local: recebe as ações do navegador e devolve as páginas.

Usa só a biblioteca padrão do Python. Escuta apenas em 127.0.0.1, ou seja,
não fica acessível para outros computadores da rede.

Autor: Antonio Santos
"""

import re
import secrets
import threading
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import paginas
from .modelo import TIPOS
from .servico import ErroValidacao

PASTA_ESTATICOS = Path(__file__).parent / "static"
ESTATICOS = {
    "/static/estilo.css": "text/css; charset=utf-8",
    "/static/app.js": "text/javascript; charset=utf-8",
    "/static/telemetria.png": "image/png",
    "/static/van.png": "image/png",
    "/static/bicicleta.png": "image/png",
}
TAMANHO_MAXIMO_FORMULARIO = 10_000
ROTA_VEICULO = re.compile(r"^/veiculos/(\d+)/(viagem|bateria|excluir)$")


class Mensagens:
    """Recados exibidos uma única vez, após o redirecionamento (padrão PRG)."""

    def __init__(self):
        self._pendentes = {}
        self._trava = threading.Lock()

    def guardar(self, sessao, tipo, texto):
        with self._trava:
            self._pendentes.setdefault(sessao, []).append((tipo, texto))

    def retirar(self, sessao):
        with self._trava:
            return self._pendentes.pop(sessao, [])


def criar_servidor(sistema, porta=8000):
    mensagens = Mensagens()

    class Manipulador(BaseHTTPRequestHandler):
        server_version = "TelemetriaEcoFleet"

        # ---------- infraestrutura ----------

        def log_message(self, formato, *args):
            pass   # mantém o terminal limpo para o usuário

        def _sessao(self):
            cookie = SimpleCookie(self.headers.get("Cookie", ""))
            if "sessao" in cookie:
                return cookie["sessao"].value, False
            return secrets.token_urlsafe(16), True

        def _filtro_painel(self, consulta):
            """
            Tipo de veículo exibido no painel. A escolha vem do link (?tipo=) e fica
            guardada em cookie, para continuar valendo depois de registrar uma
            viagem, ajustar a bateria ou voltar de outra página.
            Devolve (filtro, cookie a gravar ou None).
            """
            if "tipo" in consulta:
                filtro = consulta["tipo"] if consulta["tipo"] in TIPOS else ""
                return filtro, f"filtro={filtro or 'todos'}; Path=/; HttpOnly; SameSite=Strict"
            cookie = SimpleCookie(self.headers.get("Cookie", ""))
            guardado = cookie["filtro"].value if "filtro" in cookie else ""
            return (guardado if guardado in TIPOS else ""), None

        def _responder(self, conteudo, status=HTTPStatus.OK, tipo="text/html; charset=utf-8", cookies=()):
            dados = conteudo.encode("utf-8") if isinstance(conteudo, str) else conteudo
            self.send_response(status)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'")
            self.send_header("Cache-Control", "no-store")
            sessao, nova = self._sessao()
            if nova:
                self.send_header("Set-Cookie", f"sessao={sessao}; Path=/; HttpOnly; SameSite=Strict")
            for cookie in cookies:
                self.send_header("Set-Cookie", cookie)
            self.end_headers()
            self.wfile.write(dados)

        def _redirecionar(self, destino, tipo=None, texto=None, avisos=()):
            sessao, nova = self._sessao()
            if texto:
                mensagens.guardar(sessao, tipo, texto)
            for aviso in avisos:
                mensagens.guardar(sessao, "aviso", aviso)
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", destino)
            self.send_header("Content-Length", "0")
            if nova:
                self.send_header("Set-Cookie", f"sessao={sessao}; Path=/; HttpOnly; SameSite=Strict")
            self.end_headers()

        def _mensagens(self):
            return mensagens.retirar(self._sessao()[0])

        def _formulario(self):
            tamanho = int(self.headers.get("Content-Length") or 0)
            if tamanho > TAMANHO_MAXIMO_FORMULARIO:
                raise ErroValidacao("Formulário grande demais.")
            corpo = self.rfile.read(tamanho).decode("utf-8", errors="replace")
            return {chave: valores[0] for chave, valores in parse_qs(corpo).items()}

        def _origem_valida(self):
            """Recusa formulários enviados por outros sites para este servidor local."""
            esperado = f"http://{self.headers.get('Host', '')}"
            origem = self.headers.get("Origin") or self.headers.get("Referer")
            return origem is None or origem == esperado or origem.startswith(esperado + "/")

        # ---------- GET ----------

        def do_GET(self):
            url = urlsplit(self.path)
            consulta = {chave: valores[0] for chave, valores in parse_qs(url.query).items()}

            if url.path in ESTATICOS:
                arquivo = PASTA_ESTATICOS / Path(url.path).name
                return self._responder(arquivo.read_bytes(), tipo=ESTATICOS[url.path])

            if url.path == "/":
                filtro, cookie = self._filtro_painel(consulta)
                todos = sistema.listar_veiculos()
                contagem = {"": len(todos)}
                contagem.update({t: sum(1 for v in todos if v.TIPO == t) for t in TIPOS})
                veiculos = [v for v in todos if not filtro or v.TIPO == filtro]
                pagina = paginas.painel(sistema.resumo(filtro or None), veiculos,
                                        self._mensagens(), filtro, contagem)
                return self._responder(pagina, cookies=[cookie] if cookie else [])

            if url.path == "/veiculos/novo":
                return self._responder(paginas.formulario_veiculo())

            if url.path == "/viagens":
                filtro = consulta.get("veiculo", "")
                criticas = consulta.get("criticas") == "1"
                try:
                    viagens = sistema.historico(filtro or None, criticas)
                except ErroValidacao:
                    viagens, filtro = sistema.historico(None, criticas), ""
                return self._responder(paginas.historico(
                    viagens, sistema.listar_veiculos(), filtro, criticas, self._mensagens()))

            if url.path == "/favicon.ico":
                return self._responder(b"", HTTPStatus.NO_CONTENT, "image/x-icon")

            return self._responder(paginas.nao_encontrada(), HTTPStatus.NOT_FOUND)

        # ---------- POST ----------

        def do_POST(self):
            if not self._origem_valida():
                return self._responder("Requisição recusada.", HTTPStatus.FORBIDDEN, "text/plain; charset=utf-8")

            caminho = urlsplit(self.path).path
            try:
                dados = self._formulario()
            except ErroValidacao as erro:
                return self._redirecionar("/", "erro", str(erro))

            if caminho == "/veiculos":
                try:
                    resultado = sistema.cadastrar_veiculo(
                        dados.get("tipo", ""), dados.get("modelo", ""), dados.get("capacidade", ""),
                        dados.get("bateria", ""), dados.get("placa", ""), dados.get("limite", ""))
                except ErroValidacao as erro:
                    # Volta ao formulário com o que foi digitado, para não perder o preenchimento
                    return self._responder(paginas.formulario_veiculo(dados, str(erro)),
                                           HTTPStatus.UNPROCESSABLE_ENTITY)
                return self._redirecionar("/", "sucesso", resultado.mensagem, resultado.avisos)

            if caminho == "/exemplo":
                resultado = sistema.carregar_exemplo()
                return self._redirecionar("/", "sucesso", resultado.mensagem)

            rota = ROTA_VEICULO.match(caminho)
            if rota:
                veiculo_id, acao = rota.groups()
                try:
                    if acao == "viagem":
                        resultado = sistema.registrar_viagem(veiculo_id, dados.get("distancia", ""))
                    elif acao == "bateria":
                        resultado = sistema.ajustar_bateria(veiculo_id, dados.get("nivel", ""))
                    else:
                        resultado = sistema.excluir_veiculo(veiculo_id)
                except ErroValidacao as erro:
                    return self._redirecionar("/", "erro", str(erro))
                return self._redirecionar("/", "sucesso", resultado.mensagem, resultado.avisos)

            return self._responder(paginas.nao_encontrada(), HTTPStatus.NOT_FOUND)

    return ThreadingHTTPServer(("127.0.0.1", porta), Manipulador)
