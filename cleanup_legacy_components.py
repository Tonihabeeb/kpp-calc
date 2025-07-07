import shutil
import os
from pathlib import Path
#!/usr/bin/env python3
"""
Cleanup script to remove legacy component files and update remaining references.
This script will:
1. Remove legacy component files that are no longer needed
2. Update any remaining references to use integrated components
3. Clean up backup files created during migration
"""

