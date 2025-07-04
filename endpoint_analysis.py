#!/usr/bin/env python3
"""
KPP Simulator Endpoint Deep Inspection
Analyzes all endpoints and callbacks from the mapping report
"""

import json
from pathlib import Path

def analyze_endpoints():
    """Analyze and list all endpoints and callbacks"""
    
    # Read the latest report
    report_file = "endpoint_mapping_report_20250703_215846.json"
    
    with open(report_file, 'r') as f:
        data = json.load(f)
    
    print("="*60)
    print("🎯 KPP SIMULATOR ENDPOINT DEEP INSPECTION")
    print("="*60)
    print(f"📊 TOTAL ENDPOINTS: {data['summary']['total_extracted_endpoints']}")
    print(f"🎯 TEST COVERAGE: {data['summary']['coverage_percentage']}%")
    print()
    
    # Flask Backend Routes Analysis
    flask_routes = data['endpoint_categories']['flask_routes']['endpoints_list']
    flask_get = [ep for ep in flask_routes if ep.startswith('GET')]
    flask_post = [ep for ep in flask_routes if ep.startswith('POST')]
    
    print("🔗 FLASK BACKEND ROUTES (48 total):")
    print(f"  📥 GET routes: {len(flask_get)}")
    print(f"  📤 POST routes: {len(flask_post)}")
    print()
    
    print("📥 Flask GET Endpoints:")
    for i, ep in enumerate(sorted(flask_get), 1):
        print(f"  {i:2d}. {ep}")
    print()
    
    print("📤 Flask POST Endpoints:")
    for i, ep in enumerate(sorted(flask_post), 1):
        print(f"  {i:2d}. {ep}")
    print()
    
    # WebSocket Routes Analysis
    websocket_routes = data['endpoint_categories']['websocket_routes']['endpoints_list']
    print("🌐 WEBSOCKET ROUTES (3 total):")
    for i, ep in enumerate(websocket_routes, 1):
        print(f"  {i}. {ep}")
    print()
    
    # Dash Callbacks Analysis
    dash_endpoints = data['endpoint_categories']['dash_callbacks']['endpoints_list']
    dash_callbacks = [ep for ep in dash_endpoints if ep.startswith('CALLBACK')]
    dash_components = [ep for ep in dash_endpoints if ep.startswith('COMPONENT')]
    
    print("🎯 DASH APPLICATION (106 total interactions):")
    print(f"  ⚡ Actual callbacks: {len(dash_callbacks)}")
    print(f"  🧩 Component interactions: {len(dash_components)}")
    print()
    
    print("⚡ Dash Callbacks (Function Definitions):")
    for i, callback in enumerate(sorted(dash_callbacks), 1):
        callback_name = callback.replace('CALLBACK ', '')
        print(f"  {i:2d}. {callback_name}")
    print()
    
    # Group components by category (prioritized matching)
    component_categories = {
        'Data Stores': [],
        'Control Buttons': [],
        'Display Buttons': [],
        'Parameter Sliders': [],
        'Display Values': [],
        'Charts': [],
        'Error Components': [],
        'Action Outputs': [],
        'Intervals': [],
        'Presets': [],
        'Switches': [],
        'Other Components': []
    }
    
    for comp in dash_components:
        comp_name = comp.replace('COMPONENT ', '')
        categorized = False
        
        # Prioritized categorization
        if 'store' in comp_name and 'data' in comp_name:
            component_categories['Data Stores'].append(comp_name)
            categorized = True
        elif 'error' in comp_name:
            component_categories['Error Components'].append(comp_name)
            categorized = True
        elif 'output-' in comp_name:
            component_categories['Action Outputs'].append(comp_name)
            categorized = True
        elif 'slider' in comp_name:
            component_categories['Parameter Sliders'].append(comp_name)
            categorized = True
        elif 'chart' in comp_name and 'figure' in comp_name:
            component_categories['Charts'].append(comp_name)
            categorized = True
        elif 'interval' in comp_name:
            component_categories['Intervals'].append(comp_name)
            categorized = True
        elif 'switch' in comp_name and 'enabled' in comp_name:
            component_categories['Switches'].append(comp_name)
            categorized = True
        elif 'preset' in comp_name or 'dropdown' in comp_name:
            component_categories['Presets'].append(comp_name)
            categorized = True
        elif ('btn' in comp_name or 'button' in comp_name) and 'show' in comp_name:
            component_categories['Display Buttons'].append(comp_name)
            categorized = True
        elif 'btn' in comp_name or 'button' in comp_name:
            component_categories['Control Buttons'].append(comp_name)
            categorized = True
        elif any(word in comp_name for word in ['value', 'children', 'status', 'power', 'torque', 'efficiency', 'rpm']):
            component_categories['Display Values'].append(comp_name)
            categorized = True
        
        if not categorized:
            component_categories['Other Components'].append(comp_name)
    
    print("🧩 Dash Component Interactions (by Category):")
    total_categorized = 0
    for category, components in component_categories.items():
        if components:
            print(f"\n  📂 {category} ({len(components)}):")
            for i, comp in enumerate(sorted(components), 1):
                print(f"    {i:2d}. {comp}")
            total_categorized += len(components)
    
    print(f"\n  📊 Total Components Categorized: {total_categorized} / {len(dash_components)}")
    
    # Quick verification - list all components for debugging
    if total_categorized != len(dash_components):
        print(f"\n  ⚠️  Missing {len(dash_components) - total_categorized} components")
    
    print()
    
    # Observability Routes Analysis
    obs_routes = data['endpoint_categories']['observability_routes']['endpoints_list']
    print("🔍 OBSERVABILITY ROUTES (3 total):")
    for i, ep in enumerate(obs_routes, 1):
        print(f"  {i}. {ep}")
    print()
    
    # Summary Statistics
    print("="*60)
    print("📈 SUMMARY STATISTICS")
    print("="*60)
    print(f"Backend Routes:           {len(flask_routes):3d}")
    print(f"  └─ GET:                {len(flask_get):3d}")
    print(f"  └─ POST:               {len(flask_post):3d}")
    print(f"WebSocket Routes:         {len(websocket_routes):3d}")
    print(f"Dash Interactions:        {len(dash_endpoints):3d}")
    print(f"  └─ Callbacks:          {len(dash_callbacks):3d}")
    print(f"  └─ Components:         {len(dash_components):3d}")
    print(f"Observability Routes:     {len(obs_routes):3d}")
    print(f"Total Endpoints:          {data['summary']['total_extracted_endpoints']:3d}")
    print("="*60)

if __name__ == "__main__":
    analyze_endpoints() 