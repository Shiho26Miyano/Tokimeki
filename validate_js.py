#!/usr/bin/env python3
"""
Simple JavaScript syntax validator using Python
"""
import re
import sys

def validate_js_syntax(content):
    """Basic JavaScript syntax validation"""
    issues = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for common syntax issues
        
        # Unmatched quotes
        single_quotes = line.count("'") - line.count("\\'")
        double_quotes = line.count('"') - line.count('\\"')
        backticks = line.count('`') - line.count('\\`')
        
        if single_quotes % 2 != 0:
            issues.append(f"Line {i}: Unmatched single quote")
        if double_quotes % 2 != 0:
            issues.append(f"Line {i}: Unmatched double quote")
        if backticks % 2 != 0:
            issues.append(f"Line {i}: Unmatched backtick")
            
        # Check for template literal issues
        if '${' in line and '`' not in line:
            issues.append(f"Line {i}: Template literal syntax without backticks")
            
        # Check for broken template literals across lines
        if line.strip().endswith('${') and not line.strip().endswith('}`'):
            issues.append(f"Line {i}: Potentially broken template literal")
            
        # Check for missing semicolons in critical places
        if re.search(r'}\s*$', line.strip()) and i < len(lines) and not lines[i].strip().startswith((')', '}', ']', ',', ';')):
            if not re.search(r'(if|else|for|while|function|class)\s*\{', line):
                issues.append(f"Line {i}: Possible missing semicolon after block")
    
    return issues

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_js.py <js_file>")
        sys.exit(1)
    
    filename = sys.argv[1]
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = validate_js_syntax(content)
        
        if issues:
            print(f"Found {len(issues)} potential syntax issues in {filename}:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"No obvious syntax issues found in {filename}")
            
    except FileNotFoundError:
        print(f"File not found: {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
