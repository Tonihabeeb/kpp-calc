#!/usr/bin/env python3
"""
Ultra-simple Flask test - just try to import and create basic app
"""
try:
    print("Step 1: Importing Flask...")
    from flask import Flask
    
    print("Step 2: Creating Flask app...")
    app = Flask(__name__)
    
    print("Step 3: Adding test route...")
    @app.route('/')
    def hello():
        return "KPP Simulator is working!"
    
    print("Step 4: Starting server...")
    app.run(debug=True, host='127.0.0.1', port=5000)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
