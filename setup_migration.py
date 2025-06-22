#!/usr/bin/env python3
# =============================================================================
# SYNTHIA STYLE - SETUP DE MIGRACIÓN FLASK TO FASTAPI
# =============================================================================
# Script de configuración inicial para la migración completa

import os
import sys
import subprocess
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import shutil

class MigrationSetup:
    """
    Configurador automático para la migración de Flask a FastAPI
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.setup_log = []
        
    def log_step(self, message: str, success: bool = True):
        """Log de pasos de configuración"""
        symbol = "✅" if success else "❌"
        print(f"{symbol} {message}")
        self.setup_log.append({
            "message": message,
            "success": success,
            "timestamp": str(Path.cwd())
        })
    
    def check_system_requirements(self) -> bool:
        """Verificar requisitos del sistema"""
        print("🔍 Verificando requisitos del sistema...")
        
        requirements_ok = True
        
        # Verificar Python
        try:
            python_version = sys.version_info
            if python_version.major >= 3 and python_version.minor >= 8:
                self.log_step(f"Python {python_version.major}.{python_version.minor} OK")
            else:
                self.log_step(f"Python {python_version.major}.{python_version.minor} - Se requiere Python 3.8+", False)
                requirements_ok = False
        except Exception as e:
            self.log_step(f"Error verificando Python: {e}", False)
            requirements_ok = False
        
        # Verificar pip
        try:
            result = subprocess.run(["pip", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log_step("pip disponible")
            else:
                self.log_step("pip no encontrado", False)
                requirements_ok = False
        except Exception as e:
            self.log_step(f"Error verificando pip: {e}", False)
            requirements_ok = False
        
        return requirements_ok
    
    def install_dependencies(self) -> bool:
        """Instalar dependencias de Python"""
        print("📦 Instalando dependencias...")
        
        try:
            requirements_file = self.project_root / "requirements.txt"
            
            if not requirements_file.exists():
                self.log_step("requirements.txt no encontrado", False)
                return False
            
            # Instalar dependencias
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_step("Dependencias instaladas correctamente")
                return True
            else:
                self.log_step(f"Error instalando dependencias: {result.stderr}", False)
                return False
                
        except Exception as e:
            self.log_step(f"Error en instalación de dependencias: {e}", False)
            return False
    
    def setup_environment_files(self) -> bool:
        """Configurar archivos de entorno"""
        print("⚙️  Configurando archivos de entorno...")
        
        try:
            # Copiar .env.development como .env si no existe
            env_dev_file = self.project_root / ".env.development"
            env_file = self.project_root / ".env"
            
            if env_dev_file.exists() and not env_file.exists():
                shutil.copy2(env_dev_file, env_file)
                self.log_step("Archivo .env creado desde .env.development")
            elif env_file.exists():
                self.log_step("Archivo .env ya existe")
            else:
                self.log_step("No se pudo crear archivo .env", False)
                return False
            
            # Verificar variables críticas
            critical_vars = [
                "DATABASE_URL",
                "SECRET_KEY",
                "GEMINI_API_KEY"
            ]
            
            missing_vars = []
            with open(env_file, 'r') as f:
                env_content = f.read()
                
            for var in critical_vars:
                if f"{var}=" not in env_content or f"{var}=your_" in env_content:
                    missing_vars.append(var)
            
            if missing_vars:
                self.log_step(f"Variables de entorno faltantes: {missing_vars}", False)
                print("⚠️  Por favor configura las siguientes variables en .env:")
                for var in missing_vars:
                    print(f"   • {var}")
                return False
            else:
                self.log_step("Variables de entorno configuradas")
                return True
                
        except Exception as e:
            self.log_step(f"Error configurando archivos de entorno: {e}", False)
            return False
    
    def create_project_directories(self) -> bool:
        """Crear directorios necesarios del proyecto"""
        print("📁 Creando estructura de directorios...")
        
        try:
            directories = [
                "uploads",
                "logs",
                "cache",
                "tmp"
            ]
            
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(exist_ok=True)
                self.log_step(f"Directorio {directory} creado/verificado")
            
            return True
            
        except Exception as e:
            self.log_step(f"Error creando directorios: {e}", False)
            return False
    
    def check_database_connection(self) -> bool:
        """Verificar conexión a PostgreSQL"""
        print("🗄️  Verificando conexión a base de datos...")
        
        try:
            # Importar módulos de la aplicación
            sys.path.append(str(self.project_root))
            
            from app.core.config import get_settings
            
            settings = get_settings()
            
            if not settings.DATABASE_URL or "your_" in settings.DATABASE_URL:
                self.log_step("DATABASE_URL no configurada correctamente", False)
                print("⚠️  Por favor configura DATABASE_URL en .env con una URL válida de PostgreSQL")
                print("   Ejemplo: postgresql://user:password@localhost:5432/database")
                return False
            
            self.log_step("Configuración de base de datos presente")
            
            # TODO: Aquí se podría hacer una conexión real para verificar
            # Por ahora solo verificamos que la configuración esté presente
            
            return True
            
        except Exception as e:
            self.log_step(f"Error verificando base de datos: {e}", False)
            return False
    
    def setup_prisma(self) -> bool:
        """Configurar Prisma ORM"""
        print("🔧 Configurando Prisma ORM...")
        
        try:
            # Verificar que el schema existe
            schema_file = self.project_root / "prisma" / "schema.prisma"
            
            if not schema_file.exists():
                self.log_step("Schema de Prisma no encontrado", False)
                return False
            
            self.log_step("Schema de Prisma encontrado")
            
            # Generar cliente de Prisma
            try:
                result = subprocess.run([
                    "prisma", "generate"
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode == 0:
                    self.log_step("Cliente de Prisma generado")
                else:
                    self.log_step("Error generando cliente de Prisma - continuando", False)
                    print(f"   Error: {result.stderr}")
                    # No es error crítico, se puede generar después
                    
            except FileNotFoundError:
                self.log_step("Prisma CLI no encontrado - se puede instalar después", False)
                print("   Instala Prisma CLI: npm install -g prisma")
            
            return True
            
        except Exception as e:
            self.log_step(f"Error configurando Prisma: {e}", False)
            return False
    
    def validate_fastapi_setup(self) -> bool:
        """Validar que FastAPI está configurado correctamente"""
        print("🚀 Validando configuración de FastAPI...")
        
        try:
            # Importar aplicación principal
            sys.path.append(str(self.project_root))
            
            from app.main import app
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # Verificar que la app se puede importar
            self.log_step("Aplicación FastAPI importada correctamente")
            
            # Verificar rutas de migración
            routes = [route.path for route in app.routes]
            migration_routes = [route for route in routes if "flask" in route]
            
            if migration_routes:
                self.log_step(f"Rutas de migración encontradas: {len(migration_routes)}")
            else:
                self.log_step("No se encontraron rutas de migración", False)
                return False
            
            return True
            
        except Exception as e:
            self.log_step(f"Error validando FastAPI: {e}", False)
            return False
    
    def create_launch_script(self) -> bool:
        """Crear script de lanzamiento"""
        print("📝 Creando script de lanzamiento...")
        
        try:
            launch_script = self.project_root / "start_server.py"
            
            script_content = '''#!/usr/bin/env python3
"""
Script de lanzamiento para Synthia Style FastAPI
"""
import os
import sys
from pathlib import Path

# Agregar directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings
    
    settings = get_settings()
    
    print("🚀 Iniciando Synthia Style FastAPI Server...")
    print(f"   Host: {settings.HOST}")
    print(f"   Port: {settings.PORT}")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
'''
            
            with open(launch_script, 'w') as f:
                f.write(script_content)
            
            # Hacer ejecutable en sistemas Unix
            if os.name != 'nt':
                os.chmod(launch_script, 0o755)
            
            self.log_step("Script de lanzamiento creado")
            return True
            
        except Exception as e:
            self.log_step(f"Error creando script de lanzamiento: {e}", False)
            return False
    
    def generate_setup_report(self) -> None:
        """Generar reporte de configuración"""
        print("📄 Generando reporte de configuración...")
        
        try:
            report = {
                "setup_completed": True,
                "steps_performed": self.setup_log,
                "success_count": len([step for step in self.setup_log if step["success"]]),
                "failure_count": len([step for step in self.setup_log if not step["success"]]),
                "next_steps": [
                    "1. Configurar variables de entorno en .env",
                    "2. Configurar PostgreSQL y ejecutar migraciones",
                    "3. Instalar Prisma CLI si es necesario: npm install -g prisma",
                    "4. Ejecutar: python start_server.py",
                    "5. Ejecutar tests: python test_migration_complete.py"
                ]
            }
            
            report_file = self.project_root / "setup_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.log_step(f"Reporte guardado en {report_file}")
            
        except Exception as e:
            self.log_step(f"Error generando reporte: {e}", False)
    
    def run_complete_setup(self) -> bool:
        """Ejecutar configuración completa"""
        print("🏗️  Iniciando configuración completa de la migración...")
        print("=" * 70)
        
        setup_steps = [
            ("Verificar requisitos del sistema", self.check_system_requirements),
            ("Instalar dependencias", self.install_dependencies),
            ("Configurar archivos de entorno", self.setup_environment_files),
            ("Crear directorios del proyecto", self.create_project_directories),
            ("Verificar conexión a base de datos", self.check_database_connection),
            ("Configurar Prisma ORM", self.setup_prisma),
            ("Validar configuración FastAPI", self.validate_fastapi_setup),
            ("Crear script de lanzamiento", self.create_launch_script)
        ]
        
        total_steps = len(setup_steps)
        completed_steps = 0
        
        for step_name, step_func in setup_steps:
            try:
                print(f"\n📋 {step_name}...")
                success = step_func()
                
                if success:
                    completed_steps += 1
                    
            except Exception as e:
                print(f"💥 Error en {step_name}: {e}")
                self.log_step(f"{step_name}: {e}", False)
        
        # Generar reporte
        self.generate_setup_report()
        
        # Resultado final
        success_rate = (completed_steps / total_steps) * 100
        
        print("\n" + "=" * 70)
        print("📊 RESULTADO DE LA CONFIGURACIÓN")
        print("=" * 70)
        print(f"✅ Pasos completados: {completed_steps}/{total_steps} ({success_rate:.1f}%)")
        
        if success_rate >= 85:
            print("\n🎉 ¡CONFIGURACIÓN EXITOSA!")
            print("\n🚀 Próximos pasos:")
            print("   1. Configurar variables de entorno específicas (especialmente GEMINI_API_KEY)")
            print("   2. Configurar PostgreSQL si no está ya configurado")
            print("   3. Ejecutar servidor: python start_server.py")
            print("   4. Ejecutar tests: python test_migration_complete.py")
            return True
        else:
            print("\n⚠️  CONFIGURACIÓN PARCIAL")
            print("Revisa los errores anteriores y completa la configuración manualmente.")
            return False

def main():
    """Función principal"""
    setup = MigrationSetup()
    
    try:
        success = setup.run_complete_setup()
        return success
        
    except Exception as e:
        print(f"\n💥 Error crítico durante la configuración: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
