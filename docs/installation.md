# Guía de Instalación

## Requisitos Previos
- Python 3.x
- PostgreSQL
- pip (gestor de paquetes de Python)

## Pasos de Instalación

### 1. Clonar el Repositorio
```bash
git clone [url-del-repositorio]
cd mi_plataforma
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:
```env
DATABASE_URL=postgresql://[usuario]:[contraseña]@[host]:[puerto]/[base_de_datos]
FLASK_SECRET_KEY=[clave-secreta]
BINANCE_API_KEY=[tu-api-key]
BINANCE_API_SECRET=[tu-api-secret]
```

### 4. Inicializar la Base de Datos
```bash
flask db upgrade
```

### 5. Ejecutar la Aplicación
```bash
python run.py
```

## Verificación de la Instalación
1. Abrir un navegador web
2. Visitar `http://localhost:5000`
3. Deberías ver la página de inicio de la plataforma

## Solución de Problemas Comunes
- Error de conexión a la base de datos: Verificar credenciales en DATABASE_URL
- Error de dependencias: Asegurar que todas las dependencias están instaladas
- Error de permisos: Verificar permisos de escritura en el directorio

## Actualizaciones
Para actualizar la aplicación:
1. Obtener últimos cambios
2. Reinstalar dependencias si es necesario
3. Ejecutar migraciones pendientes
