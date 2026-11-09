"""
Gravação e leitura dos dados em SQLite (arquivo local, sem servidor).

Autor: Antonio Santos
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from .modelo import TIPOS, VanEletrica

ESQUEMA = """
CREATE TABLE IF NOT EXISTS veiculos (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo              TEXT    NOT NULL CHECK (tipo IN ('van', 'bicicleta')),
    modelo            TEXT    NOT NULL,
    capacidade_carga  REAL    NOT NULL,
    autonomia_bateria REAL    NOT NULL,
    placa             TEXT,
    limite_velocidade REAL,
    criado_em         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS viagens (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id      INTEGER NOT NULL REFERENCES veiculos(id) ON DELETE CASCADE,
    distancia       REAL    NOT NULL,
    bateria_inicial REAL    NOT NULL,
    bateria_final   REAL    NOT NULL,
    consumo         REAL    NOT NULL,
    registrada_em   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS ajustes_bateria (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id      INTEGER NOT NULL REFERENCES veiculos(id) ON DELETE CASCADE,
    valor_informado REAL    NOT NULL,
    valor_gravado   REAL    NOT NULL,
    registrado_em   TEXT    NOT NULL
);
"""


def agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Repositorio:
    """Cada instância abre a sua própria conexão. Use com `with`."""

    def __init__(self, caminho_banco):
        self.caminho = Path(caminho_banco)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(self.caminho)
        self.conexao.row_factory = sqlite3.Row
        self.conexao.execute("PRAGMA foreign_keys = ON")
        self.conexao.executescript(ESQUEMA)

    def __enter__(self):
        return self

    def __exit__(self, tipo_erro, *_):
        if tipo_erro is None:
            self.conexao.commit()
        else:
            self.conexao.rollback()
        self.conexao.close()

    # ---- veículos ----

    def inserir_veiculo(self, tipo, modelo, capacidade, bateria, placa, limite):
        cursor = self.conexao.execute(
            "INSERT INTO veiculos (tipo, modelo, capacidade_carga, autonomia_bateria,"
            " placa, limite_velocidade, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tipo, modelo, capacidade, bateria, placa, limite, agora()),
        )
        return cursor.lastrowid

    def atualizar_bateria(self, veiculo_id, bateria):
        self.conexao.execute(
            "UPDATE veiculos SET autonomia_bateria = ? WHERE id = ?", (bateria, veiculo_id))

    def excluir_veiculo(self, veiculo_id):
        self.conexao.execute("DELETE FROM veiculos WHERE id = ?", (veiculo_id,))

    def buscar_veiculo(self, veiculo_id):
        linha = self.conexao.execute(
            "SELECT * FROM veiculos WHERE id = ?", (veiculo_id,)).fetchone()
        return self._para_objeto(linha) if linha else None

    def travar_escrita(self):
        """
        Abre a transação já reservando a escrita. Assim, entre conferir se a placa
        existe e gravar o veículo, nenhum outro pedido (um clique duplo, por
        exemplo) consegue gravar no meio.
        """
        if not self.conexao.in_transaction:
            self.conexao.execute("BEGIN IMMEDIATE")

    def placa_em_uso(self, placa):
        """Compara sem o hífen, para ABC-1234 e ABC1234 contarem como a mesma placa."""
        linha = self.conexao.execute(
            "SELECT 1 FROM veiculos WHERE REPLACE(placa, '-', '') = REPLACE(?, '-', '')",
            (placa,)).fetchone()
        return linha is not None

    def listar_veiculos(self):
        linhas = self.conexao.execute("SELECT * FROM veiculos ORDER BY id").fetchall()
        return [self._para_objeto(linha) for linha in linhas]

    @staticmethod
    def _para_objeto(linha):
        """Recria o objeto da classe certa a partir da linha do banco."""
        classe = TIPOS[linha["tipo"]]
        extra = linha["placa"] if classe is VanEletrica else linha["limite_velocidade"]
        return classe(linha["id"], linha["modelo"], linha["capacidade_carga"],
                      linha["autonomia_bateria"], extra)

    # ---- viagens e ajustes ----

    def inserir_viagem(self, veiculo_id, distancia, bateria_inicial, bateria_final, consumo):
        cursor = self.conexao.execute(
            "INSERT INTO viagens (veiculo_id, distancia, bateria_inicial, bateria_final,"
            " consumo, registrada_em) VALUES (?, ?, ?, ?, ?, ?)",
            (veiculo_id, distancia, bateria_inicial, bateria_final, consumo, agora()),
        )
        return cursor.lastrowid

    def inserir_ajuste(self, veiculo_id, valor_informado, valor_gravado):
        self.conexao.execute(
            "INSERT INTO ajustes_bateria (veiculo_id, valor_informado, valor_gravado,"
            " registrado_em) VALUES (?, ?, ?, ?)",
            (veiculo_id, valor_informado, valor_gravado, agora()),
        )

    def listar_viagens(self, veiculo_id=None):
        sql = ("SELECT v.*, ve.modelo, ve.tipo FROM viagens v"
               " JOIN veiculos ve ON ve.id = v.veiculo_id")
        parametros = ()
        if veiculo_id is not None:
            sql += " WHERE v.veiculo_id = ?"
            parametros = (veiculo_id,)
        sql += " ORDER BY v.id DESC"
        return [dict(linha) for linha in self.conexao.execute(sql, parametros).fetchall()]
