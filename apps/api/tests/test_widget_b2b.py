"""
Suite de Pruebas Automatizadas para el Endpoint B2B Widget (Synthia Commerce AI)
"""

import sys
import os

# Asegurar que apps/api esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_widget_health():
    """Verifica que el endpoint de salud del widget responda 200 y status active"""
    response = client.get("/api/v1/widget/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["service"] == "synthia-b2b-widget"


def test_widget_catalog():
    """Verifica la obtención del catálogo sincronizado del comercio"""
    response = client.get("/api/v1/widget/catalog", headers={"X-Merchant-Key": "test-merchant-01"})
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_key"] == "test-merchant-01"
    assert data["total_items"] > 0
    assert len(data["items"]) >= 4
    first_item = data["items"][0]
    assert "sku" in first_item
    assert "price" in first_item


def test_widget_recommend_round_face_warm():
    """Verifica la recomendación para rostro redondo y subtono cálido (Carey / Otoño)"""
    payload = {
        "sku": "OPT-CAREY-01",
        "category": "eyewear",
        "quiz_data": {
            "face_shape": "ROUND",
            "undertone": "warm",
            "season": "AUTUMN"
        }
    }
    response = client.post(
        "/api/v1/widget/recommend",
        json=payload,
        headers={"X-Merchant-Key": "optica-monaco-b2b"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Validaciones de visagismo y colorimetría B2B
    assert data["merchant_id"] == "optica-monaco-b2b"
    assert data["visagism"]["face_shape"] == "ROUND"
    assert "RECTANGULAR" in data["visagism"]["recommended_frame_shapes"]
    assert data["colorimetry"]["undertone"] == "warm"
    assert data["current_product_score"] >= 80
    assert data["fit_verdict"] in ["PERFECT_MATCH", "GOOD_MATCH"]
    assert len(data["recommended_catalog"]) > 0
    assert len(data["colorimetry"]["best_colors"]) > 0


def test_widget_recommend_square_face_cool():
    """Verifica la recomendación para rostro cuadrado y subtono frío (Titanio Plateado / Invierno)"""
    payload = {
        "sku": "OPT-TITAN-02",
        "category": "eyewear",
        "quiz_data": {
            "face_shape": "SQUARE",
            "undertone": "cool",
            "season": "WINTER"
        }
    }
    response = client.post(
        "/api/v1/widget/recommend",
        json=payload,
        headers={"X-Merchant-Key": "optica-nordic"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["visagism"]["face_shape"] == "SQUARE"
    assert data["colorimetry"]["undertone"] == "cool"
    assert len(data["recommended_catalog"]) > 0
    assert data["processing_time_ms"] >= 0
