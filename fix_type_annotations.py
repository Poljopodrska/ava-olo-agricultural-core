#!/usr/bin/env python3
"""
Fix type annotations for Python 3.8 compatibility
App Runner uses Python 3.8, which doesn't support lowercase generic types
"""

import os
import re
import sys

def fix_file(filepath):
    """Fix type annotations in a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Replace lowercase generic types with uppercase from typing module
    patterns = [
        (r'\bdict\[', 'Dict['),
        (r'\blist\[', 'List['),
        (r'\btuple\[', 'Tuple['),
        (r'\bset\[', 'Set['),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Check if we need to add imports
    if content != original:
        # Check if typing imports exist
        if 'from typing import' in content:
            # Add missing imports
            typing_line = None
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from typing import'):
                    typing_line = i
                    break
            
            if typing_line is not None:
                # Parse existing imports
                import_match = re.match(r'from typing import (.+)', lines[typing_line])
                if import_match:
                    imports = [imp.strip() for imp in import_match.group(1).split(',')]
                    
                    # Add missing imports
                    needed = []
                    if 'Dict[' in content and 'Dict' not in imports:
                        needed.append('Dict')
                    if 'List[' in content and 'List' not in imports:
                        needed.append('List')
                    if 'Tuple[' in content and 'Tuple' not in imports:
                        needed.append('Tuple')
                    if 'Set[' in content and 'Set' not in imports:
                        needed.append('Set')
                    
                    if needed:
                        imports.extend(needed)
                        lines[typing_line] = f"from typing import {', '.join(sorted(imports))}"
                        content = '\n'.join(lines)
        
        # Write back
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed {filepath}")
        return True
    
    return False

# Fix all CAVA files
files_to_check = [
    'implementation/cava/cava_central_service.py',
    'implementation/cava/universal_conversation_engine.py',
    'implementation/cava/database_connections.py',
    'implementation/cava/llm_query_generator.py',
    'implementation/cava/error_handling.py',
    'implementation/cava/performance_optimization.py',
    'implementation/cava/cava_registration_handler.py',
    'api/cava_routes.py'
]

fixed_count = 0
for filepath in files_to_check:
    if os.path.exists(filepath):
        if fix_file(filepath):
            fixed_count += 1

print(f"\n🔧 Fixed {fixed_count} files for Python 3.8 compatibility")