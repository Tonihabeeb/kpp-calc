#!/usr/bin/env python3
"""
Replace Legacy Drivetrain with Integrated Drivetrain
This script replaces the legacy drivetrain.py with the new integrated_drivetrain.py
and tests the server functionality.
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegacyDrivetrainReplacer:
    """Replace legacy drivetrain with integrated drivetrain"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.legacy_drivetrain = self.project_root / "simulation" / "components" / "drivetrain.py"
        self.integrated_drivetrain = self.project_root / "simulation" / "components" / "integrated_drivetrain.py"
        self.backup_dir = self.project_root / "backup" / "legacy_drivetrain_backup"
        
    def run_replacement(self) -> bool:
        """Run the legacy drivetrain replacement"""
        logger.info("Starting legacy drivetrain replacement...")
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Replace legacy drivetrain with integrated one
            if not self.replace_drivetrain():
                return False
                
            # Step 3: Update imports in key files
            if not self.update_imports():
                return False
                
            # Step 4: Test server functionality
            if not self.test_server():
                return False
                
            logger.info("Legacy drivetrain replacement completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Legacy drivetrain replacement failed: {e}")
            return False
    
    def create_backup(self) -> None:
        """Create backup of legacy drivetrain"""
        logger.info("Creating backup of legacy drivetrain...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        if self.legacy_drivetrain.exists():
            import shutil
            shutil.copy2(self.legacy_drivetrain, self.backup_dir / "drivetrain_legacy.py")
            logger.info("Legacy drivetrain backed up successfully")
        else:
            logger.warning("Legacy drivetrain file not found")
    
    def replace_drivetrain(self) -> bool:
        """Replace legacy drivetrain with integrated drivetrain"""
        logger.info("Replacing legacy drivetrain with integrated drivetrain...")
        
        if not self.integrated_drivetrain.exists():
            logger.error("Integrated drivetrain file not found")
            return False
        
        # Read integrated drivetrain content
        with open(self.integrated_drivetrain, 'r', encoding='utf-8') as f:
            integrated_content = f.read()
        
        # Create new drivetrain.py with integrated content
        new_drivetrain_content = f'''"""
Integrated Drivetrain System for KPP Simulator
This replaces the legacy drivetrain.py with the new integrated system.
"""

{integrated_content}
'''
        
        # Write new drivetrain.py
        with open(self.legacy_drivetrain, 'w', encoding='utf-8') as f:
            f.write(new_drivetrain_content)
        
        logger.info("Legacy drivetrain replaced with integrated drivetrain")
        return True
    
    def update_imports(self) -> bool:
        """Update imports in key files to use new drivetrain"""
        logger.info("Updating imports in key files...")
        
        # Files that need import updates
        files_to_update = [
            "simulation/engine.py",
            "simulation/simulation.py",
            "tests/conftest.py"
        ]
        
        for file_path in files_to_update:
            full_path = self.project_root / file_path
            if full_path.exists():
                if not self.update_file_imports(full_path):
                    logger.warning(f"Failed to update imports in {file_path}")
        
        logger.info("Import updates completed")
        return True
    
    def update_file_imports(self, file_path: Path) -> bool:
        """Update imports in a specific file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace legacy drivetrain imports with integrated ones
            old_imports = [
                "from simulation.components.drivetrain import Drivetrain, DrivetrainConfig",
                "from .components.drivetrain import Drivetrain",
                "from simulation.components.drivetrain import Drivetrain, DrivetrainConfig"
            ]
            
            new_imports = [
                "from simulation.components.drivetrain import IntegratedDrivetrain, DrivetrainConfig",
                "from .components.drivetrain import IntegratedDrivetrain",
                "from simulation.components.drivetrain import IntegratedDrivetrain, DrivetrainConfig"
            ]
            
            for old_import, new_import in zip(old_imports, new_imports):
                content = content.replace(old_import, new_import)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating {file_path}: {e}")
            return False
    
    def test_server(self) -> bool:
        """Test server functionality with new drivetrain"""
        logger.info("Testing server functionality...")
        
        try:
            # Start server in background
            logger.info("Starting server...")
            server_process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Test basic server functionality
            test_results = []
            
            # Test 1: Check if server is running
            try:
                response = requests.get("http://127.0.0.1:9100/", timeout=5)
                test_results.append(("Server Running", response.status_code == 200))
            except requests.exceptions.RequestException:
                test_results.append(("Server Running", False))
            
            # Test 2: Test simulation API
            try:
                response = requests.get("http://127.0.0.1:9100/api/simulation/status", timeout=5)
                test_results.append(("Simulation API", response.status_code == 200))
            except requests.exceptions.RequestException:
                test_results.append(("Simulation API", False))
            
            # Test 3: Test start simulation
            try:
                response = requests.post("http://127.0.0.1:9100/api/simulation/control", 
                                       json={"action": "start"}, timeout=5)
                test_results.append(("Start Simulation", response.status_code == 200))
            except requests.exceptions.RequestException:
                test_results.append(("Start Simulation", False))
            
            # Test 4: Test stop simulation
            try:
                response = requests.post("http://127.0.0.1:9100/api/simulation/control", 
                                       json={"action": "stop"}, timeout=5)
                test_results.append(("Stop Simulation", response.status_code == 200))
            except requests.exceptions.RequestException:
                test_results.append(("Stop Simulation", False))
            
            # Stop server
            server_process.terminate()
            server_process.wait(timeout=5)
            
            # Report results
            logger.info("Server test results:")
            for test_name, passed in test_results:
                status = "PASS" if passed else "FAIL"
                logger.info(f"  {test_name}: {status}")
            
            # Check if all tests passed
            all_passed = all(passed for _, passed in test_results)
            
            if all_passed:
                logger.info("All server tests passed!")
            else:
                logger.warning("Some server tests failed")
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Server test failed: {e}")
            return False

def main():
    """Main execution function"""
    logger.info("Starting Legacy Drivetrain Replacement")
    
    replacer = LegacyDrivetrainReplacer()
    success = replacer.run_replacement()
    
    if success:
        logger.info("Legacy drivetrain replacement completed successfully!")
        logger.info("The simulator now uses the integrated drivetrain system.")
        logger.info("All physics upgrade components are now active.")
    else:
        logger.error("Legacy drivetrain replacement failed.")
        sys.exit(1)

if __name__ == "__main__":
    main() 