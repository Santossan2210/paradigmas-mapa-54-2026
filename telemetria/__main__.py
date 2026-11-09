"""
Inicia o sistema: sobe o servidor local e abre o navegador.

    python -m telemetria                 (porta 8000, abre o navegador)
    python -m telemetria --porta 8080
    python -m telemetria --sem-navegador

Autor: Antonio Santos
"""

import argparse
import errno
import sys
import threading
import webbrowser
from pathlib import Path

from .servico import SistemaTelemetria
from .web import criar_servidor

BANCO_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "telemetria.db"
TENTATIVAS_DE_PORTA = 10


def main():
    # O console do Windows nem sempre usa UTF-8; sem isto os acentos podem sair trocados
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Sistema de telemetria da frota EcoFleet")
    parser.add_argument("--porta", type=int, default=8000, help="porta do servidor local (padrão 8000)")
    parser.add_argument("--banco", default=str(BANCO_PADRAO), help="arquivo do banco de dados SQLite")
    parser.add_argument("--sem-navegador", action="store_true", help="não abrir o navegador automaticamente")
    args = parser.parse_args()

    sistema = SistemaTelemetria(args.banco)

    # Se a porta estiver ocupada, tenta as seguintes
    servidor = None
    for porta in range(args.porta, args.porta + TENTATIVAS_DE_PORTA):
        try:
            servidor = criar_servidor(sistema, porta)
            break
        except OSError as erro:
            if erro.errno not in (errno.EADDRINUSE, 10048):   # 10048: porta em uso no Windows
                raise
    if servidor is None:
        sys.exit(f"Nenhuma porta livre entre {args.porta} e {args.porta + TENTATIVAS_DE_PORTA - 1}.")

    endereco = f"http://127.0.0.1:{servidor.server_address[1]}/"
    print("Telemetria EcoFleet em execução.")
    print(f"  Endereço: {endereco}")
    print(f"  Dados:    {Path(args.banco).resolve()}")
    print("Para encerrar, feche esta janela ou pressione Ctrl+C.")

    if not args.sem_navegador:
        threading.Timer(0.5, webbrowser.open, args=(endereco,)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nSistema encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
