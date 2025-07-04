#!/usr/bin/env python3
"""
KPP Simulator Endpoint Deep Inspection - Simple Version
Analyzes all endpoints and callbacks from the mapping report
"""

import json

def analyze_endpoints_simple():
    """Analyze and list all endpoints and callbacks"""
    
    # Read the latest report
    report_file = "endpoint_mapping_report_20250703_215846.json"
    
    with open(report_file, 'r') as f:
        data = json.load(f)
    
    print("="*80)
    print("KPP SIMULATOR ENDPOINT DEEP INSPECTION")
    print("="*80)
    print(f"TOTAL ENDPOINTS: {data['summary']['total_extracted_endpoints']}")
    print(f"TEST COVERAGE: {data['summary']['coverage_percentage']}%")
    print()
    
    # Flask Backend Routes Analysis
    flask_routes = data['endpoint_categories']['flask_routes']['endpoints_list']
    flask_get = [ep for ep in flask_routes if ep.startswith('GET')]
    flask_post = [ep for ep in flask_routes if ep.startswith('POST')]
    
    print("FLASK BACKEND ROUTES (48 total):")
    print(f"  GET routes: {len(flask_get)}")
    print(f"  POST routes: {len(flask_post)}")
    print()
    
    # WebSocket Routes Analysis
    websocket_routes = data['endpoint_categories']['websocket_routes']['endpoints_list']
    print("WEBSOCKET ROUTES (3 total):")
    for i, ep in enumerate(websocket_routes, 1):
        print(f"  {i}. {ep}")
    print()
    
    # Dash Callbacks Analysis
    dash_endpoints = data['endpoint_categories']['dash_callbacks']['endpoints_list']
    dash_callbacks = [ep for ep in dash_endpoints if ep.startswith('CALLBACK')]
    dash_components = [ep for ep in dash_endpoints if ep.startswith('COMPONENT')]
    
    print("DASH APPLICATION (106 total interactions):")
    print(f"  Actual callbacks: {len(dash_callbacks)}")
    print(f"  Component interactions: {len(dash_components)}")
    print()
    
    print("Dash Callbacks (Function Definitions):")
    for i, callback in enumerate(sorted(dash_callbacks), 1):
        callback_name = callback.replace('CALLBACK ', '')
        print(f"  {i:2d}. {callback_name}")
    print()
    
    # Observability Routes Analysis
    obs_routes = data['endpoint_categories']['observability_routes']['endpoints_list']
    print("OBSERVABILITY ROUTES (3 total):")
    for i, ep in enumerate(obs_routes, 1):
        print(f"  {i}. {ep}")
    print()
    
    # Summary Statistics
    print("="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"Backend Routes:           {len(flask_routes):3d}")
    print(f"  - GET:                 {len(flask_get):3d}")
    print(f"  - POST:                {len(flask_post):3d}")
    print(f"WebSocket Routes:         {len(websocket_routes):3d}")
    print(f"Dash Interactions:        {len(dash_endpoints):3d}")
    print(f"  - Callbacks:           {len(dash_callbacks):3d}")
    print(f"  - Components:          {len(dash_components):3d}")
    print(f"Observability Routes:     {len(obs_routes):3d}")
    print(f"Total Endpoints:          {data['summary']['total_extracted_endpoints']:3d}")
    print("="*80)
    
    # Detailed breakdown for reference
    print("\nDETAILED BREAKDOWN:")
    print("-" * 40)
    
    print("Flask GET Endpoints:")
    for i, ep in enumerate(sorted(flask_get), 1):
        print(f"  {i:2d}. {ep}")
    
    print("\nFlask POST Endpoints:")
    for i, ep in enumerate(sorted(flask_post), 1):
        print(f"  {i:2d}. {ep}")
    
    print(f"\nDash Component Categories:")
    print(f"Data Stores: {len([c for c in dash_components if 'store' in c and 'data' in c])}")
    print(f"Control Buttons: {len([c for c in dash_components if 'btn' in c and not 'show' in c])}")
    print(f"Parameter Sliders: {len([c for c in dash_components if 'slider' in c])}")
    print(f"Error Components: {len([c for c in dash_components if 'error' in c])}")
    print(f"Display Values: {len([c for c in dash_components if any(w in c for w in ['value', 'children', 'status', 'power', 'torque', 'efficiency'])])}")
    print(f"Charts: {len([c for c in dash_components if 'chart' in c])}")
    print(f"Other Components: {len(dash_components) - sum([len([c for c in dash_components if 'store' in c and 'data' in c]), len([c for c in dash_components if 'btn' in c]), len([c for c in dash_components if 'slider' in c]), len([c for c in dash_components if 'error' in c]), len([c for c in dash_components if 'chart' in c])])}")

if __name__ == "__main__":
    analyze_endpoints_simple() 