"""
Gera o relatório da MAPA (.docx) a partir dos textos de relatorio/conteudo/,
do código-fonte do repositório e das saídas guardadas em relatorio/saidas/.

Uso, na raiz do repositório:
    python relatorio/gerar_relatorio.py

Autor: Antonio Santos
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
IDENTIFICACAO = "relatorio/identificacao.local.txt"
SAIDA_DOCX = "relatorio/gerado/Relatorio_MAPA_Paradigmas_Antonio_Santos.docx"

# Ordem de montagem. Os arquivos marcados com True começam em página nova
# (início da Parte I e da Parte II).
CONTEUDO = [
    ("relatorio/conteudo/00_capa.txt", False),
    ("relatorio/conteudo/10_tarefa1.txt", True),
    ("relatorio/conteudo/20_tarefa2.txt", False),
    ("relatorio/conteudo/30_tarefa3.txt", False),
    ("relatorio/conteudo/40_topico1.txt", True),
    ("relatorio/conteudo/50_topico2.txt", False),
    ("relatorio/conteudo/60_topico3.txt", False),
    ("relatorio/conteudo/70_topico4.txt", False),
    ("relatorio/conteudo/80_topico5.txt", False),
    ("relatorio/conteudo/90_referencias.txt", False),
]

# A Tarefa 3 precisa ocupar de 10 a 20 linhas no documento (Arial 12, margens de 2,5 cm)
ARQUIVO_TAREFA3 = "relatorio/conteudo/30_tarefa3.txt"
PALAVRAS_MIN, PALAVRAS_MAX = 130, 260

FONTE_TEXTO = "Arial"
FONTE_CODIGO = "Consolas"
CINZA_CODIGO = "EDEDED"

MARCA_ARQUIVO = re.compile(r"^\[\[(CODIGO|SAIDA|IMAGEM):(.+)\]\]$")
MARCA_CHAVE = re.compile(r"\{\{(\w+)\}\}")


def abortar(mensagem):
    print(mensagem, file=sys.stderr)
    sys.exit(1)


def caminho(relativo):
    """Resolve um caminho relativo à raiz e aborta se o arquivo não existir."""
    arquivo = RAIZ / relativo
    if not arquivo.is_file():
        abortar(f"Arquivo não encontrado: {relativo}")
    return arquivo


def ler_texto(relativo):
    # utf-8-sig aceita arquivo com ou sem BOM; splitlines trata CRLF e LF igual
    return caminho(relativo).read_text(encoding="utf-8-sig").splitlines()


def ler_identificacao():
    if not (RAIZ / IDENTIFICACAO).is_file():
        abortar("Crie relatorio/identificacao.local.txt a partir de identificacao.exemplo.txt")
    dados = {}
    for linha in ler_texto(IDENTIFICACAO):
        if "=" in linha and not linha.lstrip().startswith("#"):
            chave, valor = linha.split("=", 1)
            dados[chave.strip()] = valor.strip()
    return dados


def substituir_chaves(linha, dados):
    def valor(encontrado):
        chave = encontrado.group(1)
        if not dados.get(chave):
            abortar(f"Campo de identificação vazio: {chave}")
        return dados[chave]

    return MARCA_CHAVE.sub(valor, linha)


# ---------- formatação ----------

def configurar_documento(doc):
    for secao in doc.sections:
        secao.top_margin = secao.bottom_margin = Cm(2.5)
        secao.left_margin = secao.right_margin = Cm(2.5)

    normal = doc.styles["Normal"]
    definir_fonte(normal.font, FONTE_TEXTO, 12)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    for nome, tamanho in (("Title", 18), ("Heading 1", 16), ("Heading 2", 13)):
        estilo = doc.styles[nome]
        definir_fonte(estilo.font, FONTE_TEXTO, tamanho)
        estilo.font.bold = True
        estilo.font.color.rgb = RGBColor(0, 0, 0)

    definir_fonte(doc.styles["List Bullet"].font, FONTE_TEXTO, 12)


def definir_fonte(fonte, nome, tamanho):
    fonte.name = nome
    fonte.size = Pt(tamanho)
    # Sem isto o Word ignora a fonte em alguns idiomas/caracteres
    rpr = fonte.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for atributo in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(atributo), nome)
    # Os títulos do modelo padrão usam a fonte do tema, que tem prioridade sobre a definida acima
    for atributo in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(atributo)) is not None:
            del rfonts.attrib[qn(atributo)]


def sombrear(paragrafo, cor):
    ppr = paragrafo._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), cor)
    ppr.append(shd)


def bloco_monoespacado(doc, linhas):
    """Código ou saída: uma linha por parágrafo, sem recuo, fundo cinza-claro."""
    for linha in linhas:
        p = doc.add_paragraph()
        formato = p.paragraph_format
        formato.space_before = formato.space_after = Pt(0)
        formato.line_spacing = 1.0
        formato.left_indent = formato.first_line_indent = Cm(0)
        sombrear(p, CINZA_CODIGO)
        # Espaços preservados como estão: a indentação do código vem do próprio arquivo
        run = p.add_run(linha.replace("\t", "    ") or " ")
        definir_fonte(run.font, FONTE_CODIGO, 9)
    doc.add_paragraph()


def tabela(doc, linhas):
    celulas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in linhas if l.strip()]
    if not celulas:
        return
    colunas = max(len(l) for l in celulas)
    t = doc.add_table(rows=len(celulas), cols=colunas)
    t.style = "Table Grid"
    for i, linha in enumerate(celulas):
        for j in range(colunas):
            texto = linha[j] if j < len(linha) else ""
            par = t.cell(i, j).paragraphs[0]
            run = par.add_run(texto)
            definir_fonte(run.font, FONTE_TEXTO, 10)
            run.font.bold = i == 0
    doc.add_paragraph()


def paragrafo(doc, partes):
    if partes:
        doc.add_paragraph(" ".join(partes))


# ---------- montagem ----------

def montar_arquivo(doc, relativo, dados):
    linhas = [substituir_chaves(l, dados) for l in ler_texto(relativo)]
    acumulado = []      # linhas do parágrafo em andamento
    em_tabela = None    # linhas da tabela em andamento

    for linha in linhas:
        limpa = linha.strip()

        if em_tabela is not None:
            if limpa == "[[/TABELA]]":
                tabela(doc, em_tabela)
                em_tabela = None
            else:
                em_tabela.append(linha)
            continue

        if limpa == "[[TABELA]]":
            paragrafo(doc, acumulado)
            acumulado = []
            em_tabela = []
            continue

        marca = MARCA_ARQUIVO.match(limpa)
        if marca or not limpa or limpa.startswith("#") or limpa.startswith("- "):
            paragrafo(doc, acumulado)
            acumulado = []

        if marca:
            tipo, alvo = marca.group(1), marca.group(2).strip()
            if tipo == "IMAGEM":
                if (RAIZ / alvo).is_file():
                    doc.add_picture(str(RAIZ / alvo), width=Cm(15))
                else:
                    print(f"Aviso: imagem não encontrada, ficou fora do documento: {alvo}")
            else:
                bloco_monoespacado(doc, ler_texto(alvo))
        elif not limpa:
            continue
        elif limpa.startswith("## "):
            doc.add_heading(limpa[3:], level=2)
        elif limpa.startswith("# "):
            doc.add_heading(limpa[2:], level=1)
        elif limpa.startswith("- "):
            doc.add_paragraph(limpa[2:], style="List Bullet")
        else:
            acumulado.append(limpa)

    if em_tabela is not None:
        abortar(f"[[TABELA]] sem [[/TABELA]] em {relativo}")
    paragrafo(doc, acumulado)


def conferir_tarefa3():
    texto = " ".join(l for l in ler_texto(ARQUIVO_TAREFA3) if not l.strip().startswith("#"))
    palavras = len(texto.split())
    if not PALAVRAS_MIN <= palavras <= PALAVRAS_MAX:
        print(f"Aviso: a Tarefa 3 tem {palavras} palavras; o esperado é de "
              f"{PALAVRAS_MIN} a {PALAVRAS_MAX} (10 a 20 linhas).")
    return palavras


def main():
    # No Windows, sem isto os acentos das mensagens saem trocados no Git Bash e em pipes
    for fluxo in (sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8")

    dados = ler_identificacao()

    # Confere tudo antes de começar, para não gerar um documento pela metade
    for relativo, _ in CONTEUDO:
        caminho(relativo)

    doc = Document()
    configurar_documento(doc)

    for relativo, pagina_nova in CONTEUDO:
        if pagina_nova:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        montar_arquivo(doc, relativo, dados)

    palavras = conferir_tarefa3()

    destino = RAIZ / SAIDA_DOCX
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    print(f"Tarefa 3: {palavras} palavras")
    print(f"Relatório gerado: {SAIDA_DOCX}")


if __name__ == "__main__":
    main()
