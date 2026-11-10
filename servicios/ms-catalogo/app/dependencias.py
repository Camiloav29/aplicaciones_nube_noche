from typing import Annotated
from fastapi import Depends, Request
from app.config import Configuracion, get_configuracion
from app.repositorios.base import RepositorioProductos
from app.servicios.catalogo import ServicioCatalogo

ConfigDep = Annotated[Configuracion, Depends(get_configuracion)]


def get_repositorio(request: Request) -> RepositorioProductos:
    return request.app.state.repositorio


RepoDep = Annotated[RepositorioProductos, Depends(get_repositorio)]


def get_servicio_catalogo(repo: RepoDep, config: ConfigDep) -> ServicioCatalogo:
    return ServicioCatalogo(repositorio=repo, max_pagina=config.pagina_tamano_maximo)


ServicioCatalogoDep = Annotated[ServicioCatalogo, Depends(get_servicio_catalogo)]
