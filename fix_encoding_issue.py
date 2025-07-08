#!/usr/bin/env python3
"""
Fix character encoding issues in floater core file.
"""

import os
import sys

def fix_encoding_issue():
    """Fix character encoding issues in floater core file."""
    file_path = 'simulation/components/floater/core.py'
    
    try:
        # Try to read with different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Successfully read file with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            # If all encodings fail, read as bytes and decode with error handling
            with open(file_path, 'rb') as f:
                raw_content = f.read()
            content = raw_content.decode('utf-8', errors='replace')
            print("Read file with error handling (replacing invalid characters)")
        
        # Write back with UTF-8 encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Successfully fixed encoding for {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing encoding: {e}")
        return False

if __name__ == "__main__":
    success = fix_encoding_issue()
    sys.exit(0 if success else 1) 