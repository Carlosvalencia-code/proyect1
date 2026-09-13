# 🛍️ Synthia Commerce AI (Monorepo)

**Motor B2B de Visagismo y Colorimetría con IA para eCommerce de Moda y Óptica**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Visión General del Proyecto

**Synthia Commerce AI** es una solución B2B diseñada para marcas y tiendas online de moda, accesorios y óptica. Transforma la experiencia de compra en fichas de producto (PDP) integrando un **estilista virtual embebible** que asesora al cliente según la ciencia del visagismo (geometría facial) y la colorimetría estacional (subtono cálido/frío/neutro).

### ¿Qué problema resuelve?
* **Alta tasa de devoluciones en moda y óptica online** (estimada entre 25% y 40% en retail digital) debido a incompatibilidad estética con las facciones o el tono de piel del cliente.
* **Fricción de decisión en la PDP:** Los clientes dudan si una montura o color les favorecerá.
* **Seguridad y privacidad:** A diferencia de prototipos que filtran API keys en el navegador, Synthia procesa todas las inferencias y recomendaciones en un backend seguro multi-tenant.

---

## 🏛️ Estructura del Monorepo

```
proyect1/
├── apps/
│   ├── api/                  # Backend FastAPI (REST API, visagismo, matching de catálogo)
│   │   ├── app/
│   │   │   ├── api/v1/       # Endpoints v1 (Widget B2B, Auth, Wardrobe, Shopping)
│   │   │   ├── core/         # Configuración, logging, seguridad JWT, caché
│   │   │   ├── db/           # Adaptadores de base de datos (PostgreSQL/Prisma con fallback)
│   │   │   ├── schemas/      # Modelos de datos Pydantic v2
│   │   │   └── services/     # CatalogMatcher, GeminiService, CacheService
│   │   ├── prisma/           # Esquema de base de datos relacional
│   │   ├── tests/            # Suite de pruebas automatizadas (pytest)
│   │   └── requirements.txt  # Dependencias Python
│   │
│   ├── dashboard/            # Panel de usuario / comerciante (React + Vite + TypeScript)
│   │   ├── src/              # Componentes, vistas y contexto de análisis
│   │   └── package.json
│   │
│   └── widget/               # SDK y widget embebible para tiendas online
│       ├── src/
│       │   ├── synthia-widget.js   # Script Vanilla JS embebible (< 15 KB, sin dependencias)
│       │   └── synthia-widget.css  # Estilos UI glassmorphism y diseño responsivo
│       └── demo/
│           └── index.html          # Demo interactiva en ficha de producto (PDP) de óptica
│
├── deploy/                   # Infraestructura y despliegue (Docker Compose, Nginx, Prometheus)
└── scripts/                  # Scripts de migración, seeding y verificación
```

---

## 🚀 Inicio Rápido (Quickstart)

### 1. Requisitos Previos
* **Python 3.10+**
* **Node.js 18+** y npm
* *(Opcional)* Docker y Docker Compose para levantar PostgreSQL y Redis

### 2. Configurar y Ejecutar el Backend (`apps/api`)

```bash
# Navegar al directorio de la API
cd apps/api

# Crear y activar entorno virtual
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor de desarrollo
uvicorn app.main:app --reload --port 8000
```

> **Nota:** La API incluye mecanismos de tolerancia a fallos. Si PostgreSQL o Redis no están iniciados localmente, el servidor levantará en modo desarrollo utilizando almacenamiento en memoria y catálogos de demostración para el widget.

Acceso a la documentación interactiva OpenAPI:
* Swagger UI: `http://localhost:8000/docs`
* Health Check: `http://localhost:8000/api/v1/widget/health`

---

### 3. Ejecutar las Pruebas Automatizadas

```bash
cd apps/api
pytest tests/test_widget_b2b.py -v
```

**Resultado de la verificación:**
```
tests/test_widget_b2b.py::test_widget_health PASSED
tests/test_widget_b2b.py::test_merchant_catalog PASSED
tests/test_widget_b2b.py::test_widget_recommendation_round_face PASSED
tests/test_widget_b2b.py::test_widget_recommendation_square_face PASSED
========================= 4 passed in 3.33s =========================
```

---

### 4. Probar el Widget Embebible B2B (`apps/widget`)

El widget está diseñado en Vanilla JS puro sin dependencias externas para integrarse de forma no invasiva en cualquier plataforma (Shopify, WooCommerce, VTEX, Magento o sitios a medida).

1. Asegúrate de tener el backend corriendo en `http://localhost:8000`.
2. Abre en tu navegador el archivo demo:
   ```
   apps/widget/demo/index.html
   ```
   *(o sírvelo con cualquier servidor estático como `npx serve apps/widget/demo`)*.
3. Haz clic en **"✨ Probar con Asesor de Estilo Virtual (AI)"**.
4. Selecciona tu forma de rostro y subtono o sube una fotografía para calcular la armonía estilística y ver productos recomendados en tiempo real.

#### Código de Integración en Tienda (Ejemplo):
```html
<!-- 1. Estilos del Widget -->
<link rel="stylesheet" href="https://cdn.tusitio.com/synthia-widget.css">

<!-- 2. Contenedor en la PDP (junto al botón de Añadir al Carrito) -->
<div id="synthia-widget-container"></div>

<!-- 3. Script del Widget con Clave de Comercio y SKU -->
<script 
  src="https://cdn.tusitio.com/synthia-widget.js"
  data-synthia-auto-init="true"
  data-merchant-key="tu-clave-de-comercio"
  data-api-url="https://api.tudominio.com/api/v1/widget"
  data-sku="SKU-ACTUAL"
  data-container="#synthia-widget-container">
</script>
```

---

### 5. Iniciar el Dashboard Web (`apps/dashboard`)

```bash
cd apps/dashboard
npm install
npm run dev
```

El panel estará disponible en `http://localhost:5173`.

---

## 🔒 Arquitectura de Seguridad y Privacidad

1. **Sin filtración de credenciales cliente:**
   * Las llamadas de IA (Gemini API) se realizan exclusivamente a través de los servicios del backend (`apps/api/app/services/gemini_service.py`), evitando la exposición de `API_KEY` en los bundles de frontend.
2. **Autenticación Multi-Tenant:**
   * Cada comercio consumidor del widget se autentica mediante la cabecera HTTP `X-Merchant-Key`.
3. **Privacidad del Shopper:**
   * Las imágenes procesadas para visagismo se analizan en memoria de manera efímera para extracción de parámetros geométricos y no se persisten sin consentimiento explícito.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más información.
