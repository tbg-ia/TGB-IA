# Plataforma de Trading de Criptomonedas

## Descripción
Plataforma web para trading de criptomonedas con bot automatizado. Permite a los usuarios realizar operaciones de trading manual y automatizado según su plan de suscripción.

## Características Principales
- Sistema de autenticación de usuarios
- Panel de administración
- Panel de usuario con diferentes niveles de acceso
- Bot de trading automatizado
- Integración con exchanges de criptomonedas
- Sistema de suscripciones (Basic/Pro)

## Estructura del Proyecto
```
/mi_plataforma/
├── app/                               # Directorio principal
│   ├── __init__.py                   # Inicialización de Flask
│   ├── config.py                     # Configuración
│   ├── routes/                       # Rutas de la aplicación
│   │   ├── auth.py                   # Autenticación
│   │   └── crypto.py                 # Trading
│   ├── models/                       # Modelos de datos
│   │   ├── user.py                   # Modelo de Usuario
│   │   └── trading_bot.py            # Modelo del Bot
│   ├── templates/                    # Plantillas HTML
│   │   ├── admin/                    # Vistas de administrador
│   │   └── public/                   # Vistas públicas
│   └── auth/                         # Lógica de autenticación
│       └── decorators.py             # Decoradores de permisos
├── migrations/                       # Migraciones de base de datos
└── run.py                           # Punto de entrada
```

## Requisitos
- Python 3.x
- PostgreSQL
- Dependencias en requirements.txt

## Configuración
1. Clonar el repositorio
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Configurar variables de entorno:
   - DATABASE_URL
   - FLASK_SECRET_KEY
   - BINANCE_API_KEY
   - BINANCE_API_SECRET

## Niveles de Usuario
### Usuario Básico
- Trading manual
- Análisis de mercado básico
- Dashboard personalizado

### Usuario Pro
- Trading automatizado
- Análisis avanzado
- Soporte prioritario
- Acceso a bots de trading

### Administrador
- Gestión de usuarios
- Monitoreo de bots
- Configuración del sistema

## Desarrollo
El proyecto está desarrollado en Flask con:
- Flask-SQLAlchemy para la base de datos
- Flask-Login para autenticación
- Bootstrap para el frontend
- Python-Binance para integración con Binance

## Estado del Proyecto
En desarrollo activo. Características principales implementadas:
- [x] Sistema de autenticación
- [x] Panel de administración
- [x] Dashboard de usuario
- [ ] Integración completa con Binance
- [ ] Sistema de notificaciones
- [ ] Más exchanges y pares de trading
