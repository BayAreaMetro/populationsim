#!/usr/bin/env python3
"""
Quick script to remove emoji characters from check_controls_2_seed.py
that are causing Unicode encoding issues on Windows
"""

def fix_unicode_file():
    """Remove emoji characters from the validation script"""
    
    file_path = "check_controls_2_seed.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace emoji characters with text equivalents
    replacements = {
        '🔧': '[CONFIG]',
        '🚀': '[QUICK]',
        '⚠️ ': '[WARNING] ',
        '⚠️': '[WARNING]',
        '✅': '[SUCCESS]',
        '❌': '[ERROR]',
        '🎯': '[TARGET]',
        '\U0001f3af': '[TARGET]',  # target emoji
        '🔍': '[SEARCH]',
        '📊': '[STATS]',
        '🚨': '[CRITICAL]',
        '📁': '[DATA]',
        '⚡': '[QUICK]'
    }
    
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)
    
    # Write back with UTF-8 encoding
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed Unicode characters in {file_path}")

if __name__ == "__main__":
    fix_unicode_file()
