#!/usr/bin/env python3
"""
=============================================================================
SYNTHIA STYLE - DOCKER SETUP VALIDATION SCRIPT
=============================================================================
Script comprehensivo para validar que toda la configuración Docker está
funcionando correctamente antes del deployment.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
from urllib.parse import urlparse

class Colors:
    """ANSI color codes for console output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DockerSetupValidator:
    """Comprehensive Docker setup validation"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).absolute()
        self.test_results = []
        self.errors = []
        self.warnings = []
        
    def print_status(self, message: str, status: str = "INFO"):
        """Print colored status message"""
        color = {
            "INFO": Colors.OKBLUE,
            "SUCCESS": Colors.OKGREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
            "HEADER": Colors.HEADER
        }.get(status, Colors.OKBLUE)
        
        icon = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "HEADER": "🔍"
        }.get(status, "ℹ️")
        
        print(f"{color}{icon} {message}{Colors.ENDC}")
        
    def run_command(self, command: str, check: bool = True) -> Tuple[bool, str, str]:
        """Run shell command and return success status and output"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def test_docker_availability(self) -> bool:
        """Test if Docker and Docker Compose are available"""
        self.print_status("Testing Docker availability...", "HEADER")
        
        # Test Docker
        success, stdout, stderr = self.run_command("docker --version")
        if not success:
            self.print_status("Docker is not installed or not running", "ERROR")
            self.errors.append("Docker not available")
            return False
        
        self.print_status(f"Docker found: {stdout.strip()}", "SUCCESS")
        
        # Test Docker Compose
        success, stdout, stderr = self.run_command("docker compose version")
        if not success:
            # Try old docker-compose
            success, stdout, stderr = self.run_command("docker-compose --version")
            if not success:
                self.print_status("Docker Compose is not installed", "ERROR")
                self.errors.append("Docker Compose not available")
                return False
        
        self.print_status(f"Docker Compose found: {stdout.strip()}", "SUCCESS")
        return True
    
    def test_file_structure(self) -> bool:
        """Test that all required files are present"""
        self.print_status("Testing file structure...", "HEADER")
        
        required_files = [
            # Docker files
            "docker-compose.yml",
            "docker-compose.dev.yml", 
            "docker-compose.prod.yml",
            ".env.example",
            "Makefile",
            
            # Docker configurations
            "docker/backend/Dockerfile.prod",
            "docker/backend/Dockerfile.dev",
            "docker/frontend/Dockerfile.prod",
            "docker/frontend/Dockerfile.dev",
            "docker/nginx/Dockerfile",
            "docker/nginx/nginx.conf",
            "docker/nginx/conf.d/synthia.conf",
            
            # Scripts
            "scripts/setup-dev.sh",
            "scripts/deploy-prod.sh",
            "scripts/health-check.sh",
            "scripts/init-db.sql",
            
            # Configuration
            "config/redis.conf",
            "config/redis-prod.conf",
            
            # Monitoring
            "monitoring/prometheus.yml",
            "monitoring/grafana/datasources/prometheus.yml",
            "monitoring/grafana/dashboards/synthia-overview.json",
            "monitoring/grafana/grafana.ini",
            
            # Documentation
            "README.md",
            "QUICK_START.md",
            "DOCKER_IMPLEMENTATION_SUMMARY.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.print_status(f"Missing files: {', '.join(missing_files)}", "ERROR")
            self.errors.extend(missing_files)
            return False
        
        self.print_status("All required files present", "SUCCESS")
        return True
    
    def test_dockerfile_syntax(self) -> bool:
        """Test Dockerfile syntax"""
        self.print_status("Testing Dockerfile syntax...", "HEADER")
        
        dockerfiles = [
            "docker/backend/Dockerfile.prod",
            "docker/backend/Dockerfile.dev", 
            "docker/frontend/Dockerfile.prod",
            "docker/frontend/Dockerfile.dev",
            "docker/nginx/Dockerfile"
        ]
        
        success = True
        for dockerfile in dockerfiles:
            # Basic syntax check (look for FROM instruction)
            try:
                with open(self.project_root / dockerfile, 'r') as f:
                    content = f.read()
                    if not content.strip().startswith('#') and 'FROM' not in content:
                        self.print_status(f"Invalid Dockerfile: {dockerfile}", "ERROR")
                        success = False
                    else:
                        self.print_status(f"Dockerfile syntax OK: {dockerfile}", "SUCCESS")
            except Exception as e:
                self.print_status(f"Error reading {dockerfile}: {e}", "ERROR")
                success = False
        
        return success
    
    def test_docker_compose_syntax(self) -> bool:
        """Test Docker Compose file syntax"""
        self.print_status("Testing Docker Compose syntax...", "HEADER")
        
        compose_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml"
        ]
        
        success = True
        for compose_file in compose_files:
            cmd = f"docker compose -f {compose_file} config"
            cmd_success, stdout, stderr = self.run_command(cmd)
            
            if not cmd_success:
                self.print_status(f"Invalid compose file: {compose_file}", "ERROR")
                self.print_status(f"Error: {stderr}", "ERROR")
                success = False
            else:
                self.print_status(f"Compose syntax OK: {compose_file}", "SUCCESS")
        
        return success
    
    def test_environment_configuration(self) -> bool:
        """Test environment configuration"""
        self.print_status("Testing environment configuration...", "HEADER")
        
        env_example = self.project_root / ".env.example"
        if not env_example.exists():
            self.print_status(".env.example not found", "ERROR")
            return False
        
        # Check for required variables
        required_vars = [
            "GEMINI_API_KEY",
            "POSTGRES_PASSWORD", 
            "REDIS_PASSWORD",
            "JWT_SECRET_KEY",
            "DOMAIN"
        ]
        
        try:
            with open(env_example, 'r') as f:
                content = f.read()
                
            missing_vars = []
            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)
            
            if missing_vars:
                self.print_status(f"Missing env vars: {', '.join(missing_vars)}", "ERROR")
                return False
            
            self.print_status("Environment configuration OK", "SUCCESS")
            return True
            
        except Exception as e:
            self.print_status(f"Error reading .env.example: {e}", "ERROR")
            return False
    
    def test_script_permissions(self) -> bool:
        """Test that scripts have execute permissions"""
        self.print_status("Testing script permissions...", "HEADER")
        
        scripts = [
            "scripts/setup-dev.sh",
            "scripts/deploy-prod.sh", 
            "scripts/health-check.sh",
            "docker/nginx/scripts/generate-ssl.sh"
        ]
        
        success = True
        for script in scripts:
            script_path = self.project_root / script
            if script_path.exists():
                # Check if executable
                if not os.access(script_path, os.X_OK):
                    self.print_status(f"Script not executable: {script}", "WARNING")
                    # Try to make executable
                    try:
                        os.chmod(script_path, 0o755)
                        self.print_status(f"Made executable: {script}", "SUCCESS")
                    except:
                        self.warnings.append(f"Cannot make executable: {script}")
                else:
                    self.print_status(f"Script executable: {script}", "SUCCESS")
            else:
                self.print_status(f"Script not found: {script}", "ERROR")
                success = False
        
        return success
    
    def test_makefile_targets(self) -> bool:
        """Test Makefile targets"""
        self.print_status("Testing Makefile...", "HEADER")
        
        makefile = self.project_root / "Makefile"
        if not makefile.exists():
            self.print_status("Makefile not found", "ERROR")
            return False
        
        # Test make help
        success, stdout, stderr = self.run_command("make help")
        if not success:
            self.print_status("Makefile syntax error", "ERROR")
            self.print_status(f"Error: {stderr}", "ERROR")
            return False
        
        self.print_status("Makefile syntax OK", "SUCCESS")
        return True
    
    def test_build_development(self) -> bool:
        """Test development build"""
        self.print_status("Testing development build...", "HEADER")
        
        # Clean up first
        self.run_command("docker compose -f docker-compose.dev.yml down -v")
        
        # Build development images
        success, stdout, stderr = self.run_command(
            "docker compose -f docker-compose.dev.yml build --no-cache"
        )
        
        if not success:
            self.print_status("Development build failed", "ERROR")
            self.print_status(f"Error: {stderr}", "ERROR")
            return False
        
        self.print_status("Development build successful", "SUCCESS")
        return True
    
    def test_build_production(self) -> bool:
        """Test production build"""
        self.print_status("Testing production build...", "HEADER")
        
        # Build production images
        success, stdout, stderr = self.run_command(
            "docker compose -f docker-compose.prod.yml build --no-cache"
        )
        
        if not success:
            self.print_status("Production build failed", "ERROR")
            self.print_status(f"Error: {stderr}", "ERROR")
            return False
        
        self.print_status("Production build successful", "SUCCESS")
        return True
    
    def test_quick_startup(self) -> bool:
        """Test quick startup of development environment"""
        self.print_status("Testing quick startup...", "HEADER")
        
        # Start services
        success, stdout, stderr = self.run_command(
            "docker compose -f docker-compose.dev.yml up -d"
        )
        
        if not success:
            self.print_status("Failed to start services", "ERROR")
            self.print_status(f"Error: {stderr}", "ERROR")
            return False
        
        # Wait a bit for services to start
        time.sleep(10)
        
        # Check if services are running
        success, stdout, stderr = self.run_command(
            "docker compose -f docker-compose.dev.yml ps"
        )
        
        # Stop services
        self.run_command("docker compose -f docker-compose.dev.yml down")
        
        if not success:
            self.print_status("Failed to check service status", "ERROR")
            return False
        
        self.print_status("Quick startup test successful", "SUCCESS")
        return True
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result[1])
        failed_tests = total_tests - passed_tests
        
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "test_results": self.test_results,
            "errors": self.errors,
            "warnings": self.warnings,
            "overall_status": "PASS" if failed_tests == 0 else "FAIL"
        }
    
    def run_all_tests(self) -> bool:
        """Run all validation tests"""
        self.print_status("🐳 SYNTHIA STYLE - DOCKER SETUP VALIDATION", "HEADER")
        self.print_status("=" * 60, "HEADER")
        
        tests = [
            ("Docker Availability", self.test_docker_availability),
            ("File Structure", self.test_file_structure),
            ("Dockerfile Syntax", self.test_dockerfile_syntax),
            ("Docker Compose Syntax", self.test_docker_compose_syntax),
            ("Environment Configuration", self.test_environment_configuration),
            ("Script Permissions", self.test_script_permissions),
            ("Makefile", self.test_makefile_targets),
            ("Development Build", self.test_build_development),
            ("Production Build", self.test_build_production),
            ("Quick Startup", self.test_quick_startup),
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.test_results.append((test_name, result))
                if not result:
                    all_passed = False
            except Exception as e:
                self.print_status(f"Test '{test_name}' failed with exception: {e}", "ERROR")
                self.test_results.append((test_name, False))
                self.errors.append(f"{test_name}: {e}")
                all_passed = False
        
        # Generate report
        report = self.generate_report()
        
        # Print summary
        self.print_status("=" * 60, "HEADER")
        self.print_status("🏁 VALIDATION SUMMARY", "HEADER")
        self.print_status("=" * 60, "HEADER")
        
        self.print_status(f"Total Tests: {report['total_tests']}", "INFO")
        self.print_status(f"Passed: {report['passed_tests']}", "SUCCESS")
        self.print_status(f"Failed: {report['failed_tests']}", "ERROR" if report['failed_tests'] > 0 else "INFO")
        self.print_status(f"Success Rate: {report['success_rate']:.1f}%", "SUCCESS" if report['success_rate'] == 100 else "WARNING")
        
        if report['warnings']:
            self.print_status(f"Warnings: {len(report['warnings'])}", "WARNING")
            for warning in report['warnings']:
                self.print_status(f"  - {warning}", "WARNING")
        
        if report['errors']:
            self.print_status("Errors found:", "ERROR")
            for error in report['errors']:
                self.print_status(f"  - {error}", "ERROR")
        
        # Save report
        report_file = self.project_root / "docker_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.print_status(f"Report saved to: {report_file}", "INFO")
        
        if all_passed:
            self.print_status("🎉 ALL TESTS PASSED! Docker setup is ready for deployment.", "SUCCESS")
        else:
            self.print_status("❌ Some tests failed. Please fix the issues before deployment.", "ERROR")
        
        return all_passed

def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    validator = DockerSetupValidator(project_root)
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
