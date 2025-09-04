#!/usr/bin/env python3
"""
AssistX Server Startup Script
Automated server startup with environment validation and monitoring
"""

import os
import sys
import subprocess
import time
import logging
import signal
import asyncio
from pathlib import Path
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AssistXServer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.server_process = None
        self.startup_checks_passed = False
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received, stopping server...")
        self.stop_server()
        sys.exit(0)
    
    def check_system_requirements(self):
        """Check system requirements"""
        logger.info("Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            logger.error(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            return False
        
        logger.info(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check available memory
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        if memory_gb < 2:
            logger.warning(f"Low memory detected: {memory_gb:.1f}GB (recommended: 4GB+)")
        else:
            logger.info(f"✅ Memory: {memory_gb:.1f}GB available")
        
        # Check disk space
        disk = psutil.disk_usage('.')
        disk_gb = disk.free / (1024**3)
        
        if disk_gb < 1:
            logger.error(f"Insufficient disk space: {disk_gb:.1f}GB (minimum: 1GB)")
            return False
        
        logger.info(f"✅ Disk space: {disk_gb:.1f}GB available")
        return True
    
    def check_dependencies(self):
        """Check if all dependencies are installed"""
        logger.info("Checking dependencies...")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'sqlite3',
            'speech_recognition',
            'pyttsx3',
            'nltk',
            'jinja2'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.debug(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                logger.error(f"❌ {package} not found")
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Installing missing packages...")
            
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install'
                ] + missing_packages, check=True)
                logger.info("✅ Dependencies installed successfully")
            except subprocess.CalledProcessError:
                logger.error("❌ Failed to install dependencies")
                return False
        else:
            logger.info("✅ All dependencies are available")
        
        return True
    
    def setup_directories(self):
        """Create necessary directories"""
        logger.info("Setting up directories...")
        
        directories = [
            'database',
            'logs', 
            'voice_logs',
            'static/css',
            'static/js',
            'templates'
        ]
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"✅ {dir_name}")
        
        logger.info("✅ Directory structure ready")
        return True
    
    def initialize_database(self):
        """Initialize database if needed"""
        logger.info("Initializing database...")
        
        try:
            # Import database manager
            sys.path.insert(0, str(self.project_root))
            from database.db_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Run initialization
            asyncio.run(db_manager.initialize())
            asyncio.run(db_manager.populate_demo_data())
            
            logger.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    def check_port_availability(self, port=8000):
        """Check if port is available"""
        logger.info(f"Checking port {port} availability...")
        
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections'] or []:
                    if conn.laddr.port == port:
                        logger.warning(f"Port {port} is already in use by {proc.info['name']} (PID: {proc.info['pid']})")
                        return False
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        logger.info(f"✅ Port {port} is available")
        return True
    
    def download_models(self):
        """Download required AI models"""
        logger.info("Checking AI models...")
        
        try:
            # Download NLTK data
            import nltk
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('wordnet', quiet=True)
            logger.info("✅ NLTK models ready")
            
            # Try to load Whisper model (optional)
            try:
                import whisper
                model = whisper.load_model("base")
                logger.info("✅ Whisper model loaded")
            except Exception as e:
                logger.warning(f"Whisper model not available: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Model download failed: {e}")
            return False
    
    def run_startup_checks(self):
        """Run all startup checks"""
        logger.info("🔍 Running startup checks...")
        logger.info("="*50)
        
        checks = [
            ("System Requirements", self.check_system_requirements),
            ("Dependencies", self.check_dependencies),
            ("Directory Setup", self.setup_directories),
            ("Database Initialization", self.initialize_database),
            ("Port Availability", self.check_port_availability),
            ("AI Models", self.download_models)
        ]
        
        for check_name, check_func in checks:
            logger.info(f"\n📋 {check_name}")
            logger.info("-" * 30)
            
            try:
                if not check_func():
                    logger.error(f"❌ {check_name} failed")
                    return False
                logger.info(f"✅ {check_name} passed")
            except Exception as e:
                logger.error(f"❌ {check_name} failed with exception: {e}")
                return False
        
        logger.info("\n🎉 All startup checks passed!")
        self.startup_checks_passed = True
        return True
    
    def start_server(self, host="0.0.0.0", port=8000, reload=False):
        """Start the FastAPI server"""
        if not self.startup_checks_passed:
            logger.error("❌ Cannot start server - startup checks failed")
            return False
        
        logger.info(f"🚀 Starting AssistX server on {host}:{port}")
        
        try:
            # Prepare uvicorn command
            cmd = [
                sys.executable, '-m', 'uvicorn',
                'main:app',
                '--host', host,
                '--port', str(port),
                '--log-level', 'info'
            ]
            
            if reload:
                cmd.append('--reload')
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Wait a moment for server to start
            time.sleep(3)
            
            if self.server_process.poll() is None:
                logger.info(f"✅ Server started successfully")
                logger.info(f"📱 Dashboard: http://localhost:{port}")
                logger.info(f"📚 API Docs: http://localhost:{port}/docs")
                logger.info("Press Ctrl+C to stop the server")
                return True
            else:
                logger.error("❌ Server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    def monitor_server(self):
        """Monitor server health"""
        if not self.server_process:
            return False
        
        try:
            # Read server output
            for line in iter(self.server_process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
                
                # Check if process is still running
                if self.server_process.poll() is not None:
                    break
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
            return False
        except Exception as e:
            logger.error(f"Server monitoring error: {e}")
            return False
    
    def stop_server(self):
        """Stop the server gracefully"""
        if self.server_process:
            logger.info("Stopping server...")
            
            try:
                # Send SIGTERM first
                self.server_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.server_process.wait(timeout=10)
                    logger.info("✅ Server stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    self.server_process.kill()
                    self.server_process.wait()
                    logger.info("✅ Server stopped (forced)")
                    
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
    
    def run(self, host="0.0.0.0", port=8000, reload=False):
        """Main run method"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("🏥 AssistX - AI Voice Assistant for Medical Clinics")
        logger.info("="*60)
        
        # Run startup checks
        if not self.run_startup_checks():
            logger.error("❌ Startup checks failed - cannot start server")
            sys.exit(1)
        
        # Start server
        if not self.start_server(host, port, reload):
            logger.error("❌ Failed to start server")
            sys.exit(1)
        
        # Monitor server
        try:
            self.monitor_server()
        finally:
            self.stop_server()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AssistX Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    args = parser.parse_args()
    
    server = AssistXServer()
    server.run(host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main() 