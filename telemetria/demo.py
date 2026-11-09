"""
Demonstração no terminal, conforme o enunciado: uma van e uma bicicleta saem
com a bateria em 100% e fazem uma viagem de 50 km cada.

    python -m telemetria.demo

Autor: Antonio Santos
"""

import sys

from .modelo import BicicletaEletrica, VanEletrica


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    van = VanEletrica(1, "EcoCargo E-Van 1500", 1500.0, 100.0, "ECO1A26")
    bicicleta = BicicletaEletrica(2, "EcoBike Urban 25", 30.0, 100.0, 25.0)

    print("=== EcoFleet Solutions S.A. - Telemetria da Frota ===")

    # Mesma chamada, comportamento diferente em cada tipo de veículo (polimorfismo)
    for veiculo in (van, bicicleta):
        restante = veiculo.registrar_viagem(50.0)
        print(f"[{veiculo.ROTULO}] Distância percorrida: 50.0 km | Bateria restante: {restante:.1f}%")

    print("--- Nível final de bateria ---")
    print(f"Van elétrica: {van.get_autonomia_bateria():.1f}%")
    print(f"Bicicleta elétrica: {bicicleta.get_autonomia_bateria():.1f}%")


if __name__ == "__main__":
    main()
