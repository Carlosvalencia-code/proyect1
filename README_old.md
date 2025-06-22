# 🎨 Synthia Style Backend

Backend moderno y escalable para la aplicación de análisis de estilo personal Synthia Style, construido con **FastAPI**, **PostgreSQL**, **Prisma ORM** y sistema avanzado de suscripciones.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Características Principales

### ✨ Funcionalidades Core
- 🤖 **Análisis Facial con IA** - Análisis de forma de rostro y características usando Google Gemini
- 🌈 **Análisis Cromático** - Determinación de paleta de colores personal
- 👤 **Sistema de Usuarios Avanzado** - Perfiles extendidos, preferencias y analytics
- 📊 **Sistema de Suscripciones** - FREE, PREMIUM, PRO, ENTERPRISE con límites dinámicos
- 📈 **Analytics Integrados** - Tracking de uso, patrones de comportamiento y métricas
- 🎯 **Onboarding Personalizado** - Guía paso a paso para nuevos usuarios
- 📁 **Gestión de Archivos** - Subida, validación y optimización de imágenes

### 🛠️ Stack Tecnológico
- **Framework**: FastAPI 0.104+ con validación automática de datos
- **Base de Datos**: PostgreSQL 15+ con Prisma ORM
- **Autenticación**: JWT tokens con refresh tokens
- **IA/ML**: Google Gemini API 1.5 Flash
- **Cache**: Redis (opcional para performance)
- **Logging**: Structured logging con rotación
- **Containerización**: Docker & Docker Compose
- **Testing**: Pytest con coverage
- **Documentation**: OpenAPI/Swagger automático

## 🏗️ Arquitectura del Proyecto

```
synthia-backend/
├── 📁 app/                          # Código principal de la aplicación
│   ├── main.py                      # ⚡ Punto de entrada FastAPI
│   ├── 📁 core/                     # 🔧 Configuración central
│   │   ├── config.py                # Variables de entorno
│   │   ├── security.py              # JWT, hashing, validaciones
│   │   └── logging.py               # Sistema de logs estructurado
│   ├── 📁 api/v1/                   # 🌐 API versión 1
│   │   ├── api.py                   # Router principal
│   │   ├── 📁 endpoints/            # Endpoints específicos
│   │   │   ├── auth.py              # Autenticación y registro
│   │   │   ├── users.py             # Gestión avanzada de usuarios
│   │   │   ├── facial_analysis.py   # Análisis facial con IA
│   │   │   ├── chromatic_analysis.py # Análisis cromático
│   │   │   ├── feedback.py          # Sistema de feedback
│   │   │   └── files.py             # Gestión de archivos
│   │   └── 📁 dependencies/         # Dependencias de FastAPI
│   ├── 📁 db/                       # 🗄️ Capa de base de datos
│   │   └── database.py              # Cliente Prisma y conexiones
│   ├── 📁 models/                   # 📋 Modelos (generados por Prisma)
│   ├── 📁 schemas/                  # 📝 Esquemas Pydantic
│   │   ├── user.py                  # Esquemas de usuario extendidos
│   │   ├── facial_analysis.py       # Esquemas de análisis facial
│   │   ├── chromatic_analysis.py    # Esquemas de análisis cromático
│   │   ├── auth.py                  # Esquemas de autenticación
│   │   ├── feedback.py              # Esquemas de feedback
│   │   └── common.py                # Esquemas comunes
│   ├── 📁 services/                 # 🔄 Lógica de negocio
│   │   ├── user_service.py          # Servicio de usuarios avanzado
│   │   ├── gemini_service.py        # Integración con Gemini AI
│   │   └── file_service.py          # Servicio de archivos
│   └── 📁 utils/                    # 🧰 Utilidades
├── 📁 prisma/                       # 🗃️ ORM Prisma
│   └── schema.prisma                # Esquema de base de datos
├── 📁 scripts/                      # 📜 Scripts auxiliares
│   └── migrate_and_seed.py          # Migración y datos iniciales
├── 📁 tests/                        # 🧪 Tests automatizados
├── 📁 docs/                         # 📚 Documentación
├── 📁 logs/                         # 📄 Archivos de log
├── 📁 uploads/                      # 📎 Archivos subidos
├── docker-compose.yml               # 🐳 Servicios Docker
├── Dockerfile                       # 🐳 Imagen del backend
├── requirements.txt                 # 📦 Dependencias Python
├── .env.example                     # ⚙️ Variables de entorno ejemplo
└── setup.py                         # 🔧 Script de configuración
```

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **Python**: 3.11 o superior
- **PostgreSQL**: 15 o superior
- **Node.js**: 18+ (para Prisma CLI)
- **RAM**: 2GB mínimo (4GB recomendado)
- **Almacenamiento**: 1GB libre

### APIs Externas
- **Google Gemini API**: Clave API válida
- **Redis**: Opcional para cache (recomendado en producción)

## 🚀 Instalación y Configuración

### 🔧 Método 1: Configuración Automática (Recomendado)

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd synthia-backend

# 2. Ejecutar script de configuración automática
python setup.py

# 3. Seguir las instrucciones en pantalla
```

### 🔨 Método 2: Configuración Manual

#### 1. **Preparar el entorno**
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Actualizar pip
pip install --upgrade pip
```

#### 2. **Instalar dependencias**
```bash
# Instalar dependencias Python
pip install -r requirements.txt

# Instalar Prisma CLI (requiere Node.js)
npm install prisma @prisma/client
```

#### 3. **Configurar variables de entorno**
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus configuraciones
nano .env  # o tu editor preferido
```

**Variables críticas a configurar:**
```env
DATABASE_URL="postgresql://synthia:synthia123@localhost:5432/synthiadb"
GEMINI_API_KEY="tu_api_key_de_gemini_aqui"
JWT_SECRET_KEY="clave_secreta_super_segura"
```

#### 4. **Configurar base de datos**
```bash
# Opción A: PostgreSQL local
createdb synthiadb

# Opción B: Docker
docker run --name synthia-postgres \
  -e POSTGRES_DB=synthiadb \
  -e POSTGRES_USER=synthia \
  -e POSTGRES_PASSWORD=synthia123 \
  -p 5432:5432 -d postgres:15

# Generar cliente Prisma
npx prisma generate

# Ejecutar migraciones y datos iniciales
python scripts/migrate_and_seed.py
```

### 🐳 Método 3: Docker Compose (Más Fácil)

```bash
# Clonar y navegar al directorio
git clone <repository-url>
cd synthia-backend

# Copiar variables de entorno
cp .env.example .env
# Editar .env con GEMINI_API_KEY

# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f synthia-backend

# La aplicación estará disponible en http://localhost:8000
```

## 🎯 Uso y Operación

### ▶️ Iniciar el Servidor

#### Desarrollo:
```bash
# Método 1: Script personalizado
python run.py

# Método 2: Uvicorn directo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Método 3: Con hot reload avanzado
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```

#### Producción:
```bash
# Con Gunicorn (recomendado)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Docker
docker-compose -f docker-compose.prod.yml up -d
```

### 🌐 Endpoints Principales

Una vez ejecutándose, la API estará disponible en:

- **API Base**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Métricas**: http://localhost:8000/metrics

#### Endpoints Clave:
```
🔐 Autenticación:
POST   /api/v1/auth/register         # Registro de usuario
POST   /api/v1/auth/login            # Login
POST   /api/v1/auth/refresh          # Refresh token

👤 Usuarios:
GET    /api/v1/users/profile         # Perfil del usuario
PUT    /api/v1/users/profile         # Actualizar perfil
GET    /api/v1/users/dashboard       # Dashboard completo
GET    /api/v1/users/analytics       # Analytics del usuario
GET    /api/v1/users/onboarding      # Estado de onboarding

📊 Análisis:
POST   /api/v1/facial/analyze        # Análisis facial con IA
POST   /api/v1/chromatic/analyze     # Análisis cromático
GET    /api/v1/facial/history        # Historial de análisis

💎 Suscripciones:
GET    /api/v1/users/subscription/features  # Features del tier
GET    /api/v1/users/subscription/usage     # Límites de uso
POST   /api/v1/users/subscription/upgrade   # Upgrade de plan
```

### 🗄️ Gestión de Base de Datos

```bash
# Ver base de datos en navegador
npx prisma studio

# Ejecutar migraciones
npx prisma migrate dev

# Resetear base de datos (desarrollo)
npx prisma migrate reset

# Deploy de migraciones (producción)
npx prisma migrate deploy

# Generar nuevo cliente después de cambios
npx prisma generate

# Seed datos de prueba
python scripts/migrate_and_seed.py
```

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
python -m pytest

# Con coverage
python -m pytest --cov=app

# Tests específicos
python -m pytest tests/test_auth.py

# Tests con output verbose
python -m pytest -v

# Tests en paralelo
python -m pytest -n auto
```

### Estructura de Tests
```
tests/
├── conftest.py              # Configuración de tests
├── test_auth.py            # Tests de autenticación
├── test_users.py           # Tests de usuarios
├── test_facial_analysis.py # Tests de análisis facial
├── test_chromatic_analysis.py # Tests de análisis cromático
└── test_subscriptions.py  # Tests de suscripciones
```

## 📊 Sistema de Suscripciones

### Tiers Disponibles

| Tier | Precio/Mes | Análisis/Mes | Análisis/Día | Features Principales |
|------|------------|--------------|--------------|---------------------|
| **FREE** | $0 | 5 | 2 | Análisis básico, historial 30 días |
| **PREMIUM** | $9.99 | 25 | 5 | Análisis avanzado, export, soporte |
| **PRO** | $29.99 | 100 | 10 | Multi-foto, reportes, consultas |
| **ENTERPRISE** | $99.99 | Ilimitado | Ilimitado | Todo incluido + estilista |

### Gestión de Límites
El sistema automáticamente:
- ✅ Verifica límites antes de cada análisis
- ✅ Bloquea análisis cuando se alcanza el límite
- ✅ Resetea contadores mensualmente
- ✅ Permite upgrades instantáneos
- ✅ Tracking detallado de uso

## 📈 Analytics y Monitoreo

### Analytics de Usuario
- 📊 Sesiones y tiempo de uso
- 🎯 Patrones de análisis
- 📈 Engagement y retención
- ⚡ Performance de IA
- 🚨 Detección de churn

### Logs del Sistema
```bash
# Ver logs en tiempo real
tail -f logs/synthia_backend.log

# Logs específicos por nivel
grep "ERROR" logs/synthia_backend.log
grep "WARNING" logs/synthia_backend.log

# Logs estructurados en JSON para análisis
cat logs/synthia_backend.log | jq '.'
```

### Métricas de Performance
- 🚀 Tiempo de respuesta API
- 💾 Uso de memoria y CPU
- 🗄️ Performance de base de datos
- 🌐 Rate limiting y throttling
- 📊 Análisis de carga

## 🔧 Configuración Avanzada

### Variables de Entorno Importantes

```env
# Performance
DATABASE_POOL_SIZE=10
REDIS_ENABLED=true
CACHE_TTL_SECONDS=3600

# Seguridad
RATE_LIMIT_ENABLED=true
BCRYPT_ROUNDS=12
SESSION_COOKIE_SECURE=true  # Solo HTTPS

# Features
FACIAL_ANALYSIS_ENABLED=true
SUBSCRIPTION_FEATURES_ENABLED=true
ANALYTICS_ENABLED=true

# Monitoring
SENTRY_DSN="tu_sentry_dsn"
LOG_LEVEL="INFO"
PROMETHEUS_METRICS=true
```

### Customización de Features

El sistema permite habilitar/deshabilitar features específicas:

```python
# En app/core/config.py
class Settings:
    facial_analysis_enabled: bool = True
    chromatic_analysis_enabled: bool = True
    subscription_features_enabled: bool = True
    analytics_features_enabled: bool = True
    admin_features_enabled: bool = True
```

## 🚀 Deployment en Producción

### 🌐 Deployment con Docker

```bash
# Build de imagen de producción
docker build -t synthia-backend:latest .

# Deploy con Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl http://localhost:8000/health
```

### ☁️ Deployment en Cloud

#### AWS ECS/Fargate:
```bash
# Tag para ECR
docker tag synthia-backend:latest your-account.dkr.ecr.region.amazonaws.com/synthia-backend:latest

# Push a ECR
docker push your-account.dkr.ecr.region.amazonaws.com/synthia-backend:latest
```

#### Google Cloud Run:
```bash
# Build y deploy
gcloud run deploy synthia-backend \
  --image gcr.io/your-project/synthia-backend \
  --platform managed \
  --region us-central1
```

#### Railway/Render/Heroku:
```bash
# Usar Dockerfile incluido
# Configurar variables de entorno en el panel
```

### 🔒 Configuración de Producción

**Variables críticas para producción:**
```env
ENVIRONMENT="production"
DEBUG=false
LOG_LEVEL="WARNING"
SESSION_COOKIE_SECURE=true
INCLUDE_IN_SCHEMA=false  # Ocultar docs
CORS_ORIGINS="https://tudominio.com"
DATABASE_URL="postgresql://user:pass@prod-host:5432/db"
REDIS_URL="redis://prod-redis:6379"
SENTRY_DSN="tu_sentry_dsn_produccion"
```

## 🛡️ Seguridad

### Medidas Implementadas
- 🔐 **JWT Tokens** con expiración y refresh
- 🔒 **Bcrypt** para hashing de contraseñas
- 🛡️ **Rate Limiting** por IP y usuario
- 🚫 **CORS** configurado específicamente
- 📝 **Validación** estricta de inputs
- 🔍 **SQL Injection** protección via Prisma
- 📊 **Logging** de eventos de seguridad

### Recomendaciones de Seguridad
1. **Cambiar secrets**: JWT_SECRET_KEY, DATABASE_PASSWORD
2. **HTTPS**: Usar certificados SSL/TLS
3. **Firewall**: Limitar acceso a puertos necesarios
4. **Backup**: Configurar backups regulares
5. **Monitoring**: Implementar alertas de seguridad
6. **Updates**: Mantener dependencias actualizadas

## 🤝 Desarrollo y Contribución

### 🔄 Flujo de Desarrollo

```bash
# 1. Fork y clone
git clone <your-fork>
cd synthia-backend

# 2. Crear rama de feature
git checkout -b feature/nueva-funcionalidad

# 3. Instalar en modo desarrollo
python setup.py
pip install -e .

# 4. Hacer cambios y tests
python -m pytest

# 5. Commit y push
git commit -m "feat: nueva funcionalidad"
git push origin feature/nueva-funcionalidad

# 6. Crear Pull Request
```

### 📝 Estándares de Código

```bash
# Formateo de código
black app/ scripts/ tests/

# Linting
flake8 app/
pylint app/

# Type checking
mypy app/

# Imports
isort app/
```

### 🏷️ Convenciones

- **Commits**: Usar [Conventional Commits](https://conventionalcommits.org/)
- **Ramas**: `feature/`, `bugfix/`, `hotfix/`, `release/`
- **Tests**: Mínimo 80% de coverage
- **Documentación**: Docstrings en todas las funciones

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. **Error de conexión a base de datos**
```bash
# Verificar PostgreSQL
psql -h localhost -U synthia -d synthiadb

# Verificar variables de entorno
echo $DATABASE_URL

# Verificar logs
tail -f logs/synthia_backend.log | grep "database"
```

#### 2. **Error de Gemini API**
```bash
# Verificar API key
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# Verificar cuota
# Revisar Google Cloud Console
```

#### 3. **Error de Prisma**
```bash
# Regenerar cliente
npx prisma generate

# Verificar esquema
npx prisma validate

# Resetear migraciones
npx prisma migrate reset
```

#### 4. **Performance lenta**
```bash
# Verificar logs de performance
grep "slow" logs/synthia_backend.log

# Habilitar métricas
PROMETHEUS_METRICS=true

# Verificar recursos
docker stats  # Si usas Docker
```

### 📞 Soporte

- 📚 **Documentación**: [Docs completas](docs/)
- 🐛 **Issues**: [GitHub Issues](link-to-issues)
- 💬 **Chat**: [Discord/Slack](link-to-chat)
- 📧 **Email**: support@synthiastyle.com

## 📚 Recursos Adicionales

### 📖 Documentación Técnica
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prisma Documentation](https://www.prisma.io/docs/)
- [Google Gemini API](https://ai.google.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### 🎓 Tutoriales y Guías
- [Guía de Setup Local](docs/setup-local.md)
- [Guía de Deployment](docs/deployment.md)
- [API Reference](docs/api-reference.md)
- [Arquitectura del Sistema](docs/architecture.md)

## 📄 Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

## 🙏 Agradecimientos

- **FastAPI**: Por el excelente framework
- **Prisma**: Por el ORM moderno
- **Google**: Por la API de Gemini
- **Comunidad Open Source**: Por las librerías utilizadas

---

⭐ **¿Te gusta el proyecto? ¡Dale una estrella!**

🐛 **¿Encontraste un bug? [Reportalo aquí](link-to-issues)**

💡 **¿Tienes una idea? [Compártela con nosotros](link-to-discussions)**

---

<div align="center">
  <strong>🎨 Hecho con ❤️ para Synthia Style</strong>
</div>
