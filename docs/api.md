# Documentación de la API

## Descripción General
API RESTful para interactuar con la plataforma de trading de criptomonedas.

## Autenticación
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "usuario@ejemplo.com",
  "password": "contraseña"
}
```

### Respuesta
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "usuario@ejemplo.com",
    "subscription": "pro"
  }
}
```

## Endpoints

### Trading

#### Obtener Bots Activos
```http
GET /api/bots
Authorization: Bearer [token]
```

#### Crear Bot
```http
POST /api/bots
Authorization: Bearer [token]
Content-Type: application/json

{
  "strategy": "grid",
  "trading_pair": "BTC/USDT",
  "max_position": 1000
}
```

### Usuario

#### Perfil de Usuario
```http
GET /api/user/profile
Authorization: Bearer [token]
```

#### Actualizar Suscripción
```http
PUT /api/user/subscription
Authorization: Bearer [token]
Content-Type: application/json

{
  "plan": "pro"
}
```

## Modelos de Datos

### Usuario
```typescript
interface User {
  id: number;
  username: string;
  email: string;
  subscription_type: "basic" | "pro";
  subscription_expires: string;
}
```

### Bot de Trading
```typescript
interface TradingBot {
  id: number;
  user_id: number;
  strategy: string;
  trading_pair: string;
  active: boolean;
  max_position: number;
}
```

## Códigos de Estado
- 200: Éxito
- 400: Error de solicitud
- 401: No autorizado
- 403: Prohibido
- 404: No encontrado
- 500: Error interno

## Límites de Rate
- 100 solicitudes por minuto por IP
- 1000 solicitudes por hora por usuario

## Ejemplos de Uso

### Python
```python
import requests

api_url = "https://api.plataforma.com"
token = "your-token"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Obtener bots activos
response = requests.get(f"{api_url}/api/bots", headers=headers)
bots = response.json()
```
