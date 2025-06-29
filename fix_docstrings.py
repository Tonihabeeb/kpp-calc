#!/usr/bin/env python3
"""Fix malformed docstrings in engine.py"""


def fix_engine_docstrings():
    with open("simulation/engine.py", "r") as f:
        content = f.read()

    # Track changes
    original_count = content.count('"""')

    # Fix known malformed patterns
    fixes = [
        # Remove extra quotes from single-line docstrings
        (
            '"""Safely get nested dictionary values""""',
            '"""Safely get nested dictionary values"""',
        ),
        (
            '"""Get comprehensive transient event status""""',
            '"""Get comprehensive transient event status"""',
        ),
        (
            '"""Disable all enhanced physics effects (H1 and H2).""""""',
            '"""Disable all enhanced physics effects (H1 and H2)."""',
        ),
        # Remove any stray triple quotes
        ('""""', '"""'),
        ('""""""', '"""'),
    ]

    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"Fixed: {old[:50]}... -> {new[:50]}...")

    # Write back the file
    with open("simulation/engine.py", "w") as f:
        f.write(content)

    new_count = content.count('"""')
    print(f"Triple quotes: {original_count} -> {new_count}")
    print(f"Even (properly paired): {new_count % 2 == 0}")


if __name__ == "__main__":
    fix_engine_docstrings()
