"""Simulador del registro (A08) y del balanceador ponderado (A09) sobre réplicas de inventario."""
from dataclasses import dataclass

from fastapi.testclient import TestClient


@dataclass
class Replica:
    """Una réplica registrada: nombre, peso y cliente para hablarle."""

    instancia: str
    peso: int
    cliente: TestClient
    detenida: bool = False

    def sana(self) -> bool:
        """Chequeo de salud como el de Consul: GET /health debe dar 200."""
        return not self.detenida and self.cliente.get("/health").status_code == 200


class Balanceador:
    """Reparto ponderado: cada réplica sana aparece en la rueda tantas veces como su peso."""

    def __init__(self, replicas: list[Replica]) -> None:
        self.replicas = replicas
        self._turno = 0

    def sanas(self) -> list[Replica]:
        """Solo las réplicas que pasan el chequeo de salud reciben tráfico."""
        return [r for r in self.replicas if r.sana()]

    def get(self, ruta: str):
        """Envía la petición a la siguiente réplica de la rueda."""
        rueda = [r for r in self.sanas() for _ in range(r.peso)]
        if not rueda:
            raise RuntimeError("No hay réplicas sanas")
        replica = rueda[self._turno % len(rueda)]
        self._turno += 1
        return replica.cliente.get(ruta)
