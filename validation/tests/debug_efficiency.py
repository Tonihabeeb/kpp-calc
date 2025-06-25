#!/usr/bin/env python3
"""Debug efficiency calculation in Phase 7 test."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.pneumatics.performance_metrics import PerformanceAnalyzer

def debug_efficiency():
    """Debug the efficiency optimization workflow."""
    analyzer = PerformanceAnalyzer(
        rated_power=5000.0,
        baseline_efficiency=0.65
    )
    
    print("=== Phase 1: Poor efficiency ===")
    # Start with poor efficiency
    for i in range(5):
        snapshot = analyzer.record_performance_snapshot(
            electrical_power=5000.0,
            mechanical_power=2500.0,  # 50% efficiency
            thermal_power=100.0
        )
        total_output = snapshot.mechanical_power + snapshot.thermal_power
        efficiency = total_output / snapshot.electrical_power
        print(f"Snapshot {i+1}: Efficiency = {efficiency:.3f} ({total_output}W / {snapshot.electrical_power}W)")
    
    summary1 = analyzer.get_performance_summary()
    print(f"Phase 1 Average Efficiency: {summary1.get('average_efficiency', 0):.3f}")
    
    print("\n=== Phase 2: Improved efficiency ===")
    # Simulate implementing recommendations (improved efficiency)
    for i in range(5):
        snapshot = analyzer.record_performance_snapshot(
            electrical_power=5000.0,
            mechanical_power=4000.0,  # 80% efficiency (improved)
            thermal_power=200.0       # Better thermal boost
        )
        total_output = snapshot.mechanical_power + snapshot.thermal_power
        efficiency = total_output / snapshot.electrical_power
        print(f"Snapshot {i+6}: Efficiency = {efficiency:.3f} ({total_output}W / {snapshot.electrical_power}W)")
    
    final_summary = analyzer.get_performance_summary()
    print(f"Final Average Efficiency: {final_summary.get('average_efficiency', 0):.3f}")
    
    # Show all snapshots
    print(f"\nTotal snapshots: {len(analyzer.performance_snapshots)}")
    for i, snapshot in enumerate(analyzer.performance_snapshots):
        total_output = snapshot.mechanical_power + snapshot.thermal_power
        efficiency = total_output / snapshot.electrical_power
        print(f"All Snapshot {i+1}: Efficiency = {efficiency:.3f}")

if __name__ == "__main__":
    debug_efficiency()
