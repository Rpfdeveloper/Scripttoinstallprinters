# Historial de cambios

## 1.0.1 — 2026-10-21

- Comprobación del texto de estado de `lpstat -r`: su código de salida puede ser cero con CUPS detenido.
- `LC_MESSAGES=C` explícito para que un idioma heredado no altere la lectura de estados y nombres de cola.
- Tres nuevas pruebas de regresión; 28 pruebas automatizadas en total. La simulación también verifica que no se invoque `lpstat`.
- Indicador de GitHub Actions y guía técnica en inglés para revisar el proyecto.
- La validación con una impresora física sigue pendiente.

## 1.0.0 — 2026-10-20

- Sustituido el menú incompleto por una CLI con parámetros y ayuda.
- Configuración IPP Everywhere o PPD local, sin descargar controladores.
- Modo `--dry-run`, validación de entradas y argumentos Bash sin `eval`.
- Protección de colas existentes con actualización explícita.
- Comprobaciones de CUPS local y resultado de la operación.
- Entrada de compatibilidad con el nombre original del script.
- 25 pruebas automatizadas y procedimiento de validación con hardware.

## Prototipo original

Menús por fabricante y descargas directas, con ramas incompletas y asignaciones de modelos que necesitaban revisión. Se conserva en el historial Git.
