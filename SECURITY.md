# Política de Seguridad

## Versiones Soportadas

| Versión | Soporte de seguridad |
|---------|----------------------|
| 1.x     | ✅ Activo            |

## Reportar una Vulnerabilidad

Si encuentras una vulnerabilidad de seguridad en este proyecto, **no abras un issue público**.

Por favor, repórtala de forma responsable enviando un correo a:

📧 **sebastian.miranda@arcaoexdi.com**

Incluye en tu reporte:
- Descripción detallada de la vulnerabilidad
- Pasos para reproducirla
- Impacto potencial
- Sugerencia de corrección (si tienes una)

### Qué esperar

- Confirmación de recepción en menos de 48 horas
- Evaluación de severidad en menos de 7 días
- Parche y divulgación coordinada en menos de 30 días según complejidad

## Buenas Prácticas de Despliegue

Este repositorio es público con fines de portafolio. Si deseas desplegarlo en producción:

1. **Cambia el `SECRET_KEY`** en `.env` por una clave aleatoria larga (mínimo 32 caracteres)
2. **Usa PostgreSQL** en lugar de SQLite para entornos de producción
3. **Configura HTTPS** con un certificado válido (Let's Encrypt)
4. **Restringe CORS** a los dominios reales de tu frontend
5. **No expongas `/docs` ni `/redoc`** en producción (desactívalos en `config.py`)
6. **Aplica rate limiting** en los endpoints de autenticación
7. **Revisa las dependencias** periódicamente con `pip audit`

## Alcance

Este proyecto gestiona datos operativos de un taller pequeño. No almacena:
- Datos de tarjetas de crédito
- Información financiera sensible (solo montos de facturas)
- Datos de salud

Los campos más sensibles son: nombre del cliente, cédula/RUC y número de teléfono.
