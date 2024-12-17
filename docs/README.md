
# Plataforma de Trading - Documentación

## Descripción
Plataforma web para trading de criptomonedas y forex con soporte para bots automatizados y diferentes planes de suscripción.

## Características
- Trading manual y automatizado
- Integración con múltiples exchanges (Binance, BingX, Oanda)
- Sistema de suscripciones con período de prueba
- Panel de administración
- Gestión de usuarios y permisos
- Procesamiento de pagos con Stripe
- Sistema de notificaciones por email

## Estructura del Proyecto
```
/app/
├── api/                # API endpoints
├── auth/              # Autenticación
├── billing/           # Gestión de pagos
├── email/             # Sistema de emails
├── forms/             # Formularios
├── integrations/      # Integraciones con exchanges
├── mail/              # Plantillas de email
├── models/            # Modelos de datos
├── routes/            # Rutas de la aplicación
├── static/            # Archivos estáticos
└── templates/         # Plantillas HTML
```

## Módulos Principales
1. Trading (Crypto/Forex)
2. Gestión de Suscripciones
3. Facturación
4. Panel de Administración
5. Sistema de Notificaciones

## Estado Actual
- [x] Sistema de autenticación
- [x] Integración con Stripe
- [x] Trading manual
- [x] Trading automatizado
- [x] Gestión de suscripciones
- [x] Panel de administración
