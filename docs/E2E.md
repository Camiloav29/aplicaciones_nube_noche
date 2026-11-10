# Bitácora de Integración E2E - MercadoAndino

## Salida de Ejecución Exitosa
Plataforma levantada correctamente con Docker Compose y validada con pruebas de contrato y salud.

## Bitácora de Problemas
- **Problema:** Sincronización de puertos en réplicas.
- **Solución:** Asignación explícita de PUERTO_SERVICIO y HOST_ANUNCIADO para evitar conflictos en la red Docker.
