"""Simulador del registro (A08) y del balanceador ponderado (A09) sobre réplicas de inventario."""
from dataclasses import dataclass

from fastapi.testclient import TestClient


# Una réplica registrada: nombre, peso y cliente para hablarle
@dataclass
class Replica:
    instancia: str
    peso: int
    cliente: TestClient
    detenida: bool = False  # True simula "docker compose stop" de esta réplica

    # Chequeo de salud como el de Consul: GET /health debe dar 200
    def sana(self) -> bool:
        return not self.detenida and self.cliente.get("/health").status_code == 200


# Reparto ponderado: cada réplica sana aparece en la rueda tantas veces como su peso
class Balanceador:
    # Guarda las réplicas y el turno actual de la rueda
    def __init__(self, replicas: list[Replica]) -> None:
        self.replicas = replicas
        self._turno = 0

    # Solo las réplicas que pasan el chequeo de salud reciben tráfico
    def sanas(self) -> list[Replica]:
        return [r for r in self.replicas if r.sana()]

    # Envía la petición a la siguiente réplica de la rueda (pesos 3/2/1 → 3 turnos, 2 y 1)
    def get(self, ruta: str):
        rueda = [r for r in self.sanas() for _ in range(r.peso)]
        if not rueda:
            raise RuntimeError("No hay réplicas sanas")
        replica = rueda[self._turno % len(rueda)]
        self._turno += 1
        return replica.cliente.get(ruta)
