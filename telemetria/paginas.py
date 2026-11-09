"""
Montagem das páginas HTML. Todo texto vindo do usuário ou do banco passa por
esc() antes de entrar no HTML.

Autor: Antonio Santos
"""

from html import escape

from .servico import LIMITE_CRITICO, bateria_critica

ICONES = {"van": "🚐", "bicicleta": "🚲"}


def esc(valor):
    return escape(str(valor), quote=True)


def num(valor, casas=1):
    """Número no formato brasileiro: 1.234,5"""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def faixa_bateria(nivel):
    if bateria_critica(nivel):
        return "critica"
    if nivel < 50:
        return "media"
    return "boa"


def layout(titulo, corpo, mensagens=(), ativo=""):
    def link(href, texto, chave):
        atual = ' aria-current="page"' if chave == ativo else ""
        return f'<a href="{href}"{atual}>{texto}</a>'

    avisos = "".join(
        f'<div class="mensagem {esc(tipo)}" role="status">{esc(texto)}</div>'
        for tipo, texto in mensagens)

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} · Telemetria EcoFleet</title>
<link rel="stylesheet" href="/static/estilo.css">
<script src="/static/app.js" defer></script>
</head>
<body>
<header class="topo">
  <div class="marca">⚡ Telemetria EcoFleet</div>
  <nav>
    {link("/", "Painel", "painel")}
    {link("/veiculos/novo", "Novo veículo", "novo")}
    {link("/viagens", "Histórico", "historico")}
  </nav>
</header>
<main>
{avisos}
{corpo}
</main>
<footer>Sistema de telemetria da frota · Antonio Santos</footer>
</body>
</html>"""


# ---------- painel ----------

def painel(resumo, veiculos, mensagens):
    cartoes = f"""
<section class="indicadores">
  <div class="indicador"><span>{resumo["veiculos"]}</span>veículos</div>
  <div class="indicador"><span>{resumo["viagens"]}</span>viagens registradas</div>
  <div class="indicador"><span>{num(resumo["km_total"])}</span>km rodados</div>
  <div class="indicador {'alerta' if resumo['viagens_criticas'] else ''}">
    <span>{resumo["viagens_criticas"]}</span>viagens terminaram abaixo de {LIMITE_CRITICO:g}%</div>
</section>"""

    alerta = ""
    if resumo["em_alerta"]:
        nomes = ", ".join(esc(v.modelo) for v in resumo["em_alerta"])
        alerta = (f'<div class="mensagem aviso">🔋 Bateria crítica (abaixo de {LIMITE_CRITICO:g}%): '
                  f'{nomes}. Ajuste a bateria após a recarga.</div>')

    if not veiculos:
        corpo = cartoes + """
<section class="vazio">
  <h1>Nenhum veículo cadastrado</h1>
  <p>Comece cadastrando um veículo da frota, ou carregue o exemplo do enunciado
     (uma van e uma bicicleta com bateria em 100%).</p>
  <div class="acoes">
    <a class="botao" href="/veiculos/novo">Cadastrar veículo</a>
    <form method="post" action="/exemplo"><button class="botao secundario">Carregar exemplo</button></form>
  </div>
</section>"""
        return layout("Painel", corpo, mensagens, "painel")

    lista = "".join(cartao_veiculo(v) for v in veiculos)
    corpo = f"""{cartoes}{alerta}
<div class="cabecalho-secao">
  <h1>Frota</h1>
  <a class="botao" href="/veiculos/novo">+ Novo veículo</a>
</div>
<section class="frota">{lista}</section>"""
    return layout("Painel", corpo, mensagens, "painel")


def cartao_veiculo(v):
    bateria = v.get_autonomia_bateria()
    faixa = faixa_bateria(bateria)
    vid = v.id_veiculo
    return f"""
<article class="veiculo">
  <header>
    <span class="icone" aria-hidden="true">{ICONES[v.TIPO]}</span>
    <div>
      <h2>{esc(v.modelo)}</h2>
      <p class="sub">{esc(v.ROTULO)} · {esc(v.detalhe())} · carga {num(v.capacidade_carga, 0)} kg</p>
    </div>
  </header>

  <div class="bateria {faixa}">
    <div class="rotulo"><span>Bateria</span><strong>{num(bateria)}%</strong></div>
    <div class="barra" role="progressbar" aria-valuenow="{bateria:.1f}" aria-valuemin="0" aria-valuemax="100"
         aria-label="Bateria de {esc(v.modelo)}"><div style="width:{bateria:.1f}%"></div></div>
    <p class="sub">Autonomia estimada: {num(v.autonomia_estimada_km())} km
       · consumo de {num(v.TAXA_CONSUMO)} ponto por km</p>
  </div>

  <form method="post" action="/veiculos/{vid}/viagem" class="linha">
    <label for="dist-{vid}">Distância da viagem (km)</label>
    <div class="campo-botao">
      <input id="dist-{vid}" name="distancia" type="number" inputmode="decimal" step="0.1"
             min="0.1" max="1000" placeholder="ex.: 50" required>
      <button class="botao">Registrar viagem</button>
    </div>
  </form>

  <details>
    <summary>Mais opções</summary>
    <form method="post" action="/veiculos/{vid}/bateria" class="linha">
      <label for="bat-{vid}">Ajustar bateria (após recarga), em %</label>
      <div class="campo-botao">
        <input id="bat-{vid}" name="nivel" type="number" step="0.1" placeholder="0 a 100" required>
        <button class="botao secundario">Salvar nível</button>
      </div>
    </form>
    <div class="acoes">
      <a href="/viagens?veiculo={vid}">Ver histórico deste veículo</a>
      <form method="post" action="/veiculos/{vid}/excluir" data-confirmar="Excluir {esc(v.modelo)} e todo o histórico?">
        <button class="botao perigo">Excluir veículo</button>
      </form>
    </div>
  </details>
</article>"""


# ---------- cadastro ----------

def formulario_veiculo(valores=None, erro=None):
    valores = valores or {}
    tipo = valores.get("tipo", "van")

    def valor(campo, padrao=""):
        return esc(valores.get(campo, padrao))

    def marcado(opcao):
        return " checked" if tipo == opcao else ""

    # O erro fica dentro do formulário: após o envio, o navegador pode manter a
    # rolagem da página, e uma mensagem no topo ficaria fora da área visível
    aviso = f'<div class="mensagem erro" role="alert">{esc(erro)}</div>' if erro else ""
    corpo = f"""
<h1>Cadastrar veículo</h1>
<form method="post" action="/veiculos" class="cartao formulario" id="form-veiculo">
  {aviso}
  <fieldset class="tipos">
    <legend>Tipo de veículo</legend>
    <label class="opcao"><input type="radio" name="tipo" value="van"{marcado("van")}>
      <span>🚐 <strong>Van elétrica</strong><small>Carga · consome 0,5 ponto de bateria por km</small></span></label>
    <label class="opcao"><input type="radio" name="tipo" value="bicicleta"{marcado("bicicleta")}>
      <span>🚲 <strong>Bicicleta elétrica</strong><small>Entrega · consome 0,2 ponto de bateria por km</small></span></label>
  </fieldset>

  <label for="modelo">Modelo</label>
  <input id="modelo" name="modelo" maxlength="60" required value="{valor('modelo')}" placeholder="ex.: EcoCargo E-Van 1500">

  <div class="duas-colunas">
    <div>
      <label for="capacidade">Capacidade de carga (kg)</label>
      <input id="capacidade" name="capacidade" type="number" step="0.1" min="0" required value="{valor('capacidade')}">
    </div>
    <div>
      <label for="bateria">Bateria atual (%)</label>
      <input id="bateria" name="bateria" type="number" step="0.1" required value="{valor('bateria', '100')}">
      <small>Valores fora de 0 a 100 são registrados como 0%.</small>
    </div>
  </div>

  <div data-tipo="van">
    <label for="placa">Placa (só van)</label>
    <input id="placa" name="placa" maxlength="8" value="{valor('placa')}" placeholder="ABC1D23" autocapitalize="characters">
  </div>
  <div data-tipo="bicicleta">
    <label for="limite">Limite de velocidade assistida em km/h (só bicicleta)</label>
    <input id="limite" name="limite" type="number" step="0.1" min="1" value="{valor('limite', '25')}">
  </div>

  <div class="acoes">
    <button class="botao">Cadastrar</button>
    <a href="/">Cancelar</a>
  </div>
</form>"""
    return layout("Novo veículo", corpo, ativo="novo")


# ---------- histórico ----------

def historico(viagens, veiculos, filtro_veiculo, somente_criticas, mensagens):
    opcoes = '<option value="">Todos os veículos</option>' + "".join(
        f'<option value="{v.id_veiculo}"{" selected" if str(v.id_veiculo) == filtro_veiculo else ""}>'
        f'{esc(v.modelo)}</option>' for v in veiculos)

    if viagens:
        linhas = "".join(f"""
<tr>
  <td>{esc(dia_hora(v["registrada_em"]))}</td>
  <td>{ICONES[v["tipo"]]} {esc(v["modelo"])}</td>
  <td class="num">{num(v["distancia"])} km</td>
  <td class="num">{num(v["bateria_inicial"])}% → {num(v["bateria_final"])}%</td>
  <td class="num">{num(v["consumo"])}</td>
  <td>{'<span class="selo critica">Crítica</span>' if bateria_critica(v["bateria_final"]) else '<span class="selo boa">Normal</span>'}</td>
</tr>""" for v in viagens)
        tabela = f"""
<div class="tabela-rolagem">
<table>
  <thead><tr><th>Data e hora</th><th>Veículo</th><th>Distância</th><th>Bateria</th><th>Consumo (pontos)</th><th>Situação</th></tr></thead>
  <tbody>{linhas}</tbody>
</table>
</div>"""
    else:
        tabela = '<p class="vazio">Nenhuma viagem encontrada com esses filtros.</p>'

    corpo = f"""
<h1>Histórico de viagens</h1>
<form method="get" action="/viagens" class="filtros">
  <label for="veiculo">Veículo</label>
  <select id="veiculo" name="veiculo">{opcoes}</select>
  <label class="caixa"><input type="checkbox" name="criticas" value="1"{" checked" if somente_criticas else ""}>
    Só viagens que terminaram abaixo de {LIMITE_CRITICO:g}%</label>
  <button class="botao secundario">Filtrar</button>
</form>
{tabela}"""
    return layout("Histórico", corpo, mensagens, "historico")


def dia_hora(texto):
    """'2026-11-09 07:50:12' -> '09/11/2026 07:50'"""
    data, hora = texto.split(" ")
    ano, mes, dia = data.split("-")
    return f"{dia}/{mes}/{ano} {hora[:5]}"


def nao_encontrada():
    return layout("Página não encontrada",
                  '<section class="vazio"><h1>Página não encontrada</h1><p><a href="/">Voltar ao painel</a></p></section>')
