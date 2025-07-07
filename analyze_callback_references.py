import re
import ast
from typing import Dict, List, Set, Tuple
from collections import defaultdict
        import json
#!/usr/bin/env python3
"""
Deep analysis script to find callback reference issues in Dash apps.
Checks for:
1. Non-existent component IDs referenced in callbacks
2. Components that might only exist in conditional layouts (suppressed)
3. Mismatched Input/Output/State references
4. Orphaned components (exist in layout but not used in callbacks)
"""

