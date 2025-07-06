#!/usr/bin/env python3
"""
Phase 8 Integration Gap Analysis Script
This script validates the analysis and identifies exactly what systems are developed but not integrated.
"""

import importlib.util
import os
import sys
from pathlib import Path


def check_file_exists(filepath):
    """Check if a file exists and return file size"""
    path = Path(filepath)
    if path.exists():
        return True, path.stat().st_size
    return False, 0


def analyze_integration_gaps():
    """Analyze what advanced systems exist but aren't integrated"""

    print("🔍 PHASE 8 INTEGRATION GAP ANALYSIS")
    print("=" * 60)

    # Define base directory
    base_dir = Path("h:/My Drive/kpp force calc")

    # Check advanced systems that should exist
    advanced_systems = {
        "Advanced IntegratedDrivetrain System": [
            "simulation/components/integrated_drivetrain.py",
            "simulation/components/sprocket.py",
            "simulation/components/gearbox.py",
            "simulation/components/one_way_clutch.py",
            "simulation/components/flywheel.py",
            "simulation/components/clutch.py",
        ],
        "Advanced Electrical System": [
            "simulation/components/integrated_electrical_system.py",
            "simulation/components/advanced_generator.py",
            "simulation/components/power_electronics.py",
        ],
        "Grid Services System": [
            "simulation/grid_services/__init__.py",
            "simulation/grid_services/coordinator.py",
            "phase7_implementation_plan.md",
        ],
        "Advanced Control System": [
            "simulation/control/integrated_control_system.py",
            "simulation/control/load_manager.py",
            "simulation/control/transient_event_controller.py",
        ],
        "Enhanced Loss Model": ["simulation/physics/integrated_loss_model.py"],
    }

    # Check current backend integration
    integration_status = {}

    for system_name, files in advanced_systems.items():
        print(f"\n📋 {system_name}")
        print("-" * 40)

        system_status = {"files_exist": [], "files_missing": [], "total_size": 0}

        for file_path in files:
            full_path = base_dir / file_path
            exists, size = check_file_exists(full_path)

            if exists:
                system_status["files_exist"].append(file_path)
                system_status["total_size"] += size
                print(f"  ✅ {file_path} ({size:,} bytes)")
            else:
                system_status["files_missing"].append(file_path)
                print(f"  ❌ {file_path} (MISSING)")

        integration_status[system_name] = system_status

    # Check engine.py integration
    print(f"\n🔧 ENGINE INTEGRATION ANALYSIS")
    print("-" * 40)

    engine_file = base_dir / "simulation/engine.py"
    if engine_file.exists():
        with open(engine_file, "r", encoding="utf-8") as f:
            engine_content = f.read()

        # Check what's imported
        imports_check = {
            "integrated_drivetrain": "from simulation.components.integrated_drivetrain import"
            in engine_content,
            "integrated_electrical": "from simulation.components.integrated_electrical_system import"
            in engine_content,
            "grid_services": "from simulation.grid_services import" in engine_content,
            "integrated_control": "from simulation.control.integrated_control_system import"
            in engine_content,
            "loss_model": "from simulation.physics.integrated_loss_model import"
            in engine_content,
        }

        # Check what's actually used in step() method
        usage_check = {
            "integrated_drivetrain": "self.integrated_drivetrain.update("
            in engine_content,
            "integrated_electrical": "self.integrated_electrical_system.update("
            in engine_content,
            "grid_services": "self.grid_services_coordinator.update(" in engine_content,
            "integrated_control": "self.integrated_control_system.update("
            in engine_content,
            "loss_model": "self.enhanced_loss_model.update(" in engine_content,
        }

        # Check legacy systems still used
        legacy_usage = {
            "legacy_drivetrain": "self.integrated_drivetrain.update(" in engine_content
            or "self.integrated_drivetrain.apply_torque(" in engine_content,
            "legacy_generator": "self.generator.calculate_power_output("
            in engine_content
            or "self.generator.get_load_torque(" in engine_content,
        }

        print("  📥 IMPORTS (what's available):")
        for system, imported in imports_check.items():
            status = "✅" if imported else "❌"
            print(f"    {status} {system}")

        print("\n  🔄 USAGE (what's actually used):")
        for system, used in usage_check.items():
            status = "✅" if used else "❌"
            print(f"    {status} {system}")

        print("\n  🏚️ LEGACY SYSTEMS (should be replaced):")
        for system, used in legacy_usage.items():
            status = "⚠️ STILL USED" if used else "✅ REPLACED"
            print(f"    {status} {system}")

    # Check app.py integration
    print(f"\n🌐 FRONTEND API INTEGRATION")
    print("-" * 40)

    app_file = base_dir / "app.py"
    if app_file.exists():
        with open(app_file, "r", encoding="utf-8") as f:
            app_content = f.read()

        # Check for advanced system endpoints
        endpoint_check = {
            "drivetrain_status": '@app.route("/data/drivetrain_status")' in app_content,
            "electrical_status": '@app.route("/data/electrical_status")' in app_content,
            "grid_services_status": '@app.route("/data/grid_services_status")'
            in app_content,
            "control_system_status": '@app.route("/data/control_system_status")'
            in app_content,
            "loss_analysis": '@app.route("/data/loss_analysis")' in app_content,
            "pneumatic_status": '@app.route("/data/pneumatic_status")'
            in app_content,  # This should exist
        }

        print("  🔗 API ENDPOINTS:")
        for endpoint, exists in endpoint_check.items():
            status = "✅" if exists else "❌"
            print(f"    {status} /data/{endpoint}")

    # Check templates integration
    print(f"\n🎨 FRONTEND UI INTEGRATION")
    print("-" * 40)

    index_file = base_dir / "templates/index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            template_content = f.read()

        # Check for advanced system UI sections
        ui_sections = {
            "pneumatics": "Phase 7 Pneumatic System"
            in template_content,  # Should exist
            "advanced_drivetrain": "Advanced IntegratedDrivetrain System" in template_content,
            "advanced_electrical": "Advanced Electrical System" in template_content,
            "grid_services": "Grid Services" in template_content,
            "integrated_control_system": "Control System" in template_content,
            "loss_analysis": "Loss Analysis" in template_content,
        }

        print("  🖥️ UI SECTIONS:")
        for section, exists in ui_sections.items():
            status = "✅" if exists else "❌"
            print(f"    {status} {section}")

    # Summary and recommendations
    print(f"\n📊 INTEGRATION SUMMARY")
    print("=" * 60)

    total_advanced_files = sum(len(files) for files in advanced_systems.values())
    existing_files = sum(
        len(status["files_exist"]) for status in integration_status.values()
    )
    total_size = sum(status["total_size"] for status in integration_status.values())

    print(
        f"Advanced Systems Coverage: {existing_files}/{total_advanced_files} files ({existing_files/total_advanced_files*100:.1f}%)"
    )
    print(f"Total Advanced Code: {total_size:,} bytes ({total_size/1024:.1f} KB)")

    if existing_files > 0:
        print(f"\n✅ GOOD NEWS: {existing_files} advanced system files found!")
        print(f"💡 OPPORTUNITY: Most advanced systems are developed but NOT INTEGRATED")
        print(f"🎯 SOLUTION: Phase 8 Integration Plan will connect everything")

        # Calculate potential impact
        unused_systems = []
        for system_name, status in integration_status.items():
            if len(status["files_exist"]) > 0:
                unused_systems.append(
                    f"- {system_name} ({len(status['files_exist'])} files, {status['total_size']:,} bytes)"
                )

        if unused_systems:
            print(f"\n🚀 UNUSED ADVANCED SYSTEMS:")
            for system in unused_systems:
                print(f"  {system}")

    else:
        print(f"\n❌ NO ADVANCED SYSTEMS FOUND")
        print(f"📝 RECOMMENDATION: Develop advanced systems first")


if __name__ == "__main__":
    analyze_integration_gaps()
