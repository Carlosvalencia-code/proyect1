"""
Setup script para Synthia Style Backend
Facilita la instalación y configuración inicial
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Ejecutar comando y manejar errores"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e.stderr}")
        return None


def check_dependencies():
    """Verificar dependencias del sistema"""
    print("🔍 Verificando dependencias del sistema...")
    
    # Verificar Python
    if sys.version_info < (3, 11):
        print("❌ Se requiere Python 3.11 o superior")
        sys.exit(1)
    else:
        print(f"✅ Python {sys.version}")
    
    # Verificar pip
    if shutil.which("pip") is None:
        print("❌ pip no encontrado")
        sys.exit(1)
    else:
        print("✅ pip disponible")
    
    # Verificar PostgreSQL (opcional)
    if shutil.which("psql"):
        print("✅ PostgreSQL disponible")
    else:
        print("⚠️  PostgreSQL no encontrado (puedes usar Docker)")
    
    # Verificar Docker (opcional)
    if shutil.which("docker"):
        print("✅ Docker disponible")
    else:
        print("⚠️  Docker no encontrado (instalación manual requerida)")


def create_directories():
    """Crear directorios necesarios"""
    print("📁 Creando directorios...")
    
    directories = [
        "uploads/facial",
        "uploads/temp", 
        "uploads/thumbnails",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Creado: {directory}")


def setup_environment():
    """Configurar archivo de entorno"""
    print("⚙️  Configurando archivo de entorno...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Archivo .env creado desde .env.example")
        print("⚠️  IMPORTANTE: Edita .env con tus configuraciones antes de ejecutar")
    elif env_file.exists():
        print("✅ Archivo .env ya existe")
    else:
        print("❌ No se encontró .env.example")


def install_python_dependencies():
    """Instalar dependencias de Python"""
    print("📦 Instalando dependencias de Python...")
    
    if Path("requirements.txt").exists():
        result = run_command("pip install -r requirements.txt", "Instalación de dependencias")
        if result is None:
            print("❌ Error instalando dependencias")
            return False
    else:
        print("❌ requirements.txt no encontrado")
        return False
    
    return True


def setup_database():
    """Configurar base de datos con Prisma"""
    print("🗄️  Configurando base de datos...")
    
    # Verificar si Prisma está disponible
    if shutil.which("prisma"):
        print("✅ Prisma CLI encontrado")
    else:
        print("📦 Instalando Prisma CLI...")
        if shutil.which("npm"):
            run_command("npm install -g prisma", "Instalación de Prisma CLI")
        else:
            print("⚠️  npm no encontrado. Instala Node.js para usar Prisma CLI")
            print("   Alternativamente, usa Docker Compose para la base de datos")
            return
    
    # Generar cliente Prisma
    if Path("prisma/schema.prisma").exists():
        run_command("prisma generate", "Generación del cliente Prisma")
        
        # Solo ejecutar migraciones si hay conexión a BD
        print("⚠️  Para ejecutar migraciones, asegúrate de:")
        print("   1. Tener PostgreSQL ejecutándose")
        print("   2. Configurar DATABASE_URL en .env")
        print("   3. Ejecutar: prisma migrate deploy")
    else:
        print("❌ Esquema de Prisma no encontrado")


def create_docker_setup():
    """Crear configuración para Docker"""
    print("🐳 Configuración de Docker disponible...")
    
    if Path("docker-compose.yml").exists():
        print("✅ docker-compose.yml encontrado")
        print("   Para ejecutar con Docker:")
        print("   1. docker-compose up -d")
        print("   2. Esperar a que los servicios estén listos")
        print("   3. La aplicación estará en http://localhost:8000")
    else:
        print("❌ docker-compose.yml no encontrado")


def show_next_steps():
    """Mostrar pasos siguientes"""
    print("\n🎉 Setup completado!")
    print("\n📋 Pasos siguientes:")
    print("\n1. Configurar variables de entorno:")
    print("   - Edita .env con tus configuraciones")
    print("   - Especialmente: DATABASE_URL y GEMINI_API_KEY")
    
    print("\n2. Configurar base de datos:")
    print("   OPCIÓN A - PostgreSQL local:")
    print("   - Instalar PostgreSQL")
    print("   - Crear base de datos")
    print("   - Ejecutar: prisma migrate deploy")
    
    print("\n   OPCIÓN B - Docker:")
    print("   - Ejecutar: docker-compose up -d")
    
    print("\n3. Ejecutar aplicación:")
    print("   - Desarrollo: python run.py")
    print("   - Producción: ver README.md")
    
    print("\n4. Acceder a la aplicación:")
    print("   - API: http://localhost:8000")
    print("   - Docs: http://localhost:8000/docs")
    print("   - Health: http://localhost:8000/health")
    
    print("\n📚 Para más información, ver README.md")


def main():
    """Función principal del setup"""
    print("🚀 Synthia Style Backend - Setup")
    print("=" * 40)
    
    # Verificar que estamos en el directorio correcto
    if not Path("app/main.py").exists():
        print("❌ Ejecuta este script desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Ejecutar pasos del setup
    check_dependencies()
    create_directories()
    setup_environment()
    
    if install_python_dependencies():
        setup_database()
    
    create_docker_setup()
    show_next_steps()


if __name__ == "__main__":
    main()
