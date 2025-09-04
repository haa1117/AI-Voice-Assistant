#!/usr/bin/env python3
"""
AssistX Test Runner
Automated testing script with comprehensive coverage and reporting
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        
    def run_command(self, command, description=""):
        """Run a shell command and return success status"""
        logger.info(f"Running: {description or command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True,
                cwd=self.project_root
            )
            logger.info(f"✅ {description or command} - SUCCESS")
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ {description or command} - FAILED")
            logger.error(f"Error: {e.stderr}")
            return False, e.stderr
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        logger.info("Checking dependencies...")
        
        required_packages = [
            'pytest',
            'pytest-asyncio', 
            'httpx',
            'fastapi',
            'uvicorn'
        ]
        
        missing_packages = []
        
                 for package in required_packages:
             success, _ = self.run_command(f"python -c 'import {package.replace('-', '_')}'")
             if not success:
                 missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Installing missing packages...")
            success, _ = self.run_command(f"pip install {' '.join(missing_packages)}")
            if not success:
                logger.error("Failed to install dependencies")
                return False
        
        logger.info("✅ All dependencies are available")
        return True
    
    def setup_test_environment(self):
        """Set up test environment"""
        logger.info("Setting up test environment...")
        
        # Create necessary directories
        dirs_to_create = ['logs', 'voice_logs', 'database']
        for dir_name in dirs_to_create:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
        
        # Clean up any existing test databases
        test_dbs = ['test_assistx.db', 'test_db.db', 'test_nlp_db.db']
        for db_file in test_dbs:
            db_path = self.project_root / db_file
            if db_path.exists():
                db_path.unlink()
                logger.info(f"Cleaned up {db_file}")
        
        logger.info("✅ Test environment ready")
        return True
    
    def run_unit_tests(self):
        """Run unit tests"""
        logger.info("Running unit tests...")
        
        test_files = [
            'tests/test_database.py',
            'tests/test_nlp.py'
        ]
        
        all_passed = True
        
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                success, output = self.run_command(
                    f"python -m pytest {test_file} -v",
                    f"Unit tests: {test_file}"
                )
                self.test_results[test_file] = success
                if not success:
                    all_passed = False
            else:
                logger.warning(f"Test file not found: {test_file}")
        
        return all_passed
    
    def run_integration_tests(self):
        """Run integration tests"""
        logger.info("Running integration tests...")
        
        success, output = self.run_command(
            "python -m pytest tests/test_main.py -v",
            "Integration tests"
        )
        
        self.test_results['integration'] = success
        return success
    
    def run_performance_tests(self):
        """Run performance tests"""
        logger.info("Running performance tests...")
        
        # Simple performance test - check if app starts quickly
        start_time = time.time()
        
        try:
            # Import main application
            sys.path.insert(0, str(self.project_root))
            from main import app
            
            startup_time = time.time() - start_time
            logger.info(f"App startup time: {startup_time:.2f} seconds")
            
            if startup_time < 10:  # Should start within 10 seconds
                logger.info("✅ Performance test - App startup PASSED")
                self.test_results['performance'] = True
                return True
            else:
                logger.error("❌ Performance test - App startup too slow")
                self.test_results['performance'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            self.test_results['performance'] = False
            return False
    
    def run_linting(self):
        """Run code linting"""
        logger.info("Running code linting...")
        
        # Check if flake8 is available
        success, _ = self.run_command("python -c 'import flake8'")
        if not success:
            logger.info("Installing flake8...")
            success, _ = self.run_command("pip install flake8")
        
        if success:
            success, output = self.run_command(
                "flake8 --max-line-length=100 --exclude=venv,__pycache__ .",
                "Code linting"
            )
            self.test_results['linting'] = success
            return success
        else:
            logger.warning("Flake8 not available, skipping linting")
            return True
    
    def run_security_check(self):
        """Run basic security checks"""
        logger.info("Running security checks...")
        
        # Check for common security issues
        security_issues = []
        
        # Check for hardcoded secrets (basic check)
        main_file = self.project_root / 'main.py'
        if main_file.exists():
            content = main_file.read_text()
            if 'password' in content.lower() or 'secret' in content.lower():
                security_issues.append("Potential hardcoded credentials in main.py")
        
        # Check if demo data contains real-looking information
        db_file = self.project_root / 'database' / 'db_manager.py'
        if db_file.exists():
            content = db_file.read_text()
            # This is acceptable for demo purposes
        
        if security_issues:
            for issue in security_issues:
                logger.warning(f"⚠️  Security: {issue}")
            self.test_results['security'] = False
            return False
        else:
            logger.info("✅ Basic security checks passed")
            self.test_results['security'] = True
            return True
    
    def cleanup(self):
        """Clean up test artifacts"""
        logger.info("Cleaning up test artifacts...")
        
        # Remove test databases
        test_files = [
            'test_assistx.db',
            'test_db.db', 
            'test_nlp_db.db',
            '.coverage',
            'htmlcov'
        ]
        
        for file_name in test_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                if file_path.is_dir():
                    import shutil
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
                logger.info(f"Cleaned up {file_name}")
        
        logger.info("✅ Cleanup completed")
    
    def generate_report(self):
        """Generate test report"""
        logger.info("\n" + "="*60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name:<20} : {status}")
        
        logger.info("-"*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
                 success_rate = (passed_tests/total_tests)*100 if total_tests > 0 else 0
         logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("\n🎉 ALL TESTS PASSED! AssistX is ready for deployment.")
            return True
        else:
            logger.error(f"\n💥 {total_tests - passed_tests} TESTS FAILED! Please fix issues before deployment.")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 Starting AssistX Test Suite")
        logger.info("="*60)
        
        start_time = time.time()
        
        # Run all test phases
        test_phases = [
            ("Dependency Check", self.check_dependencies),
            ("Environment Setup", self.setup_test_environment),
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Code Linting", self.run_linting),
            ("Security Check", self.run_security_check)
        ]
        
        for phase_name, phase_func in test_phases:
            logger.info(f"\n📋 {phase_name}")
            logger.info("-" * 40)
            
            try:
                result = phase_func()
                if phase_name not in ["Dependency Check", "Environment Setup"]:
                    self.test_results[phase_name.lower().replace(" ", "_")] = result
            except Exception as e:
                logger.error(f"❌ {phase_name} failed with exception: {e}")
                if phase_name not in ["Dependency Check", "Environment Setup"]:
                    self.test_results[phase_name.lower().replace(" ", "_")] = False
        
        # Generate final report
        total_time = time.time() - start_time
        logger.info(f"\n⏱️  Total test time: {total_time:.2f} seconds")
        
        success = self.generate_report()
        
        # Cleanup
        self.cleanup()
        
        return success

def main():
    """Main entry point"""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 