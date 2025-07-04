#!/usr/bin/env python3
"""
Deep analysis script to find callback reference issues in Dash apps.
Checks for:
1. Non-existent component IDs referenced in callbacks
2. Components that might only exist in conditional layouts (suppressed)
3. Mismatched Input/Output/State references
4. Orphaned components (exist in layout but not used in callbacks)
"""

import re
import ast
from typing import Dict, List, Set, Tuple
from collections import defaultdict

def extract_callback_patterns(file_content: str) -> List[Dict]:
    """Extract all callback definitions and their Input/Output/State patterns"""
    callbacks = []
    
    # Find all @app.callback blocks
    callback_pattern = r'@app\.callback\((.*?)\ndef\s+(\w+)'
    matches = re.finditer(callback_pattern, file_content, re.DOTALL)
    
    for match in matches:
        callback_def = match.group(1)
        function_name = match.group(2)
        
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
            'raw_definition': callback_def
        })
    
    return callbacks

def extract_component_ids(file_content: str) -> Dict[str, List[str]]:
    """Extract all component IDs from the layout"""
    components = defaultdict(list)
    
    # Find all id="..." patterns
    id_pattern = r'id\s*=\s*["\']([^"\']+)["\']'
    matches = re.finditer(id_pattern, file_content)
    
    for match in matches:
        component_id = match.group(1)
        # Find the line number for context
        line_num = file_content[:match.start()].count('\n') + 1
        components[component_id].append(line_num)
    
    return dict(components)

def find_conditional_components(file_content: str) -> Dict[str, str]:
    """Find components that exist only in conditional layouts (tabs, etc.)"""
    conditional_components = {}
    
    # Find function definitions that create UI components
    function_pattern = r'def\s+(create_\w+)\s*\([^)]*\):'
    matches = re.finditer(function_pattern, file_content)
    
    for match in matches:
        func_name = match.group(1)
        # Find the function body
        func_start = match.end()
        # Simple heuristic: find next function or end of file
        next_func = re.search(r'\ndef\s+\w+', file_content[func_start:])
        if next_func:
            func_end = func_start + next_func.start()
        else:
            func_end = len(file_content)
        
        func_body = file_content[func_start:func_end]
        
        # Find IDs in this function
        id_pattern = r'id\s*=\s*["\']([^"\']+)["\']'
        ids_in_func = re.findall(id_pattern, func_body)
        
        for component_id in ids_in_func:
            conditional_components[component_id] = func_name
    
    return conditional_components

def analyze_callback_issues(file_path: str) -> Dict:
    """Perform comprehensive analysis of callback reference issues"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract data
    callbacks = extract_callback_patterns(content)
    layout_components = extract_component_ids(content)
    conditional_components = find_conditional_components(content)
    
    # Analysis results
    issues = {
        'missing_components': [],
        'suppressed_components': [],
        'orphaned_components': [],
        'callback_summary': [],
        'conditional_summary': {}
    }
    
    # Track all referenced IDs
    referenced_ids = set()
    
    # Analyze each callback
    for callback in callbacks:
        callback_info = {
            'function': callback['function_name'],
            'outputs': callback['outputs'],
            'inputs': callback['inputs'], 
            'states': callback['states'],
            'issues': []
        }
        
        # Check all references (inputs, outputs, states)
        all_refs = callback['outputs'] + callback['inputs'] + callback['states']
        
        for component_id, prop in all_refs:
            referenced_ids.add(component_id)
            
            if component_id not in layout_components:
                # Check if it's a conditional component
                if component_id in conditional_components:
                    callback_info['issues'].append(f"SUPPRESSED: {component_id} (in {conditional_components[component_id]})")
                    issues['suppressed_components'].append({
                        'id': component_id,
                        'callback': callback['function_name'],
                        'property': prop,
                        'defined_in': conditional_components[component_id]
                    })
                else:
                    callback_info['issues'].append(f"MISSING: {component_id}")
                    issues['missing_components'].append({
                        'id': component_id,
                        'callback': callback['function_name'],
                        'property': prop
                    })
        
        issues['callback_summary'].append(callback_info)
    
    # Find orphaned components
    for component_id in layout_components:
        if component_id not in referenced_ids:
            issues['orphaned_components'].append({
                'id': component_id,
                'lines': layout_components[component_id]
            })
    
    # Conditional components summary
    issues['conditional_summary'] = conditional_components
    
    return issues

def print_analysis_report(issues: Dict):
    """Print a comprehensive analysis report"""
    
    print("=" * 80)
    print("DASH CALLBACK REFERENCE ANALYSIS REPORT")
    print("=" * 80)
    
    # Missing Components
    if issues['missing_components']:
        print("\n🚨 MISSING COMPONENTS (Critical Issues):")
        print("-" * 50)
        for item in issues['missing_components']:
            print(f"  ❌ ID: '{item['id']}' (property: {item['property']})")
            print(f"     Referenced in callback: {item['callback']}")
    else:
        print("\n✅ No missing components found!")
    
    # Suppressed Components  
    if issues['suppressed_components']:
        print(f"\n⚠️  SUPPRESSED COMPONENTS ({len(issues['suppressed_components'])} found):")
        print("-" * 50)
        for item in issues['suppressed_components']:
            print(f"  🔶 ID: '{item['id']}' (property: {item['property']})")
            print(f"     Referenced in callback: {item['callback']}")
            print(f"     Defined in function: {item['defined_in']}")
            print(f"     ➤ This may cause runtime errors if component is not always rendered")
    else:
        print("\n✅ No suppressed component issues found!")
    
    # Orphaned Components
    if issues['orphaned_components']:
        print(f"\n📋 ORPHANED COMPONENTS ({len(issues['orphaned_components'])} found):")
        print("-" * 50)
        print("  Components that exist in layout but are not used in any callbacks:")
        for item in issues['orphaned_components']:
            lines_str = ', '.join(map(str, item['lines']))
            print(f"  🔹 ID: '{item['id']}' (lines: {lines_str})")
    
    # Callback Summary
    print(f"\n📊 CALLBACK SUMMARY ({len(issues['callback_summary'])} callbacks):")
    print("-" * 50)
    for callback in issues['callback_summary']:
        status = "❌ HAS ISSUES" if callback['issues'] else "✅ OK"
        print(f"  {status} {callback['function']}:")
        print(f"    Outputs: {len(callback['outputs'])}, Inputs: {len(callback['inputs'])}, States: {len(callback['states'])}")
        if callback['issues']:
            for issue in callback['issues']:
                print(f"    ⚠️  {issue}")
    
    # Conditional Components
    if issues['conditional_summary']:
        print(f"\n🔄 CONDITIONAL COMPONENTS ({len(issues['conditional_summary'])} found):")
        print("-" * 50)
        funcs = defaultdict(list)
        for comp_id, func_name in issues['conditional_summary'].items():
            funcs[func_name].append(comp_id)
        
        for func_name, comp_ids in funcs.items():
            print(f"  📁 {func_name}: {len(comp_ids)} components")
            for comp_id in sorted(comp_ids):
                print(f"    - {comp_id}")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    
    if issues['missing_components']:
        print("1. 🚨 CRITICAL: Add missing components to your layout or remove references")
    
    if issues['suppressed_components']:
        print("2. ⚠️  IMPORTANT: For suppressed components, consider:")
        print("   - Use suppress_callback_exceptions=True (already done)")
        print("   - Ensure components are always rendered in some form")
        print("   - Add conditional logic in callbacks to handle missing components")
    
    if issues['orphaned_components']:
        print("3. 📋 CLEANUP: Consider removing orphaned components or adding callbacks")
    
    if not any([issues['missing_components'], issues['suppressed_components']]):
        print("🎉 Your callback references look good!")

if __name__ == "__main__":
    # Analyze the main dash app
    file_path = "dash_app.py"
    
    try:
        issues = analyze_callback_issues(file_path)
        print_analysis_report(issues)
        
        # Save detailed report to file
        import json
        with open("callback_analysis_report.json", "w") as f:
            json.dump(issues, f, indent=2)
        print(f"\n📄 Detailed report saved to: callback_analysis_report.json")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found")
    except Exception as e:
        print(f"❌ Error analyzing file: {e}") 