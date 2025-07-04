#!/usr/bin/env python3
"""
Targeted Value Mismatch Analysis
Focuses on specific value mismatches identified in the codebase
"""

import re
import json
from typing import Dict, List, Set

def analyze_health_value_mismatches():
    """Analyze health value mismatches between data sources and callbacks"""
    print("🔍 Analyzing Health Value Mismatches")
    print("=" * 50)
    
    # Read the dash_app.py file
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all health value assignments
    health_assignments = []
    
    # Pattern 1: health = 'value'
    pattern1 = r"health\s*=\s*['\"]([^'\"]+)['\"]"
    matches1 = re.finditer(pattern1, content)
    for match in matches1:
        health_assignments.append({
            'type': 'direct_assignment',
            'value': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    # Pattern 2: 'health': 'value'
    pattern2 = r"'health':\s*['\"]([^'\"]+)['\"]"
    matches2 = re.finditer(pattern2, content)
    for match in matches2:
        health_assignments.append({
            'type': 'dict_key',
            'value': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    # Pattern 3: "health": "value"
    pattern3 = r'"health":\s*["\']([^"\']+)["\']'
    matches3 = re.finditer(pattern3, content)
    for match in matches3:
        health_assignments.append({
            'type': 'dict_key_quoted',
            'value': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    print(f"Found {len(health_assignments)} health value assignments:")
    for assignment in health_assignments:
        print(f"  • {assignment['value']} ({assignment['type']}) at line ~{assignment['line']}")
    
    # Find all health value comparisons
    health_comparisons = []
    
    # Pattern: health == 'value'
    comp_pattern = r"health.*?==\s*['\"]([^'\"]+)['\"]"
    comp_matches = re.finditer(comp_pattern, content)
    for match in comp_matches:
        health_comparisons.append({
            'value': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    # Pattern: health in ['value1', 'value2']
    in_pattern = r"health.*?in\s*\[([^\]]+)\]"
    in_matches = re.finditer(in_pattern, content)
    for match in in_matches:
        values_str = match.group(1)
        values = [v.strip().strip('"\'') for v in values_str.split(',')]
        for value in values:
            if value:
                health_comparisons.append({
                    'value': value,
                    'line': content[:match.start()].count('\n') + 1
                })
    
    print(f"\nFound {len(health_comparisons)} health value comparisons:")
    for comparison in health_comparisons:
        print(f"  • {comparison['value']} at line ~{comparison['line']}")
    
    # Find mismatches
    assigned_values = set(assignment['value'] for assignment in health_assignments)
    compared_values = set(comparison['value'] for comparison in health_comparisons)
    
    print(f"\n📊 Analysis Results:")
    print(f"  • Assigned values: {assigned_values}")
    print(f"  • Compared values: {compared_values}")
    
    # Check for mismatches
    missing_in_comparison = assigned_values - compared_values
    missing_in_assignment = compared_values - assigned_values
    
    if missing_in_comparison:
        print(f"\n⚠️  Values assigned but not compared: {missing_in_comparison}")
    
    if missing_in_assignment:
        print(f"\n⚠️  Values compared but not assigned: {missing_in_assignment}")
    
    if not missing_in_comparison and not missing_in_assignment:
        print(f"\n✅ All health values are consistent!")
    
    return {
        'assignments': health_assignments,
        'comparisons': health_comparisons,
        'assigned_values': list(assigned_values),
        'compared_values': list(compared_values),
        'missing_in_comparison': list(missing_in_comparison),
        'missing_in_assignment': list(missing_in_assignment)
    }

def analyze_status_value_mismatches():
    """Analyze status value mismatches between data sources and callbacks"""
    print("\n🔍 Analyzing Status Value Mismatches")
    print("=" * 50)
    
    # Read the dash_app.py file
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all status value assignments
    status_assignments = []
    
    # Pattern 1: status = 'value'
    pattern1 = r"status\s*=\s*['\"]([^'\"]+)['\"]"
    matches1 = re.finditer(pattern1, content)
    for match in matches1:
        status_assignments.append({
            'type': 'direct_assignment',
            'value': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    # Pattern 2: 'status': 'value'
    pattern2 = r"'status':\s*['\"]([^'\"]+)['\"]"
    matches2 = re.finditer(pattern2, content)
    for match in matches2:
        status_assignments.append({
            'type': 'dict_key',
            'value': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    # Pattern 3: "status": "value"
    pattern3 = r'"status":\s*["\']([^"\']+)["\']'
    matches3 = re.finditer(pattern3, content)
    for match in matches3:
        status_assignments.append({
            'type': 'dict_key_quoted',
            'value': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    print(f"Found {len(status_assignments)} status value assignments:")
    for assignment in status_assignments:
        print(f"  • {assignment['value']} ({assignment['type']}) at line ~{assignment['line']}")
    
    # Find all status value comparisons
    status_comparisons = []
    
    # Pattern: status == 'value'
    comp_pattern = r"status.*?==\s*['\"]([^'\"]+)['\"]"
    comp_matches = re.finditer(comp_pattern, content)
    for match in comp_matches:
        status_comparisons.append({
            'value': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    print(f"\nFound {len(status_comparisons)} status value comparisons:")
    for comparison in status_comparisons:
        print(f"  • {comparison['value']} at line ~{comparison['line']}")
    
    # Find mismatches
    assigned_values = set(assignment['value'] for assignment in status_assignments)
    compared_values = set(comparison['value'] for comparison in status_comparisons)
    
    print(f"\n📊 Analysis Results:")
    print(f"  • Assigned values: {assigned_values}")
    print(f"  • Compared values: {compared_values}")
    
    # Check for mismatches
    missing_in_comparison = assigned_values - compared_values
    missing_in_assignment = compared_values - assigned_values
    
    if missing_in_comparison:
        print(f"\n⚠️  Values assigned but not compared: {missing_in_comparison}")
    
    if missing_in_assignment:
        print(f"\n⚠️  Values compared but not assigned: {missing_in_assignment}")
    
    if not missing_in_comparison and not missing_in_assignment:
        print(f"\n✅ All status values are consistent!")
    
    return {
        'assignments': status_assignments,
        'comparisons': status_comparisons,
        'assigned_values': list(assigned_values),
        'compared_values': list(compared_values),
        'missing_in_comparison': list(missing_in_comparison),
        'missing_in_assignment': list(missing_in_assignment)
    }

def analyze_data_structure_mismatches():
    """Analyze data structure mismatches between expected and actual data"""
    print("\n🔍 Analyzing Data Structure Mismatches")
    print("=" * 50)
    
    # Read the dash_app.py file
    with open('dash_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Expected data structure from initial store
    expected_structure = {
        'time': 0.0,
        'power': 0.0,
        'torque': 0.0,
        'power_output': 0.0,
        'overall_efficiency': 0.0,
        'status': 'stopped',
        'health': 'initializing'
    }
    
    print(f"Expected structure keys: {list(expected_structure.keys())}")
    
    # Find all data access patterns
    data_access_patterns = []
    
    # Pattern: .get('key', default)
    get_pattern = r"\.get\(['\"]([^'\"]+)['\"]"
    get_matches = re.finditer(get_pattern, content)
    for match in get_matches:
        data_access_patterns.append({
            'type': 'get_method',
            'key': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    # Pattern: ['key']
    bracket_pattern = r"\[['\"]([^'\"]+)['\"]\]"
    bracket_matches = re.finditer(bracket_pattern, content)
    for match in bracket_matches:
        data_access_patterns.append({
            'type': 'bracket_access',
            'key': match.group(1),
            'line': content[:match.start()].count('\n') + 1
        })
    
    # Filter for simulation data access
    simulation_data_access = [
        pattern for pattern in data_access_patterns
        if any(keyword in content[max(0, pattern['line']-5):pattern['line']+5] 
               for keyword in ['simulation_data', 'new_data', 'data'])
    ]
    
    print(f"Found {len(simulation_data_access)} simulation data access patterns:")
    accessed_keys = set()
    for access in simulation_data_access:
        accessed_keys.add(access['key'])
        print(f"  • {access['key']} ({access['type']}) at line ~{access['line']}")
    
    # Check for mismatches
    expected_keys = set(expected_structure.keys())
    missing_keys = expected_keys - accessed_keys
    unexpected_keys = accessed_keys - expected_keys
    
    print(f"\n📊 Analysis Results:")
    print(f"  • Expected keys: {expected_keys}")
    print(f"  • Accessed keys: {accessed_keys}")
    
    if missing_keys:
        print(f"\n⚠️  Expected keys not accessed: {missing_keys}")
    
    if unexpected_keys:
        print(f"\n⚠️  Unexpected keys accessed: {unexpected_keys}")
    
    if not missing_keys and not unexpected_keys:
        print(f"\n✅ All data structure keys are consistent!")
    
    return {
        'expected_keys': list(expected_keys),
        'accessed_keys': list(accessed_keys),
        'missing_keys': list(missing_keys),
        'unexpected_keys': list(unexpected_keys)
    }

def main():
    """Main analysis function"""
    print("🎯 Targeted Value Mismatch Analysis")
    print("=" * 60)
    
    # Run all analyses
    health_analysis = analyze_health_value_mismatches()
    status_analysis = analyze_status_value_mismatches()
    structure_analysis = analyze_data_structure_mismatches()
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  • Health mismatches: {len(health_analysis['missing_in_comparison']) + len(health_analysis['missing_in_assignment'])}")
    print(f"  • Status mismatches: {len(status_analysis['missing_in_comparison']) + len(status_analysis['missing_in_assignment'])}")
    print(f"  • Structure mismatches: {len(structure_analysis['missing_keys']) + len(structure_analysis['unexpected_keys'])}")
    
    # Save detailed report
    report = {
        'health_analysis': health_analysis,
        'status_analysis': status_analysis,
        'structure_analysis': structure_analysis
    }
    
    with open('targeted_value_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: targeted_value_analysis_report.json")

if __name__ == "__main__":
    main() 