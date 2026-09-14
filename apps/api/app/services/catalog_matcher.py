"""
Motor de Armonización de Catálogo B2B (Synthia Catalog Matcher)
Armoniza visagismo y colorimetría del comprador con el inventario del comercio.
"""

from typing import List, Dict, Any, Optional
from app.schemas.widget import (
    ColorimetryProfile,
    VisagismProfile,
    CatalogItem,
    WidgetRecommendResponse
)

# Catálogo B2B de Demostración (Óptica y Moda)
DEFAULT_DEMO_CATALOG: List[Dict[str, Any]] = [
    {
        "sku": "OPT-CAREY-01",
        "title": "Gafas de Sol Carey Polarizadas 'Capri'",
        "category": "eyewear",
        "price": 289.00,
        "currency": "PEN",
        "image_url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&q=80",
        "undertone": "warm",
        "frame_shape": "RECTANGULAR",
        "color_family": "tortoise_amber",
        "tryon_overlay_url": "/assets/frames/opt-carey-01.svg",
        "palette_affinity": ["AUTUMN", "SPRING"],
        "face_shape_affinity": ["ROUND", "OVAL", "HEART"]
    },
    {
        "sku": "OPT-TITAN-02",
        "title": "Montura de Titanio Plateado 'Nordic Minimal'",
        "category": "eyewear",
        "price": 349.00,
        "currency": "PEN",
        "image_url": "https://images.unsplash.com/photo-1574258495973-f010dfbb5371?w=500&q=80",
        "undertone": "cool",
        "frame_shape": "ROUND",
        "color_family": "silver_metallic",
        "tryon_overlay_url": "/assets/frames/opt-titan-02.svg",
        "palette_affinity": ["WINTER", "SUMMER"],
        "face_shape_affinity": ["SQUARE", "OVAL", "DIAMOND"]
    },
    {
        "sku": "OPT-AVIAT-03",
        "title": "Aviador Dorado con Lentes Ámbar 'Solstice'",
        "category": "eyewear",
        "price": 310.00,
        "currency": "PEN",
        "image_url": "https://images.unsplash.com/photo-1508296695146-257a814070b4?w=500&q=80",
        "undertone": "warm",
        "frame_shape": "AVIATOR",
        "color_family": "gold_amber",
        "tryon_overlay_url": "/assets/frames/opt-aviat-03.svg",
        "palette_affinity": ["AUTUMN", "SPRING"],
        "face_shape_affinity": ["SQUARE", "HEART", "OVAL"]
    },
    {
        "sku": "OPT-BLACK-04",
        "title": "Montura Acetato Negro Piano 'Brooklyn'",
        "category": "eyewear",
        "price": 269.00,
        "currency": "PEN",
        "image_url": "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=500&q=80",
        "undertone": "cool",
        "frame_shape": "SQUARE",
        "color_family": "black",
        "tryon_overlay_url": "/assets/frames/opt-black-04.svg",
        "palette_affinity": ["WINTER"],
        "face_shape_affinity": ["ROUND", "OVAL"]
    },
    {
        "sku": "OPT-CAT-05",
        "title": "Gafas Ojo de Gato Borgoña 'Milano'",
        "category": "eyewear",
        "price": 299.00,
        "currency": "PEN",
        "image_url": "https://images.unsplash.com/photo-1577803645773-f96470509666?w=500&q=80",
        "undertone": "cool",
        "frame_shape": "CAT_EYE",
        "color_family": "burgundy",
        "tryon_overlay_url": "/assets/frames/opt-cat-05.svg",
        "palette_affinity": ["WINTER", "AUTUMN"],
        "face_shape_affinity": ["ROUND", "DIAMOND", "OVAL", "SQUARE"]
    }
]


class CatalogMatcher:
    """Motor de matching de catálogo B2B"""

    def __init__(self, catalog: Optional[List[Dict[str, Any]]] = None):
        self.catalog = catalog or DEFAULT_DEMO_CATALOG

    def calculate_match_score(
        self,
        item: Dict[str, Any],
        colorimetry: ColorimetryProfile,
        visagism: VisagismProfile
    ) -> int:
        score = 50  # Base

        # Afinidad de colorimetría (hasta +25 pts)
        if item.get("undertone") == colorimetry.undertone:
            score += 15
        elif colorimetry.undertone == "neutral":
            score += 10

        if colorimetry.season in item.get("palette_affinity", []):
            score += 10

        # Afinidad de visagismo / forma de rostro (hasta +25 pts)
        if visagism.face_shape in item.get("face_shape_affinity", []):
            score += 20
        elif "OVAL" in item.get("face_shape_affinity", []):
            score += 10

        return min(98, max(45, score))

    def get_recommendations(
        self,
        merchant_id: str,
        current_sku: Optional[str],
        colorimetry: ColorimetryProfile,
        visagism: VisagismProfile,
        limit: int = 4
    ) -> List[CatalogItem]:
        results: List[CatalogItem] = []

        for item in self.catalog:
            # Si es el SKU actual, podemos incluirlo o priorizarlo según contexto
            score = self.calculate_match_score(item, colorimetry, visagism)

            badge = "Armonía Estilística"
            if score >= 90:
                badge = "Match Perfecto ⭐"
            elif score >= 80:
                badge = "Muy Favorecedor"
            elif score >= 70:
                badge = "Buen Contraste"

            results.append(
                CatalogItem(
                    sku=item["sku"],
                    title=item["title"],
                    category=item["category"],
                    price=item["price"],
                    currency=item.get("currency", "PEN"),
                    image_url=item["image_url"],
                    color_family=item.get("color_family"),
                    frame_shape=item.get("frame_shape"),
                    harmony_score=score,
                    match_tag=badge,
                    tryon_overlay_url=item.get("tryon_overlay_url")
                )
            )

        # Ordenar por puntuación descendente
        results.sort(key=lambda x: x.harmony_score, reverse=True)
        return results[:limit]

    def build_stylist_advice(
        self,
        colorimetry: ColorimetryProfile,
        visagism: VisagismProfile,
        current_product_score: Optional[int] = None
    ) -> str:
        shape_tips = {
            "ROUND": "Al tener rostro redondo, los marcos angulares o rectangulares aportan estructura y definen los pómulos.",
            "SQUARE": "Tus facciones angulares y mandíbula marcada se equilibran elegantemente con monturas redondeadas u ovaladas.",
            "OVAL": "Tu proporción facial es armónica y versátil, permitiéndote lucir monturas tanto geométricas como orgánicas.",
            "HEART": "Para un rostro con frente despejada y mentón afinado, las monturas tipo aviador o de base ancha equilibran las proporciones.",
            "DIAMOND": "Los marcos tipo Cat-Eye o líneas suaves en el entrecejo realzan tus pómulos pronunciados.",
            "OBLONG": "Monturas con profundidad vertical o acetato contrastante acortan sutilmente el eje facial."
        }

        tone_tips = {
            "warm": f"Tu subtono cálido ({colorimetry.season}) brilla con acabados en carey ámbar, dorados, miel y verdes oliva.",
            "cool": f"Tu subtono frío ({colorimetry.season}) armoniza con acetato negro profundo, plata, gunmetal y tonos joya.",
            "neutral": f"Tu subtono neutro ({colorimetry.season}) tiene flexibilidad para alternar metales fríos y cálidos."
        }

        advice_shape = shape_tips.get(visagism.face_shape, "Tus proporciones faciales tienen balance natural.")
        advice_tone = tone_tips.get(colorimetry.undertone, "Tus tonos naturales ofrecen balance cromático.")

        return f"{advice_shape} {advice_tone}"


catalog_matcher = CatalogMatcher()
