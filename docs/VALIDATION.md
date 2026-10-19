# Validación con una impresora real

Este procedimiento está pendiente de ejecución con hardware. Las pruebas automatizadas utilizan CUPS simulado y no acreditan compatibilidad con un modelo.

1. Anota la distribución, versión de Bash, versión de CUPS, fabricante, modelo y firmware. Usa una cola de prueba con nombre nuevo.
2. Comprueba que CUPS local está activo: `lpstat -h localhost -r`. Guarda la configuración actual si vas a utilizar `--update`.
3. Obtén la URI real de la impresora. Para IPP Everywhere, comprueba que el equipo lo admita. Para PPD, registra su origen y versión e instala los filtros del fabricante que requiera.
4. Ejecuta primero `--dry-run` y revisa la URI, el nombre y la modalidad. La simulación no comprueba conectividad ni colas existentes.
5. Aplica el mismo comando sin `--dry-run` con un usuario autorizado en CUPS.
6. Comprueba la cola: `lpstat -h localhost -p NOMBRE` y `lpstat -h localhost -v NOMBRE`.
7. Envía una página de prueba explícitamente: `lp -h localhost -d NOMBRE /ruta/a/prueba.pdf`. La utilidad no imprime automáticamente.
8. Verifica en papel el resultado y comprueba las opciones disponibles con `lpoptions -h localhost -p NOMBRE -l`. No des por hecho que dúplex, color o acabados están disponibles.
9. Repite el alta sin `--update`: debe rechazar la modificación. Prueba `--update` únicamente sobre la cola de prueba y revisa sus opciones después.
10. Registra el resultado y elimina manualmente la cola de prueba desde CUPS cuando termines. No elimines una cola con trabajos pendientes sin revisarlos.

## Registro

| Campo | Resultado |
| --- | --- |
| Fecha y persona que valida | Pendiente |
| Distribución / Bash / CUPS | Pendiente |
| Modelo / firmware | Pendiente |
| Modalidad y URI sin credenciales | Pendiente |
| Origen y versión del PPD, si procede | Pendiente |
| Creación y consulta de cola | Pendiente |
| Impresión física | Pendiente |
| Protección de cola existente | Pendiente |
| Actualización explícita | Pendiente |
| Incidencias y limitaciones | Pendiente |
