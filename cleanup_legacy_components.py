#!/usr/bin/env python3
"""
Cleanup script to remove legacy component files and update remaining references.
This script will:
1. Remove legacy component files that are no longer needed
2. Update any remaining references to use integrated components
3. Clean up backup files created during migration
"""

import os
import shutil
from pathlib import Path

def remove_legacy_files():
    """Remove legacy component files that are no longer needed."""
    legacy_files = [
        "simulation/components/drivetrain.py",
        "simulation/components/generator.py",
        "simulation/components/drivetrain.py.backup",
        "simulation/components/generator.py.backup",
    ]
    
    removed_count = 0
    for file_path in legacy_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️  Removed legacy file: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
    
    print(f"✅ Removed {removed_count} legacy files")
    return removed_count

def cleanup_backup_files():
    """Remove backup files created during migration."""
    backup_files = [
        "simulation/components/integrated_electrical_system.py.backup",
        "simulation/components/flywheel.py.backup",
        "simulation/components/gearbox.py.backup",
        "simulation/components/one_way_clutch.py.backup",
        "simulation/components/sprocket.py.backup",
        "simulation/components/integrated_drivetrain.py.backup",
        "simulation/components/control.py.backup",
    ]
    
    removed_count = 0
    for file_path in backup_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️  Removed backup file: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
    
    print(f"✅ Removed {removed_count} backup files")
    return removed_count

def update_remaining_references():
    """Update any remaining legacy references in files."""
    # Files that need manual updates
    files_to_update = [
        "validation/tests/test_drivetrain.py",
        "validation/tests/test_generator.py",
        "test_systematic.py",
        "physics_analysis_and_tuning.py",
        "test_no_legacy_components.py",
        "test_phase9_4_integration.py",
    ]
    
    print("\n📝 Files that need manual updates:")
    for file_path in files_to_update:
        if os.path.exists(file_path):
            print(f"  - {file_path}")
        else:
            print(f"  - {file_path} (not found)")
    
    print("\n🔧 Manual updates needed:")
    print("1. Update test files to use integrated components")
    print("2. Replace legacy component imports with integrated equivalents")
    print("3. Update test methods to work with integrated component interfaces")

def main():
    """Main cleanup function."""
    print("🧹 Starting legacy component cleanup...")
    
    # Remove legacy files
    legacy_removed = remove_legacy_files()
    
    # Clean up backup files
    backup_removed = cleanup_backup_files()
    
    # Identify files needing manual updates
    update_remaining_references()
    
    print(f"\n🎉 Cleanup complete!")
    print(f"✅ Removed {legacy_removed} legacy files")
    print(f"✅ Removed {backup_removed} backup files")
    
    print("\n📋 Next steps:")
    print("1. Update remaining test files to use integrated components")
    print("2. Run the migration script to update all references")
    print("3. Test the system to ensure everything works correctly")
    print("4. Update documentation to reflect the new architecture")

if __name__ == "__main__":
    main() 