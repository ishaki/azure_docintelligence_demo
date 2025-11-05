"""
Validation script to check all project files for errors.
"""
import ast
import sys
from pathlib import Path


def validate_python_file(file_path: Path) -> tuple[bool, str]:
    """
    Validate a Python file for syntax errors.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def validate_html_file(file_path: Path) -> tuple[bool, str]:
    """
    Basic HTML validation - check for closing tags and structure.
    
    Args:
        file_path: Path to the HTML file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic checks
        if '<html' not in content.lower():
            return False, "Missing <html> tag"
        if '<head' not in content.lower():
            return False, "Missing <head> tag"
        if '<body' not in content.lower():
            return False, "Missing <body> tag"
        
        return True, ""
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def validate_javascript_file(file_path: Path) -> tuple[bool, str]:
    """
    Basic JavaScript validation - check for common syntax issues.
    
    Args:
        file_path: Path to the JavaScript file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic checks
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            return False, f"Mismatched braces: {open_braces} opening, {close_braces} closing"
        
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            return False, f"Mismatched parentheses: {open_parens} opening, {close_parens} closing"
        
        return True, ""
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def main():
    """Main validation function."""
    project_root = Path(__file__).parent
    errors = []
    warnings = []
    
    print("=" * 60)
    print("Validating Project Files")
    print("=" * 60)
    print()
    
    # Validate Python files
    python_files = [
        project_root / "main.py",
        project_root / "run.py",
    ]
    
    print("Validating Python files...")
    for py_file in python_files:
        if py_file.exists():
            is_valid, error_msg = validate_python_file(py_file)
            if is_valid:
                print(f"  [OK] {py_file.name}")
            else:
                print(f"  [ERROR] {py_file.name}: {error_msg}")
                errors.append(f"{py_file.name}: {error_msg}")
        else:
            print(f"  [WARN] {py_file.name}: File not found")
            warnings.append(f"{py_file.name}: File not found")
    
    print()
    
    # Validate HTML files
    html_files = [
        project_root / "static" / "index.html",
    ]
    
    print("Validating HTML files...")
    for html_file in html_files:
        if html_file.exists():
            is_valid, error_msg = validate_html_file(html_file)
            if is_valid:
                print(f"  [OK] {html_file.name}")
            else:
                print(f"  [ERROR] {html_file.name}: {error_msg}")
                errors.append(f"{html_file.name}: {error_msg}")
        else:
            print(f"  [WARN] {html_file.name}: File not found")
            warnings.append(f"{html_file.name}: File not found")
    
    print()
    
    # Validate JavaScript files
    js_files = [
        project_root / "static" / "script.js",
    ]
    
    print("Validating JavaScript files...")
    for js_file in js_files:
        if js_file.exists():
            is_valid, error_msg = validate_javascript_file(js_file)
            if is_valid:
                print(f"  [OK] {js_file.name}")
            else:
                print(f"  [ERROR] {js_file.name}: {error_msg}")
                errors.append(f"{js_file.name}: {error_msg}")
        else:
            print(f"  [WARN] {js_file.name}: File not found")
            warnings.append(f"{js_file.name}: File not found")
    
    print()
    print("=" * 60)
    
    if errors:
        print(f"[FAILED] Validation failed with {len(errors)} error(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    elif warnings:
        print(f"[WARNING] Validation completed with {len(warnings)} warning(s)")
        for warning in warnings:
            print(f"  - {warning}")
        return 0
    else:
        print("[SUCCESS] All files validated successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

