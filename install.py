#!/usr/bin/env python3
"""
AssistX Installation Script
Simple installation and setup for AssistX - AI Voice Assistant for Medical Clinics
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description=""):
    """Run a shell command"""
    logger.info(f"Running: {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ Success")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed: {e.stderr}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version < (3, 8):
        logger.error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install required dependencies"""
    logger.info("Installing dependencies...")
    return run_command("pip install -r requirements.txt", "Installing Python packages")

def create_directories():
    """Create necessary directories"""
    logger.info("Creating directories...")
    directories = ['database', 'logs', 'voice_logs', 'static/css', 'static/js', 'templates']
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ Directories created")
    return True

def initialize_database():
    """Initialize the database"""
    logger.info("Initializing database...")
    try:
        from database.db_manager import DatabaseManager
        import asyncio
        
        db_manager = DatabaseManager()
        asyncio.run(db_manager.initialize())
        asyncio.run(db_manager.populate_demo_data())
        
        logger.info("✅ Database initialized with demo data")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main installation process"""
    logger.info("🏥 AssistX Installation")
    logger.info("="*40)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories),
        ("Initializing database", initialize_database)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n📋 {step_name}")
        if not step_func():
            logger.error(f"❌ Installation failed at: {step_name}")
            return False
    
    logger.info("\n🎉 Installation completed successfully!")
    logger.info("\nTo start AssistX:")
    logger.info("  python start_server.py")
    logger.info("\nOr run directly:")
    logger.info("  python main.py")
    logger.info("\nThen open: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 