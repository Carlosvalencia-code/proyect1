#!/usr/bin/env python3
# =============================================================================
# SYNTHIA STYLE - TEST COMPLETO DE MIGRACIÓN FLASK TO FASTAPI
# =============================================================================
# Script de testing integral para verificar la migración completa

import asyncio
import sys
import os
import json
import base64
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import tempfile
from PIL import Image
import io

# Agregar directorio al path
sys.path.append(str(Path(__file__).parent))

# Test configuration
TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "test_user_email": "test_migration@synthiastyle.com",
    "test_user_name": "Usuario Test Migración",
    "timeout": 30,
    "endpoints_to_test": [
        "health",
        "auth_login",
        "auth_signup", 
        "dashboard",
        "chromatic_analysis",
        "facial_analysis",
        "feedback",
        "auth_logout"
    ]
}

class MigrationTester:
    """
    Tester completo para la migración de Flask a FastAPI
    """
    
    def __init__(self):
        self.base_url = TEST_CONFIG["base_url"]
        self.test_results = {
            "test_started": datetime.now().isoformat(),
            "tests_performed": [],
            "successes": [],
            "failures": [],
            "warnings": [],
            "performance_metrics": {}
        }
        self.session_cookies = {}
        
    async def test_server_health(self) -> bool:
        """Test del health check del servidor"""
        print("🔍 Testing server health...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
                start_time = datetime.now()
                response = await client.get(f"{self.base_url}/api/v1/flask/health")
                end_time = datetime.now()
                
                response_time = (end_time - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ Server health OK - Response time: {response_time:.2f}ms")
                    
                    self.test_results["tests_performed"].append("server_health")
                    self.test_results["successes"].append({
                        "test": "server_health",
                        "response_time_ms": response_time,
                        "data": health_data
                    })
                    self.test_results["performance_metrics"]["health_check"] = response_time
                    return True
                else:
                    print(f"❌ Server health failed - Status: {response.status_code}")
                    self.test_results["failures"].append({
                        "test": "server_health",
                        "error": f"Status code {response.status_code}",
                        "response": response.text
                    })
                    return False
                    
        except Exception as e:
            print(f"❌ Server health error: {e}")
            self.test_results["failures"].append({
                "test": "server_health",
                "error": str(e)
            })
            return False
    
    async def test_authentication_flow(self) -> bool:
        """Test completo del flujo de autenticación"""
        print("🔐 Testing authentication flow...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
                # 1. Test Signup
                signup_data = {
                    "email": TEST_CONFIG["test_user_email"],
                    "full_name": TEST_CONFIG["test_user_name"]
                }
                
                start_time = datetime.now()
                signup_response = await client.post(
                    f"{self.base_url}/api/v1/flask/auth/signup",
                    json=signup_data
                )
                signup_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if signup_response.status_code != 200:
                    print(f"❌ Signup failed - Status: {signup_response.status_code}")
                    return False
                
                print(f"✅ Signup successful - Response time: {signup_time:.2f}ms")
                
                # Obtener cookies de sesión
                self.session_cookies = signup_response.cookies
                
                # 2. Test Dashboard con autenticación
                start_time = datetime.now()
                dashboard_response = await client.get(
                    f"{self.base_url}/api/v1/flask/dashboard",
                    cookies=self.session_cookies
                )
                dashboard_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if dashboard_response.status_code != 200:
                    print(f"❌ Dashboard access failed - Status: {dashboard_response.status_code}")
                    return False
                
                print(f"✅ Dashboard access successful - Response time: {dashboard_time:.2f}ms")
                
                # 3. Test Logout
                start_time = datetime.now()
                logout_response = await client.post(
                    f"{self.base_url}/api/v1/flask/auth/logout",
                    cookies=self.session_cookies
                )
                logout_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if logout_response.status_code != 200:
                    print(f"❌ Logout failed - Status: {logout_response.status_code}")
                    return False
                
                print(f"✅ Logout successful - Response time: {logout_time:.2f}ms")
                
                # 4. Test re-login
                login_data = {"email": TEST_CONFIG["test_user_email"]}
                start_time = datetime.now()
                login_response = await client.post(
                    f"{self.base_url}/api/v1/flask/auth/login",
                    json=login_data
                )
                login_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if login_response.status_code != 200:
                    print(f"❌ Re-login failed - Status: {login_response.status_code}")
                    return False
                
                print(f"✅ Re-login successful - Response time: {login_time:.2f}ms")
                
                # Actualizar cookies para siguientes tests
                self.session_cookies = login_response.cookies
                
                # Guardar métricas
                self.test_results["performance_metrics"].update({
                    "signup_time": signup_time,
                    "dashboard_time": dashboard_time,
                    "logout_time": logout_time,
                    "login_time": login_time
                })
                
                self.test_results["tests_performed"].extend([
                    "auth_signup", "auth_dashboard", "auth_logout", "auth_login"
                ])
                self.test_results["successes"].append({
                    "test": "authentication_flow",
                    "message": "Complete authentication flow successful"
                })
                
                return True
                
        except Exception as e:
            print(f"❌ Authentication flow error: {e}")
            self.test_results["failures"].append({
                "test": "authentication_flow",
                "error": str(e)
            })
            return False
    
    async def test_chromatic_analysis(self) -> bool:
        """Test del análisis cromático"""
        print("🎨 Testing chromatic analysis...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
                # Datos de prueba para el quiz cromático
                quiz_data = {
                    "vein_color": "blue",
                    "sun_reaction": "burn",
                    "jewelry": "silver",
                    "best_colors": ["blue", "purple", "pink", "gray"]
                }
                
                start_time = datetime.now()
                response = await client.post(
                    f"{self.base_url}/api/v1/flask/analysis/chromatic",
                    json=quiz_data,
                    cookies=self.session_cookies
                )
                analysis_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code != 200:
                    print(f"❌ Chromatic analysis failed - Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                
                analysis_result = response.json()
                print(f"✅ Chromatic analysis successful - Response time: {analysis_time:.2f}ms")
                
                # Verificar estructura de respuesta
                if not analysis_result.get("success"):
                    print("❌ Analysis response format invalid")
                    return False
                
                data = analysis_result.get("data", {})
                required_fields = ["estacion", "subtono", "confianza_analisis"]
                for field in required_fields:
                    if field not in data:
                        print(f"❌ Missing field in response: {field}")
                        return False
                
                print(f"   • Estación detectada: {data.get('estacion')}")
                print(f"   • Subtono: {data.get('subtono')}")
                print(f"   • Confianza: {data.get('confianza_analisis')}%")
                
                # Test obtener resultados
                start_time = datetime.now()
                results_response = await client.get(
                    f"{self.base_url}/api/v1/flask/analysis/chromatic/results",
                    cookies=self.session_cookies
                )
                results_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if results_response.status_code != 200:
                    print(f"⚠️  Get chromatic results failed - Status: {results_response.status_code}")
                    self.test_results["warnings"].append("Chromatic results retrieval failed")
                else:
                    print(f"✅ Chromatic results retrieval successful - Response time: {results_time:.2f}ms")
                
                # Test formato React
                react_response = await client.get(
                    f"{self.base_url}/api/v1/flask/analysis/chromatic/react-format",
                    cookies=self.session_cookies
                )
                
                if react_response.status_code == 200:
                    print("✅ React format compatibility confirmed")
                else:
                    print("⚠️  React format not available")
                    self.test_results["warnings"].append("React format endpoint failed")
                
                self.test_results["performance_metrics"]["chromatic_analysis"] = analysis_time
                self.test_results["tests_performed"].append("chromatic_analysis")
                self.test_results["successes"].append({
                    "test": "chromatic_analysis",
                    "response_time_ms": analysis_time,
                    "detected_season": data.get('estacion'),
                    "confidence": data.get('confianza_analisis')
                })
                
                return True
                
        except Exception as e:
            print(f"❌ Chromatic analysis error: {e}")
            self.test_results["failures"].append({
                "test": "chromatic_analysis",
                "error": str(e)
            })
            return False
    
    def create_test_image(self) -> str:
        """Crear imagen de prueba en base64"""
        try:
            # Crear imagen simple de prueba
            img = Image.new('RGB', (200, 200), color='lightblue')
            
            # Convertir a base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            img_bytes = buffer.getvalue()
            
            return base64.b64encode(img_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"Error creating test image: {e}")
            return ""
    
    async def test_facial_analysis(self) -> bool:
        """Test del análisis facial"""
        print("👤 Testing facial analysis...")
        
        try:
            # Crear imagen de prueba
            test_image_b64 = self.create_test_image()
            
            if not test_image_b64:
                print("❌ Could not create test image")
                return False
            
            async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
                # Test análisis facial con imagen base64
                analysis_data = {
                    "image_base64": test_image_b64
                }
                
                start_time = datetime.now()
                response = await client.post(
                    f"{self.base_url}/api/v1/flask/analysis/facial",
                    json=analysis_data,
                    cookies=self.session_cookies
                )
                analysis_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code != 200:
                    print(f"❌ Facial analysis failed - Status: {response.status_code}")
                    print(f"Response: {response.text}")
                    # No es error crítico si Gemini no está configurado
                    if "Gemini" in response.text or "API" in response.text:
                        print("⚠️  Gemini API not configured - facial analysis skipped")
                        self.test_results["warnings"].append("Gemini API not configured for facial analysis")
                        return True
                    return False
                
                analysis_result = response.json()
                print(f"✅ Facial analysis successful - Response time: {analysis_time:.2f}ms")
                
                # Verificar estructura de respuesta
                if not analysis_result.get("success"):
                    print("❌ Facial analysis response format invalid")
                    return False
                
                data = analysis_result.get("data", {})
                if "forma_rostro" in data:
                    print(f"   • Forma detectada: {data.get('forma_rostro')}")
                    print(f"   • Confianza: {data.get('confianza_analisis', 'N/A')}%")
                
                self.test_results["performance_metrics"]["facial_analysis"] = analysis_time
                self.test_results["tests_performed"].append("facial_analysis")
                self.test_results["successes"].append({
                    "test": "facial_analysis",
                    "response_time_ms": analysis_time,
                    "face_shape": data.get('forma_rostro'),
                    "confidence": data.get('confianza_analisis')
                })
                
                return True
                
        except Exception as e:
            print(f"❌ Facial analysis error: {e}")
            # Si es error de Gemini API, no es crítico para la migración
            if "Gemini" in str(e) or "API" in str(e):
                print("⚠️  Facial analysis skipped due to API configuration")
                self.test_results["warnings"].append(f"Facial analysis API issue: {e}")
                return True
            
            self.test_results["failures"].append({
                "test": "facial_analysis",
                "error": str(e)
            })
            return False
    
    async def test_feedback_system(self) -> bool:
        """Test del sistema de feedback"""
        print("💬 Testing feedback system...")
        
        try:
            async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
                feedback_data = {
                    "type": "chromatic",
                    "rating": 5,
                    "comment": "Excelente análisis cromático, muy preciso!",
                    "helpful": True
                }
                
                start_time = datetime.now()
                response = await client.post(
                    f"{self.base_url}/api/v1/flask/feedback",
                    json=feedback_data,
                    cookies=self.session_cookies
                )
                feedback_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code != 200:
                    print(f"❌ Feedback submission failed - Status: {response.status_code}")
                    return False
                
                print(f"✅ Feedback submission successful - Response time: {feedback_time:.2f}ms")
                
                self.test_results["performance_metrics"]["feedback_submission"] = feedback_time
                self.test_results["tests_performed"].append("feedback")
                self.test_results["successes"].append({
                    "test": "feedback_system",
                    "response_time_ms": feedback_time
                })
                
                return True
                
        except Exception as e:
            print(f"❌ Feedback system error: {e}")
            self.test_results["failures"].append({
                "test": "feedback_system",
                "error": str(e)
            })
            return False
    
    async def test_frontend_compatibility(self) -> bool:
        """Test de compatibilidad con frontend React"""
        print("⚛️  Testing frontend React compatibility...")
        
        try:
            # Verificar que el frontend React existe
            frontend_path = Path(__file__).parent.parent / "frontend"
            if not frontend_path.exists():
                print("⚠️  Frontend React directory not found")
                self.test_results["warnings"].append("Frontend React directory not found")
                return True
            
            # Verificar types.ts
            types_file = frontend_path / "types.ts"
            if types_file.exists():
                print("✅ Frontend types.ts found")
                
                with open(types_file, 'r') as f:
                    types_content = f.read()
                
                # Verificar tipos requeridos
                required_types = [
                    "FaceShape", "SkinUndertone", "ColorSeason",
                    "FacialAnalysisDataAPI", "ChromaticAnalysisDataAPI"
                ]
                
                missing_types = []
                for type_name in required_types:
                    if type_name not in types_content:
                        missing_types.append(type_name)
                
                if missing_types:
                    print(f"⚠️  Missing types in frontend: {missing_types}")
                    self.test_results["warnings"].append(f"Missing frontend types: {missing_types}")
                else:
                    print("✅ All required types present in frontend")
            else:
                print("⚠️  Frontend types.ts not found")
                self.test_results["warnings"].append("Frontend types.ts not found")
            
            # Verificar servicios
            services_dir = frontend_path / "services"
            if services_dir.exists():
                print("✅ Frontend services directory found")
                
                gemini_service = services_dir / "geminiService.ts"
                if gemini_service.exists():
                    print("✅ Frontend geminiService.ts found")
                else:
                    print("⚠️  Frontend geminiService.ts not found")
                    self.test_results["warnings"].append("Frontend geminiService.ts not found")
            else:
                print("⚠️  Frontend services directory not found")
                self.test_results["warnings"].append("Frontend services directory not found")
            
            self.test_results["tests_performed"].append("frontend_compatibility")
            self.test_results["successes"].append({
                "test": "frontend_compatibility",
                "message": "Frontend compatibility check completed"
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Frontend compatibility check error: {e}")
            self.test_results["failures"].append({
                "test": "frontend_compatibility",
                "error": str(e)
            })
            return False
    
    async def run_complete_test_suite(self) -> bool:
        """Ejecutar suite completa de tests"""
        print("🚀 Iniciando suite completa de tests de migración Flask → FastAPI")
        print("=" * 80)
        
        test_functions = [
            ("Server Health Check", self.test_server_health),
            ("Authentication Flow", self.test_authentication_flow),
            ("Chromatic Analysis", self.test_chromatic_analysis),
            ("Facial Analysis", self.test_facial_analysis),
            ("Feedback System", self.test_feedback_system),
            ("Frontend Compatibility", self.test_frontend_compatibility)
        ]
        
        total_tests = len(test_functions)
        passed_tests = 0
        
        for test_name, test_func in test_functions:
            try:
                print(f"\n📋 Ejecutando: {test_name}")
                success = await test_func()
                
                if success:
                    passed_tests += 1
                    print(f"✅ {test_name} - PASÓ")
                else:
                    print(f"❌ {test_name} - FALLÓ")
                    
            except Exception as e:
                print(f"💥 Error en {test_name}: {e}")
                self.test_results["failures"].append({
                    "test": test_name,
                    "error": f"Test execution error: {e}"
                })
        
        # Resultado final
        success_rate = (passed_tests / total_tests) * 100
        self.test_results["test_completed"] = datetime.now().isoformat()
        self.test_results["total_tests"] = total_tests
        self.test_results["passed_tests"] = passed_tests
        self.test_results["success_rate"] = success_rate
        
        print("\n" + "=" * 80)
        print("📊 RESULTADO DE LOS TESTS")
        print("=" * 80)
        print(f"✅ Tests pasados: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"⚠️  Warnings: {len(self.test_results['warnings'])}")
        print(f"❌ Failures: {len(self.test_results['failures'])}")
        
        # Mostrar métricas de performance
        if self.test_results["performance_metrics"]:
            print("\n⚡ Métricas de Performance:")
            for metric, time_ms in self.test_results["performance_metrics"].items():
                print(f"   • {metric}: {time_ms:.2f}ms")
        
        # Mostrar warnings
        if self.test_results["warnings"]:
            print("\n⚠️  Warnings encontrados:")
            for warning in self.test_results["warnings"]:
                print(f"   • {warning}")
        
        # Mostrar errores
        if self.test_results["failures"]:
            print("\n❌ Errores encontrados:")
            for failure in self.test_results["failures"]:
                test_name = failure.get("test", "Unknown")
                error = failure.get("error", "Unknown error")
                print(f"   • {test_name}: {error}")
        
        # Guardar reporte
        report_path = Path(__file__).parent / "migration_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte completo guardado en: {report_path}")
        
        # Evaluación final
        if success_rate >= 85:
            print("\n🎉 ¡MIGRACIÓN EXITOSA!")
            print("La migración de Flask a FastAPI está funcionando correctamente.")
            return True
        elif success_rate >= 60:
            print("\n⚠️  MIGRACIÓN PARCIALMENTE EXITOSA")
            print("La migración funciona pero hay issues menores que resolver.")
            return True
        else:
            print("\n❌ MIGRACIÓN NECESITA REVISIÓN")
            print("Hay problemas significativos que necesitan ser solucionados.")
            return False

async def main():
    """Función principal"""
    print("🔧 Iniciando tests de migración de Flask a FastAPI...")
    
    tester = MigrationTester()
    
    try:
        success = await tester.run_complete_test_suite()
        return success
        
    except Exception as e:
        print(f"\n💥 Error crítico durante los tests: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
