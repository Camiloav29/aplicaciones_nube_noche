import os
import httpx
import structlog

logger = structlog.get_logger()


def obtener_id_instancia() -> tuple[str, str, str, int, int, str]:
    consul_url = os.getenv("CONSUL_URL", "http://localhost:8500")
    nombre = os.getenv("NOMBRE_SERVICIO", "ms-catalogo")
    host = os.getenv("HOST_ANUNCIADO", "localhost")
    puerto = int(os.getenv("PUERTO_SERVICIO", "8001"))
    peso = int(os.getenv("PESO_SERVICIO", "1"))
    instancia_id = f"{nombre}-{host}-{puerto}"
    return consul_url, instancia_id, nombre, puerto, peso, host


async def registrar_en_consul(cliente: httpx.AsyncClient) -> str:
    consul_url, instancia_id, nombre, puerto, peso, host = obtener_id_instancia()
    payload = {
        "ID": instancia_id,
        "Name": nombre,
        "Address": host,
        "Port": puerto,
        "Tags": [f"peso={peso}"],
        "Check": {
            "HTTP": f"http://{host}:{puerto}/health",
            "Interval": "5s",
            "Timeout": "2s",
            "DeregisterCriticalServiceAfter": "20s",
        },
    }
    try:
        resp = await cliente.put(f"{consul_url}/v1/agent/service/register", json=payload)
        resp.raise_for_status()
        logger.info("consul_registrado", instancia_id=instancia_id)
    except httpx.HTTPError as exc:
        logger.warning("consul_no_disponible_al_registrar", error=str(exc))
    return instancia_id


async def cancelar_en_consul(cliente: httpx.AsyncClient, instancia_id: str) -> None:
    consul_url, *_ = obtener_id_instancia()
    try:
        resp = await cliente.put(f"{consul_url}/v1/agent/service/deregister/{instancia_id}")
        resp.raise_for_status()
        logger.info("consul_cancelado", instancia_id=instancia_id)
    except httpx.HTTPError as exc:
        logger.warning("consul_no_disponible_al_cancelar", error=str(exc))
