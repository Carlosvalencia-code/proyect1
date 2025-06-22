#!/usr/bin/env python3
# =============================================================================
# SYNTHIA STYLE - VALIDADOR DE ESTRUCTURA DE MIGRACIÓN
# =============================================================================
# Script que valida que la estructura de migración está correcta

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

class MigrationStructureValidator:
    """
    Validador de la estructura de archivos para la migración Flask → FastAPI
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.validation_results = {
            "validation_started": str(Path.cwd()),
            "structure_checks": [],
            "file_checks": [],
            "content_checks": [],
            "missing_files": [],
            "issues": [],
            "recommendations": []
        }
    
    def check_required_directories(self) -> bool:
        """Verificar que existen los directorios requeridos"""
        print("📁 Verificando estructura de directorios...")
        
        required_dirs = [
            "app",
            "app/api",
            "app/api/v1",
            "app/api/v1/endpoints",
            "app/core",
            "app/db",
            "app/schemas",
            "app/services",
            "app/models",
            "app/utils",
            "prisma",
            "scripts",
            "docs",
            "tests"
        ]
        
        missing_dirs = []
        existing_dirs = []
        
        for directory in required_dirs:
            dir_path = self.project_root / directory
            if dir_path.exists() and dir_path.is_dir():
                existing_dirs.append(directory)
                print(f"   ✅ {directory}/")
            else:
                missing_dirs.append(directory)
                print(f"   ❌ {directory}/ - FALTANTE")
        
        self.validation_results["structure_checks"].append({
            "check": "required_directories",
            "total": len(required_dirs),
            "existing": len(existing_dirs),
            "missing": missing_dirs
        })
        
        if missing_dirs:
            self.validation_results["issues"].append(f"Directorios faltantes: {missing_dirs}")
        
        return len(missing_dirs) == 0
    
    def check_required_files(self) -> bool:
        """Verificar que existen los archivos requeridos"""
        print("\n📄 Verificando archivos requeridos...")
        
        required_files = [
            "app/main.py",
            "app/__init__.py",
            "app/api/__init__.py",
            "app/api/v1/__init__.py",
            "app/api/v1/api.py",
            "app/api/v1/endpoints/__init__.py",
            "app/api/v1/endpoints/flask_migration.py",
            "app/core/config.py",
            "app/core/security.py",
            "app/core/logging.py",
            "app/db/database.py",
            "app/schemas/__init__.py",
            "app/schemas/flask_migration.py",
            "app/services/__init__.py",
            "app/services/flask_migration_service.py",
            "app/services/gemini_service.py",
            "app/services/cache_service.py",
            "prisma/schema.prisma",
            "requirements.txt",
            ".env.development"
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists() and full_path.is_file():
                existing_files.append(file_path)
                print(f"   ✅ {file_path}")
            else:
                missing_files.append(file_path)
                print(f"   ❌ {file_path} - FALTANTE")
        
        self.validation_results["file_checks"].append({
            "check": "required_files", 
            "total": len(required_files),
            "existing": len(existing_files),
            "missing": missing_files
        })
        
        if missing_files:
            self.validation_results["missing_files"].extend(missing_files)
            self.validation_results["issues"].append(f"Archivos faltantes: {missing_files}")
        
        return len(missing_files) == 0
    
    def check_flask_migration_endpoints(self) -> bool:
        """Verificar que los endpoints de migración Flask están implementados"""
        print("\n🔗 Verificando endpoints de migración Flask...")
        
        endpoints_file = self.project_root / "app/api/v1/endpoints/flask_migration.py"
        
        if not endpoints_file.exists():
            print("   ❌ Archivo flask_migration.py no encontrado")
            return False
        
        try:
            with open(endpoints_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_endpoints = [
                "/auth/login",
                "/auth/signup", 
                "/auth/logout",
                "/dashboard",
                "/analysis/facial",
                "/analysis/chromatic",
                "/feedback",
                "/health"
            ]
            
            missing_endpoints = []
            existing_endpoints = []
            
            for endpoint in required_endpoints:
                if endpoint in content:
                    existing_endpoints.append(endpoint)
                    print(f"   ✅ {endpoint}")
                else:
                    missing_endpoints.append(endpoint)
                    print(f"   ❌ {endpoint} - FALTANTE")
            
            self.validation_results["content_checks"].append({
                "check": "flask_migration_endpoints",
                "file": "flask_migration.py",
                "total": len(required_endpoints),
                "existing": len(existing_endpoints),
                "missing": missing_endpoints
            })
            
            if missing_endpoints:
                self.validation_results["issues"].append(f"Endpoints de migración faltantes: {missing_endpoints}")
            
            return len(missing_endpoints) == 0
            
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
            self.validation_results["issues"].append(f"Error leyendo flask_migration.py: {e}")
            return False
    
    def check_schemas_compatibility(self) -> bool:
        """Verificar que los schemas son compatibles con el frontend React"""
        print("\n📋 Verificando compatibilidad de schemas...")
        
        schemas_file = self.project_root / "app/schemas/flask_migration.py"
        
        if not schemas_file.exists():
            print("   ❌ Archivo flask_migration.py schemas no encontrado")
            return False
        
        try:
            with open(schemas_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_schemas = [
                "FaceShape",
                "ColorSeason", 
                "SkinUndertone",
                "FacialAnalysisRequest",
                "FacialAnalysisResponse",
                "ChromaticAnalysisResponse",
                "UserLogin",
                "UserSignup",
                "FeedbackSubmission"
            ]
            
            missing_schemas = []
            existing_schemas = []
            
            for schema in required_schemas:
                if f"class {schema}" in content or f"{schema} =" in content:
                    existing_schemas.append(schema)
                    print(f"   ✅ {schema}")
                else:
                    missing_schemas.append(schema)
                    print(f"   ❌ {schema} - FALTANTE")
            
            self.validation_results["content_checks"].append({
                "check": "migration_schemas",
                "file": "flask_migration.py",
                "total": len(required_schemas),
                "existing": len(existing_schemas),
                "missing": missing_schemas
            })
            
            if missing_schemas:
                self.validation_results["issues"].append(f"Schemas de migración faltantes: {missing_schemas}")
            
            return len(missing_schemas) == 0
            
        except Exception as e:
            print(f"   ❌ Error leyendo schemas: {e}")
            self.validation_results["issues"].append(f"Error leyendo schemas: {e}")
            return False
    
    def check_service_implementation(self) -> bool:
        """Verificar que los servicios de migración están implementados"""
        print("\n⚙️  Verificando implementación de servicios...")
        
        service_file = self.project_root / "app/services/flask_migration_service.py"
        
        if not service_file.exists():
            print("   ❌ Archivo flask_migration_service.py no encontrado")
            return False
        
        try:
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_methods = [
                "analyze_face_with_gemini",
                "analyze_chromatic_quiz",
                "create_user_session",
                "save_analysis_result",
                "save_user_feedback"
            ]
            
            missing_methods = []
            existing_methods = []
            
            for method in required_methods:
                if f"def {method}" in content or f"async def {method}" in content:
                    existing_methods.append(method)
                    print(f"   ✅ {method}")
                else:
                    missing_methods.append(method)
                    print(f"   ❌ {method} - FALTANTE")
            
            self.validation_results["content_checks"].append({
                "check": "service_methods",
                "file": "flask_migration_service.py",
                "total": len(required_methods),
                "existing": len(existing_methods),
                "missing": missing_methods
            })
            
            if missing_methods:
                self.validation_results["issues"].append(f"Métodos de servicio faltantes: {missing_methods}")
            
            return len(missing_methods) == 0
            
        except Exception as e:
            print(f"   ❌ Error leyendo servicio: {e}")
            self.validation_results["issues"].append(f"Error leyendo servicio: {e}")
            return False
    
    def check_prisma_configuration(self) -> bool:
        """Verificar configuración de Prisma para PostgreSQL"""
        print("\n🗄️  Verificando configuración de Prisma...")
        
        schema_file = self.project_root / "prisma/schema.prisma"
        
        if not schema_file.exists():
            print("   ❌ Schema de Prisma no encontrado")
            return False
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checks = [
                ('provider = "postgresql"', "Proveedor PostgreSQL"),
                ('generator client', "Generador de cliente"),
                ('prisma-client-py', "Cliente Python"),
                ('model User', "Modelo User"),
                ('model FacialAnalysis', "Modelo FacialAnalysis"),
                ('model ChromaticAnalysis', "Modelo ChromaticAnalysis")
            ]
            
            passed_checks = []
            failed_checks = []
            
            for check, description in checks:
                if check in content:
                    passed_checks.append(description)
                    print(f"   ✅ {description}")
                else:
                    failed_checks.append(description)
                    print(f"   ❌ {description} - FALTANTE")
            
            self.validation_results["content_checks"].append({
                "check": "prisma_configuration",
                "file": "schema.prisma",
                "total": len(checks),
                "existing": len(passed_checks),
                "missing": failed_checks
            })
            
            if failed_checks:
                self.validation_results["issues"].append(f"Configuración Prisma faltante: {failed_checks}")
            
            return len(failed_checks) == 0
            
        except Exception as e:
            print(f"   ❌ Error leyendo schema de Prisma: {e}")
            self.validation_results["issues"].append(f"Error leyendo Prisma schema: {e}")
            return False
    
    def check_configuration_files(self) -> bool:
        """Verificar archivos de configuración"""
        print("\n⚙️  Verificando archivos de configuración...")
        
        config_files = [
            (".env.development", "Configuración de desarrollo"),
            ("requirements.txt", "Dependencias Python"),
            ("app/core/config.py", "Configuración principal"),
            ("app/core/security.py", "Configuración de seguridad")
        ]
        
        missing_configs = []
        existing_configs = []
        
        for file_path, description in config_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                existing_configs.append(description)
                print(f"   ✅ {description}")
                
                # Verificaciones específicas
                if file_path == ".env.development":
                    self._check_env_file(full_path)
                elif file_path == "requirements.txt":
                    self._check_requirements_file(full_path)
                    
            else:
                missing_configs.append(description)
                print(f"   ❌ {description} - FALTANTE")
        
        if missing_configs:
            self.validation_results["issues"].append(f"Archivos de configuración faltantes: {missing_configs}")
        
        return len(missing_configs) == 0
    
    def _check_env_file(self, env_path: Path) -> None:
        """Verificar contenido del archivo .env"""
        try:
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            required_vars = [
                "DATABASE_URL",
                "SECRET_KEY", 
                "GEMINI_API_KEY",
                "HOST",
                "PORT"
            ]
            
            for var in required_vars:
                if f"{var}=" in env_content:
                    if f"{var}=your_" not in env_content:
                        print(f"      ✅ {var} configurada")
                    else:
                        print(f"      ⚠️  {var} necesita configuración")
                        self.validation_results["recommendations"].append(f"Configurar {var} en .env")
                else:
                    print(f"      ❌ {var} faltante")
                    self.validation_results["issues"].append(f"Variable {var} faltante en .env")
                    
        except Exception as e:
            print(f"      ❌ Error leyendo .env: {e}")
    
    def _check_requirements_file(self, req_path: Path) -> None:
        """Verificar dependencias en requirements.txt"""
        try:
            with open(req_path, 'r') as f:
                req_content = f.read()
            
            required_deps = [
                "fastapi",
                "uvicorn",
                "pydantic",
                "pydantic-settings",
                "asyncpg",
                "prisma",
                "google-generativeai",
                "redis"
            ]
            
            missing_deps = []
            for dep in required_deps:
                if dep in req_content:
                    print(f"      ✅ {dep}")
                else:
                    missing_deps.append(dep)
                    print(f"      ❌ {dep} faltante")
            
            if missing_deps:
                self.validation_results["issues"].append(f"Dependencias faltantes: {missing_deps}")
                
        except Exception as e:
            print(f"      ❌ Error leyendo requirements: {e}")
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generar reporte de validación"""
        print("\n📊 Generando reporte de validación...")
        
        total_issues = len(self.validation_results["issues"])
        total_recommendations = len(self.validation_results["recommendations"])
        
        # Calcular score de completitud
        total_checks = (
            sum(check.get("total", 0) for check in self.validation_results["structure_checks"]) +
            sum(check.get("total", 0) for check in self.validation_results["file_checks"]) +
            sum(check.get("total", 0) for check in self.validation_results["content_checks"])
        )
        
        completed_checks = (
            sum(check.get("existing", 0) for check in self.validation_results["structure_checks"]) +
            sum(check.get("existing", 0) for check in self.validation_results["file_checks"]) +
            sum(check.get("existing", 0) for check in self.validation_results["content_checks"])
        )
        
        completion_rate = (completed_checks / total_checks * 100) if total_checks > 0 else 0
        
        report = {
            **self.validation_results,
            "summary": {
                "total_checks": total_checks,
                "completed_checks": completed_checks, 
                "completion_rate": round(completion_rate, 1),
                "total_issues": total_issues,
                "total_recommendations": total_recommendations
            }
        }
        
        # Guardar reporte
        report_path = self.project_root / "migration_structure_validation.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Reporte guardado en: {report_path}")
        
        return report
    
    def run_complete_validation(self) -> bool:
        """Ejecutar validación completa"""
        print("🔍 VALIDACIÓN DE ESTRUCTURA DE MIGRACIÓN FLASK → FASTAPI")
        print("=" * 70)
        
        validation_steps = [
            ("Directorios requeridos", self.check_required_directories),
            ("Archivos requeridos", self.check_required_files),
            ("Endpoints de migración", self.check_flask_migration_endpoints),
            ("Schemas de compatibilidad", self.check_schemas_compatibility),
            ("Implementación de servicios", self.check_service_implementation),
            ("Configuración de Prisma", self.check_prisma_configuration),
            ("Archivos de configuración", self.check_configuration_files)
        ]
        
        passed_validations = 0
        total_validations = len(validation_steps)
        
        for step_name, step_func in validation_steps:
            try:
                success = step_func()
                if success:
                    passed_validations += 1
                    
            except Exception as e:
                print(f"💥 Error en {step_name}: {e}")
                self.validation_results["issues"].append(f"Error en {step_name}: {e}")
        
        # Generar reporte final
        report = self.generate_validation_report()
        
        # Resultado final
        success_rate = (passed_validations / total_validations) * 100
        completion_rate = report["summary"]["completion_rate"]
        
        print("\n" + "=" * 70)
        print("📊 RESULTADO DE LA VALIDACIÓN")
        print("=" * 70)
        print(f"✅ Validaciones pasadas: {passed_validations}/{total_validations} ({success_rate:.1f}%)")
        print(f"📈 Completitud de estructura: {completion_rate:.1f}%")
        print(f"⚠️  Issues encontrados: {len(self.validation_results['issues'])}")
        print(f"💡 Recomendaciones: {len(self.validation_results['recommendations'])}")
        
        if self.validation_results["issues"]:
            print("\n❌ Issues encontrados:")
            for issue in self.validation_results["issues"][:5]:  # Mostrar solo los primeros 5
                print(f"   • {issue}")
            if len(self.validation_results["issues"]) > 5:
                print(f"   ... y {len(self.validation_results['issues']) - 5} más")
        
        if self.validation_results["recommendations"]:
            print("\n💡 Recomendaciones:")
            for rec in self.validation_results["recommendations"][:3]:  # Mostrar solo las primeras 3
                print(f"   • {rec}")
            if len(self.validation_results["recommendations"]) > 3:
                print(f"   ... y {len(self.validation_results['recommendations']) - 3} más")
        
        # Evaluación final
        if completion_rate >= 90 and success_rate >= 85:
            print("\n🎉 ¡ESTRUCTURA DE MIGRACIÓN COMPLETA!")
            print("La migración está lista para ser ejecutada.")
            return True
        elif completion_rate >= 70 and success_rate >= 70:
            print("\n⚠️  ESTRUCTURA MAYORMENTE COMPLETA")
            print("La migración está casi lista, resolver issues menores.")
            return True
        else:
            print("\n❌ ESTRUCTURA INCOMPLETA")
            print("Necesita más trabajo antes de ejecutar la migración.")
            return False

def main():
    """Función principal"""
    validator = MigrationStructureValidator()
    
    try:
        success = validator.run_complete_validation()
        return success
        
    except Exception as e:
        print(f"\n💥 Error crítico durante la validación: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
