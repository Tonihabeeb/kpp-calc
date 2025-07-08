#!/usr/bin/env python3
"""
Fix character encoding issues in floater core file.
"""

import os
import sys

def fix_floater_encoding():
    """Fix character encoding issues in floater core file."""
    file_path = 'simulation/components/floater/core.py'
    
    try:
        # Read the file as bytes first
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        print(f"Original file size: {len(raw_content)} bytes")
        
        # Try to decode with different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = None
        
        for encoding in encodings:
            try:
                content = raw_content.decode(encoding)
                print(f"Successfully decoded with {encoding}")
                break
            except UnicodeDecodeError as e:
                print(f"Failed to decode with {encoding}: {e}")
                continue
        
        if content is None:
            # If all encodings fail, use error handling
            content = raw_content.decode('utf-8', errors='replace')
            print("Used error handling (replacing invalid characters)")
        
        # Replace problematic Unicode characters with ASCII equivalents
        replacements = {
            'ρ': 'rho',  # Greek rho
            '×': 'x',    # Multiplication sign
            '°': 'deg',  # Degree sign
            '±': '+/-',  # Plus-minus sign
            '≤': '<=',   # Less than or equal
            '≥': '>=',   # Greater than or equal
            '≠': '!=',   # Not equal
            '≈': '~',    # Approximately equal
            '∞': 'inf',  # Infinity
            'π': 'pi',   # Pi
            'Δ': 'Delta', # Delta
            'θ': 'theta', # Theta
            'α': 'alpha', # Alpha
            'β': 'beta',  # Beta
            'γ': 'gamma', # Gamma
            'δ': 'delta', # Delta
            'ε': 'epsilon', # Epsilon
            'μ': 'mu',   # Mu
            'σ': 'sigma', # Sigma
            'τ': 'tau',  # Tau
            'φ': 'phi',  # Phi
            'ω': 'omega', # Omega
        }
        
        for unicode_char, ascii_replacement in replacements.items():
            content = content.replace(unicode_char, ascii_replacement)
        
        # Write back with UTF-8 encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Successfully fixed encoding for {file_path}")
        print(f"Final file size: {len(content)} characters")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing encoding: {e}")
        return False

if __name__ == "__main__":
    success = fix_floater_encoding()
    sys.exit(0 if success else 1) 