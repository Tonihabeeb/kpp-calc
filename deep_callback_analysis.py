#!/usr/bin/env python3
"""
Deep Analysis of Callback Logic Value Mismatches
Comprehensive check of all callback logic, data structures, and value mappings
"""

import re
import json
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

def extract_data_structures(file_content: str) -> Dict[str, Any]:
    """Extract all data structures and their expected formats"""
    structures = {}
    
    # Find dcc.Store definitions
    store_pattern = r'dcc\.Store\(id="([^"]+)",\s*data=({[^}]+})\)'
    matches = re.finditer(store_pattern, file_content)
    
    for match in matches:
        store_id = match.group(1)
        data_str = match.group(2)
        try:
            # Clean up the data string and evaluate
            data_str = data_str.replace("'", '"')
            data = json.loads(data_str)
            structures[store_id] = data
        except:
            structures[store_id] = "parse_error"
    
    return structures

def extract_callback_logic(file_content: str) -> List[Dict]:
    """Extract all callback definitions and their logic"""
    callbacks = []
    
    # Find all @app.callback blocks
    callback_pattern = r'@app\.callback\((.*?)\ndef\s+(\w+)\s*\((.*?)\):(.*?)(?=#|\n@app\.callback|\nif __name__|\Z)'
    matches = re.finditer(callback_pattern, file_content, re.DOTALL)
    
    for match in matches:
        callback_def = match.group(1)
        function_name = match.group(2)
        params = match.group(3)
        function_body = match.group(4)
        
        # Extract Output patterns
        outputs = re.findall(r'Output\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', callback_def)
        
        # Extract Input patterns
        inputs = re.findall(r'Input\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', callback_def)
        
        # Extract State patterns
        states = re.findall(r'State\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', callback_def)
        
        callbacks.append({
            'function_name': function_name,
            'outputs': outputs,
            'inputs': inputs,
            'states': states,
            'params': params,
            'body': function_body,
            'raw_definition': callback_def
        })
    
    return callbacks

def extract_value_mappings(file_content: str) -> Dict[str, List[str]]:
    """Extract all value mappings and comparisons in the code"""
    mappings = defaultdict(list)
    
    # Find value comparisons
    comparison_patterns = [
        r'==\s*["\']([^"\']+)["\']',  # == "value"
        r'!=\s*["\']([^"\']+)["\']',  # != "value"
        r'in\s*\[([^\]]+)\]',         # in ["value1", "value2"]
        r'get\([^,]+,\s*["\']([^"\']+)["\']\)',  # .get(key, "default")
    ]
    
    for pattern in comparison_patterns:
        matches = re.finditer(pattern, file_content)
        for match in matches:
            value = match.group(1)
            if ',' in value:  # Handle lists
                values = [v.strip().strip('"\'') for v in value.split(',')]
                for v in values:
                    if v:
                        mappings['comparison_values'].append(v)
            else:
                mappings['comparison_values'].append(value)
    
    # Find status values
    status_pattern = r'status.*?["\']([^"\']+)["\']'
    status_matches = re.finditer(status_pattern, file_content)
    for match in status_matches:
        mappings['status_values'].append(match.group(1))
    
    # Find health values
    health_pattern = r'health.*?["\']([^"\']+)["\']'
    health_matches = re.finditer(health_pattern, file_content)
    for match in health_matches:
        mappings['health_values'].append(match.group(1))
    
    return dict(mappings)

def analyze_data_flow_consistency(callbacks: List[Dict], data_structures: Dict) -> List[Dict]:
    """Analyze data flow consistency between callbacks and data structures"""
    issues = []
    
    for callback in callbacks:
        # Check if callback outputs match data structure expectations
        for output_id, output_prop in callback['outputs']:
            if output_id in data_structures:
                expected_structure = data_structures[output_id]
                # Check if the callback logic matches the expected data structure
                if isinstance(expected_structure, dict):
                    # Look for key access patterns in callback body
                    key_pattern = r'\.get\(["\']([^"\']+)["\']'
                    accessed_keys = re.findall(key_pattern, callback['body'])
                    
                    for key in accessed_keys:
                        if key not in expected_structure:
                            issues.append({
                                'type': 'missing_key',
                                'callback': callback['function_name'],
                                'output': output_id,
                                'key': key,
                                'expected_keys': list(expected_structure.keys())
                            })
    
    return issues

def analyze_value_mismatches(callbacks: List[Dict], value_mappings: Dict) -> List[Dict]:
    """Analyze value mismatches in callback logic"""
    issues = []
    
    # Extract all unique values used in comparisons
    all_comparison_values = set(value_mappings.get('comparison_values', []))
    all_status_values = set(value_mappings.get('status_values', []))
    all_health_values = set(value_mappings.get('health_values', []))
    
    # Check for inconsistencies in status handling
    for callback in callbacks:
        if 'status' in callback['body'].lower():
            # Look for status comparisons
            status_comparisons = re.findall(r'status.*?==\s*["\']([^"\']+)["\']', callback['body'])
            for status in status_comparisons:
                if status not in all_status_values:
                    issues.append({
                        'type': 'unexpected_status',
                        'callback': callback['function_name'],
                        'value': status,
                        'expected_statuses': list(all_status_values)
                    })
    
    # Check for inconsistencies in health handling
    for callback in callbacks:
        if 'health' in callback['body'].lower():
            # Look for health comparisons
            health_comparisons = re.findall(r'health.*?==\s*["\']([^"\']+)["\']', callback['body'])
            for health in health_comparisons:
                if health not in all_health_values:
                    issues.append({
                        'type': 'unexpected_health',
                        'callback': callback['function_name'],
                        'value': health,
                        'expected_healths': list(all_health_values)
                    })
    
    return issues

def analyze_data_type_consistency(callbacks: List[Dict]) -> List[Dict]:
    """Analyze data type consistency in callbacks"""
    issues = []
    
    for callback in callbacks:
        # Check for potential type mismatches
        body = callback['body']
        
        # Check for numeric operations on potentially non-numeric data
        numeric_ops = ['* 100', '/ 1000', '+ ', '- ', '* ']
        for op in numeric_ops:
            if op in body:
                # Look for the variable being operated on
                op_pattern = rf'([a-zA-Z_][a-zA-Z0-9_]*)\s*\{op[1:]}'
                matches = re.findall(op_pattern, body)
                for var in matches:
                    # Check if this variable might be non-numeric
                    if var in ['status', 'health', 'error']:
                        issues.append({
                            'type': 'potential_type_mismatch',
                            'callback': callback['function_name'],
                            'variable': var,
                            'operation': op,
                            'suggestion': f'Check if {var} is numeric before {op} operation'
                        })
    
    return issues

def analyze_missing_error_handling(callbacks: List[Dict]) -> List[Dict]:
    """Analyze missing error handling in callbacks"""
    issues = []
    
    for callback in callbacks:
        body = callback['body']
        
        # Check for API calls without error handling
        api_calls = re.findall(r'requests\.(get|post|put|delete)\(', body)
        if api_calls:
            # Check if there's try/except around API calls
            if 'try:' not in body or 'except' not in body:
                issues.append({
                    'type': 'missing_error_handling',
                    'callback': callback['function_name'],
                    'api_calls': api_calls,
                    'suggestion': 'Wrap API calls in try/except blocks'
                })
        
        # Check for dictionary access without .get()
        dict_access = re.findall(r'(\w+)\[["\']([^"\']+)["\']\]', body)
        for var, key in dict_access:
            if f'{var}.get(' not in body:
                issues.append({
                    'type': 'unsafe_dict_access',
                    'callback': callback['function_name'],
                    'variable': var,
                    'key': key,
                    'suggestion': f'Use {var}.get("{key}") instead of {var}["{key}"]'
                })
    
    return issues

def main():
    """Main analysis function"""
    print("🔍 Deep Callback Logic Analysis")
    print("=" * 60)
    
    # Read the main Dash app file
    try:
        with open('dash_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ dash_app.py not found")
        return
    
    print("📊 Extracting data structures...")
    data_structures = extract_data_structures(content)
    
    print("🔄 Extracting callback logic...")
    callbacks = extract_callback_logic(content)
    
    print("🎯 Extracting value mappings...")
    value_mappings = extract_value_mappings(content)
    
    print("\n📋 Analysis Results:")
    print("=" * 60)
    
    # Data Structure Analysis
    print(f"\n📦 Data Structures Found: {len(data_structures)}")
    for store_id, structure in data_structures.items():
        print(f"  • {store_id}: {type(structure).__name__}")
        if isinstance(structure, dict):
            print(f"    Keys: {list(structure.keys())}")
    
    # Callback Analysis
    print(f"\n🔄 Callbacks Found: {len(callbacks)}")
    for callback in callbacks:
        print(f"  • {callback['function_name']}")
        print(f"    Outputs: {len(callback['outputs'])}")
        print(f"    Inputs: {len(callback['inputs'])}")
        print(f"    States: {len(callback['states'])}")
    
    # Value Mappings Analysis
    print(f"\n🎯 Value Mappings Found:")
    for category, values in value_mappings.items():
        unique_values = list(set(values))
        print(f"  • {category}: {len(unique_values)} unique values")
        print(f"    Values: {unique_values[:10]}{'...' if len(unique_values) > 10 else ''}")
    
    # Run specific analyses
    print(f"\n🔍 Running Deep Analysis...")
    
    data_flow_issues = analyze_data_flow_consistency(callbacks, data_structures)
    value_mismatch_issues = analyze_value_mismatches(callbacks, value_mappings)
    type_consistency_issues = analyze_data_type_consistency(callbacks)
    error_handling_issues = analyze_missing_error_handling(callbacks)
    
    # Report issues
    all_issues = data_flow_issues + value_mismatch_issues + type_consistency_issues + error_handling_issues
    
    if all_issues:
        print(f"\n⚠️  Issues Found: {len(all_issues)}")
        print("=" * 60)
        
        for i, issue in enumerate(all_issues, 1):
            print(f"\n{i}. {issue['type'].upper()}")
            print(f"   Callback: {issue['callback']}")
            if 'output' in issue:
                print(f"   Output: {issue['output']}")
            if 'value' in issue:
                print(f"   Value: {issue['value']}")
            if 'suggestion' in issue:
                print(f"   Suggestion: {issue['suggestion']}")
            if 'expected_keys' in issue:
                print(f"   Expected Keys: {issue['expected_keys']}")
    else:
        print(f"\n✅ No issues found! All callback logic appears consistent.")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  • Data Structures: {len(data_structures)}")
    print(f"  • Callbacks: {len(callbacks)}")
    print(f"  • Issues Found: {len(all_issues)}")
    
    # Save detailed report
    report = {
        'data_structures': data_structures,
        'callbacks': [{
            'function_name': c['function_name'],
            'outputs': c['outputs'],
            'inputs': c['inputs'],
            'states': c['states']
        } for c in callbacks],
        'value_mappings': value_mappings,
        'issues': all_issues
    }
    
    with open('deep_callback_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: deep_callback_analysis_report.json")

if __name__ == "__main__":
    main() 