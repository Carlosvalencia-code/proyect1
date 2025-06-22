# 🛍️ Guía del Sistema de Shopping y Afiliados - Synthia Style

## Descripción General

El sistema de shopping y afiliados de Synthia Style es un motor completo de recomendaciones inteligentes de compras que integra múltiples merchants, gestiona comisiones de afiliados y proporciona analytics avanzados.

## 🎯 Características Principales

### 1. Búsqueda de Productos Multi-Merchant
- Búsqueda concurrente en múltiples tiendas online
- Filtros avanzados por precio, categoría, marca, color, etc.
- Ranking inteligente por relevancia y calidad
- Cache optimizado para mejor performance

### 2. Motor de Recomendaciones Inteligentes
- Análisis del armario actual del usuario
- Recomendaciones personalizadas basadas en IA
- Identificación automática de gaps en el armario
- Sugerencias estacionales y por ocasión
- Optimización por presupuesto

### 3. Sistema de Afiliados Completo
- Integración con APIs de múltiples merchants
- Tracking automático de clicks y conversiones
- Gestión de comisiones y earnings
- Reportes detallados de performance
- Sistema de pagos automatizado

### 4. Gestión de Wishlist Inteligente
- Alertas de precio y stock
- Seguimiento de productos deseados
- Notificaciones automáticas de ofertas
- Priorización de compras

## 🚀 Configuración e Instalación

### 1. Variables de Entorno

Agregar al archivo `.env`:

```bash
# === Configuración de Merchants ===
# Amazon Associates
AMAZON_AFFILIATE_TAG=your_amazon_tag
AMAZON_ACCESS_KEY=your_amazon_access_key
AMAZON_SECRET_KEY=your_amazon_secret_key

# ASOS Affiliate
ASOS_AFFILIATE_TAG=your_asos_tag
ASOS_API_KEY=your_asos_api_key

# Otros merchants
ZARA_AFFILIATE_TAG=your_zara_tag
HM_AFFILIATE_TAG=your_hm_tag
UNIQLO_AFFILIATE_TAG=your_uniqlo_tag

# === Configuración de Shopping ===
SHOPPING_ENABLED=true
SHOPPING_CACHE_TTL=3600
SHOPPING_MAX_RESULTS_PER_MERCHANT=20
SHOPPING_CONCURRENT_REQUESTS=5

# === Configuración de Afiliados ===
AFFILIATE_COMMISSION_DEFAULT_RATE=0.05
AFFILIATE_MINIMUM_PAYOUT=25.00
AFFILIATE_PAYMENT_SCHEDULE=monthly
```

### 2. Ejecutar Migraciones

```bash
# Navegar al directorio del backend
cd /workspace/synthia-style-complete/backend

# Ejecutar script de migración
python scripts/migrate_shopping_features.py
```

### 3. Instalar Dependencias

```bash
# Instalar dependencias adicionales
pip install -r requirements.txt

# Generar cliente de Prisma
npx prisma generate
```

## 📚 API Reference

### Endpoints de Shopping

#### 🔍 Búsqueda de Productos
```http
POST /api/v1/shopping/search
```

**Request:**
```json
{
  "query": "camiseta básica",
  "category": "TOPS",
  "min_price": 10.0,
  "max_price": 50.0,
  "brand": ["Nike", "Adidas"],
  "colors": ["negro", "blanco"],
  "sizes": ["M", "L"],
  "on_sale": true,
  "sort_by": "price_asc",
  "limit": 20,
  "offset": 0
}
```

**Response:**
```json
{
  "products": [
    {
      "id": "product_123",
      "merchant": "amazon",
      "name": "Camiseta Básica Premium",
      "price": 29.99,
      "sale_price": 24.99,
      "currency": "USD",
      "brand": "Nike",
      "category": "TOPS",
      "colors": ["negro", "blanco"],
      "sizes": ["S", "M", "L", "XL"],
      "images": ["https://..."],
      "rating": 4.5,
      "review_count": 127,
      "in_stock": true
    }
  ],
  "total_count": 45,
  "search_time": 0.85,
  "result_quality_score": 87.5
}
```

#### 🎯 Generar Recomendaciones
```http
POST /api/v1/shopping/recommendations
```

**Request:**
```json
{
  "recommendation_types": ["BASIC_ITEM", "SEASONAL_REFRESH"],
  "max_recommendations": 10,
  "budget_range": {"min": 20, "max": 100},
  "specific_categories": ["TOPS", "BOTTOMS"],
  "include_trends": true,
  "exclude_owned_similar": true
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "id": "rec_123",
      "item_type": "TOPS",
      "recommended_name": "Camiseta versátil",
      "description": "Camiseta que combina con múltiples outfits...",
      "recommendation_type": "BASIC_ITEM",
      "reason": "Tu armario necesita más básicos versátiles...",
      "priority": 8.5,
      "confidence": 9.2,
      "product": { /* producto recomendado */ },
      "estimated_uses": 30,
      "roi_score": 85.0
    }
  ],
  "total_found": 8,
  "personalization_score": 92.3,
  "generation_metadata": { /* metadatos */ }
}
```

#### ❤️ Gestión de Wishlist
```http
# Obtener wishlist
GET /api/v1/shopping/wishlist

# Agregar producto
POST /api/v1/shopping/wishlist
{
  "product_id": "product_123",
  "price_threshold": 25.0,
  "notify_price_drop": true,
  "priority": 8
}

# Actualizar item
PUT /api/v1/shopping/wishlist/{item_id}
{
  "price_threshold": 20.0,
  "notes": "Para evento especial"
}
```

### Endpoints de Afiliados

#### 💰 Ganancias y Comisiones
```http
# Obtener ganancias
GET /api/v1/affiliates/earnings?limit=20&status=CONFIRMED

# Resumen de ganancias
GET /api/v1/affiliates/earnings/summary?days=30

# Tasas de comisión por merchant
GET /api/v1/affiliates/commission-rates
```

#### 📊 Tracking y Analytics
```http
# Registrar click en link de afiliado
POST /api/v1/affiliates/track/click
{
  "product_id": "product_123",
  "merchant": "amazon",
  "source": "recommendation"
}

# Registrar conversión
POST /api/v1/affiliates/track/conversion
{
  "tracking_id": "track_123",
  "purchase_amount": 89.99,
  "order_id": "AMZ-12345"
}

# Analytics de performance
GET /api/v1/affiliates/analytics/performance?days=30
```

## 🛠️ Integración con Frontend

### Ejemplo de Implementación React

```typescript
// services/shoppingService.ts
import { apiService } from './apiService';

export class ShoppingService {
  async searchProducts(filters: ProductSearchFilters) {
    return await apiService.post('/shopping/search', filters);
  }

  async generateRecommendations(request: RecommendationRequest) {
    return await apiService.post('/shopping/recommendations', request);
  }

  async addToWishlist(productId: string, preferences: WishlistPreferences) {
    return await apiService.post('/shopping/wishlist', {
      product_id: productId,
      ...preferences
    });
  }

  async getAffiliateLink(productId: string, source: string = 'app') {
    const response = await fetch(
      `/api/v1/shopping/affiliate-link/${productId}?source=${source}`,
      { method: 'GET', credentials: 'include' }
    );
    return response.url; // URL del redirect
  }
}

// Componente de búsqueda
const ProductSearch: React.FC = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (query: string) => {
    setLoading(true);
    try {
      const result = await shoppingService.searchProducts({
        query,
        limit: 20,
        sort_by: 'relevance'
      });
      setProducts(result.products);
    } catch (error) {
      console.error('Error searching products:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <SearchInput onSearch={handleSearch} />
      {loading ? <LoadingSpinner /> : <ProductGrid products={products} />}
    </div>
  );
};
```

### Context para Shopping

```typescript
// contexts/ShoppingContext.tsx
const ShoppingContext = createContext<ShoppingContextType | undefined>(undefined);

export const ShoppingProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [wishlist, setWishlist] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [earnings, setEarnings] = useState(null);

  const addToWishlist = async (product: Product) => {
    const result = await shoppingService.addToWishlist(product.id, {
      price_threshold: product.price * 0.9, // 10% descuento
      notify_price_drop: true,
      priority: 5
    });
    setWishlist(prev => [...prev, result]);
  };

  const generateRecommendations = async () => {
    const result = await shoppingService.generateRecommendations({
      max_recommendations: 10,
      include_trends: true
    });
    setRecommendations(result.recommendations);
  };

  return (
    <ShoppingContext.Provider value={{
      wishlist,
      recommendations,
      earnings,
      addToWishlist,
      generateRecommendations
    }}>
      {children}
    </ShoppingContext.Provider>
  );
};
```

## 🔧 Personalización y Configuración

### Configurar Nuevos Merchants

1. **Agregar configuración en `merchant_integration_service.py`:**

```python
self.merchant_configs[Merchant.NEW_MERCHANT] = {
    "base_url": "https://api.newmerchant.com",
    "search_endpoint": "/v1/products/search",
    "affiliate_tag": settings.NEW_MERCHANT_AFFILIATE_TAG,
    "api_key": settings.NEW_MERCHANT_API_KEY,
    "commission_rate": 0.07,  # 7%
    "currency": "USD",
    "enabled": bool(settings.NEW_MERCHANT_API_KEY)
}
```

2. **Implementar método de búsqueda específico:**

```python
async def _new_merchant_api_search(self, filters: ProductSearchFilters, config: Dict[str, Any]) -> List[ProductResponse]:
    # Implementar lógica específica del merchant
    pass
```

### Personalizar Motor de Recomendaciones

```python
# En shopping_recommendation_service.py
async def _generate_custom_recommendations(
    self,
    user_data: Dict[str, Any],
    custom_criteria: Dict[str, Any]
) -> List[ShoppingRecommendationCreate]:
    # Lógica personalizada de recomendaciones
    pass
```

## 📊 Monitoreo y Analytics

### Métricas Disponibles

1. **Performance de Búsqueda:**
   - Tiempo de respuesta por merchant
   - Tasa de éxito de requests
   - Calidad de resultados

2. **Efectividad de Recomendaciones:**
   - Click-through rate
   - Conversion rate
   - Satisfacción del usuario

3. **Ganancias de Afiliados:**
   - Ingresos por merchant
   - Productos más efectivos
   - Tendencias temporales

### Dashboard de Analytics

```python
# Ejemplo de consulta de métricas
async def get_shopping_metrics(user_id: str, days: int = 30):
    return {
        "search_performance": await get_search_metrics(user_id, days),
        "recommendation_effectiveness": await get_recommendation_metrics(user_id, days),
        "affiliate_earnings": await get_earnings_metrics(user_id, days),
        "user_behavior": await get_behavior_metrics(user_id, days)
    }
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de Rate Limiting:**
   ```
   Solución: Ajustar MERCHANT_RATE_LIMIT_* en configuración
   ```

2. **Productos no encontrados:**
   ```
   Verificar: Configuración de API keys de merchants
   ```

3. **Recomendaciones de baja calidad:**
   ```
   Verificar: Datos de armario del usuario y análisis IA
   ```

### Logs y Debugging

```python
import logging
logger = logging.getLogger(__name__)

# Habilitar debug logging
logger.setLevel(logging.DEBUG)
```

## 🚀 Roadmap y Mejoras Futuras

### Próximas Funcionalidades

1. **AI Visual Search**: Búsqueda por imagen
2. **Price Prediction**: Predicción de precios futuros
3. **Social Shopping**: Recomendaciones basadas en amigos
4. **Sustainability Score**: Puntuación de sostenibilidad
5. **Virtual Try-On**: Probador virtual con AR

### Optimizaciones Planificadas

1. **Performance**: Cache distribuido con Redis Cluster
2. **Escalabilidad**: Microservicios independientes por merchant
3. **ML/AI**: Modelos propios de recomendación
4. **Real-time**: WebSockets para updates en tiempo real

## 📞 Soporte

Para soporte técnico o preguntas sobre la implementación:
- Crear issue en el repositorio
- Consultar documentación de APIs de merchants
- Revisar logs de aplicación

---

*Documentación actualizada para Synthia Style v1.0 - Sistema de Shopping y Afiliados*
