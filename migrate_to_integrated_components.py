#!/usr/bin/env python3
"""
Migration script to update all legacy component references to use integrated components.
This script will systematically replace all legacy references with their integrated counterparts.
"""

import os
import re
import shutil
from pathlib import Path

def backup_file(file_path):
    """Create a backup of the file before modifying it."""
    backup_path = str(file_path) + '.backup'
    shutil.copy2(file_path, backup_path)
    print(f"Backed up {file_path} to {backup_path}")

def update_file_content(content, replacements):
    """Update file content with the specified replacements."""
    updated_content = content
    
    for old_pattern, new_pattern in replacements:
        updated_content = re.sub(old_pattern, new_pattern, updated_content, flags=re.MULTILINE)
    
    return updated_content

def migrate_file(file_path, replacements):
    """Migrate a single file with the specified replacements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        updated_content = update_file_content(content, replacements)
        
        if updated_content != original_content:
            backup_file(file_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ Updated {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main migration function."""
    print("🚀 Starting migration to integrated components...")
    
    # Define the replacements to make
    replacements = [
        # Legacy electrical system references
        (r'\belectrical_system\b', 'integrated_electrical_system'),
        (r'\bElectricalSystem\b', 'IntegratedElectricalSystem'),
        
        # Legacy pneumatic system references  
        (r'\bpneumatic_system\b', 'pneumatics'),
        (r'\bPneumaticSystem\b', 'PneumaticSystem'),  # Keep class name same
        
        # Legacy integrated_drivetrain references
        (r'\bdrivetrain\b(?!_config)', 'integrated_drivetrain'),
        (r'\bDrivetrain\b(?!Config)', 'IntegratedDrivetrain'),
        
        # Legacy control system references
        (r'\bcontrol_system\b', 'integrated_control_system'),
        (r'\bControlSystem\b', 'Control'),
        
        # Update method calls to use integrated components
        (r'self\.integrated_electrical_system\.', 'self.integrated_electrical_system.'),
        (r'self\.pneumatics\.', 'self.pneumatics.'),
        (r'self\.integrated_drivetrain\.', 'self.integrated_drivetrain.'),
        (r'self\.integrated_control_system\.', 'self.integrated_control_system.'),
        
        # Update hasattr checks
        (r'hasattr\(.*, "integrated_electrical_system"\)', 'hasattr(self, "integrated_electrical_system")'),
        (r'hasattr\(.*, "pneumatics"\)', 'hasattr(self, "pneumatics")'),
        (r'hasattr\(.*, "integrated_drivetrain"\)', 'hasattr(self, "integrated_drivetrain")'),
        (r'hasattr\(.*, "integrated_control_system"\)', 'hasattr(self, "integrated_control_system")'),
        
        # Update getattr calls
        (r'getattr\(.*, "integrated_electrical_system"', 'getattr(self, "integrated_electrical_system"'),
        (r'getattr\(.*, "pneumatics"', 'getattr(self, "pneumatics"'),
        (r'getattr\(.*, "integrated_drivetrain"', 'getattr(self, "integrated_drivetrain"'),
        (r'getattr\(.*, "integrated_control_system"', 'getattr(self, "integrated_control_system"'),
        
        # Update import statements
        (r'from simulation\.components\.integrated_electrical_system import', 'from simulation.components.integrated_electrical_system import'),
        (r'from simulation\.components\.integrated_drivetrain import', 'from simulation.components.integrated_drivetrain import'),
        
        # Update component creation
        (r'create_standard_kmp_electrical_system', 'create_standard_kmp_electrical_system'),
        (r'create_standard_kpp_drivetrain', 'create_standard_kpp_drivetrain'),
        
        # Update emergency method calls to use reset() instead
        (r'\.emergency_shutdown\(\)', '.reset()'),
        (r'\.emergency_vent_all\(\)', '.reset()'),
        (r'\.emergency_stop\(\)', '.reset()'),
        
        # Update config attribute access to use getattr with None checks
        (r'self\.(\w+_config)\.(\w+)', r'getattr(self.\1, "\2", None)'),
        
        # Remove unused expressions
        (r'^\s*i < \(num_floaters // 2\)\s*$', ''),
        (r'^\s*chain_radius \* math\.cos\(theta\)\s*$', ''),
        (r'^\s*self\.params\.get\("ambient_temperature", 20\.0\)\s*$', ''),
    ]
    
    # Files to migrate (exclude test files and backups)
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip test directories and backup files
        dirs[:] = [d for d in dirs if not d.startswith('test') and not d.endswith('_backup')]
        
        for file in files:
            if file.endswith('.py') and not file.endswith('.backup'):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    print(f"📁 Found {len(python_files)} Python files to process")
    
    # Process each file
    updated_count = 0
    for file_path in python_files:
        if migrate_file(file_path, replacements):
            updated_count += 1
    
    print(f"\n🎉 Migration complete!")
    print(f"✅ Updated {updated_count} files")
    print(f"⏭️  Skipped {len(python_files) - updated_count} files (no changes needed)")
    
    # Additional manual fixes needed
    print("\n📝 Manual fixes still needed:")
    print("1. Update ControlConfig class to include target_rpm, kp, ki, kd attributes")
    print("2. Add proper type annotations in SimulationEngine.__init__")
    print("3. Add None checks for all component method calls")
    print("4. Update any remaining legacy references in comments or docstrings")

if __name__ == "__main__":
    main() 