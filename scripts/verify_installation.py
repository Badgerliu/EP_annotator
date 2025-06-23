#!/usr/bin/env python3
"""
Installation verification script for EP_annotator.

This script checks that all required dependencies are properly installed
and accessible.
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    min_version = (3, 7)
    
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= min_version:
        print("✅ Python version is compatible")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} is too old. "
              f"Minimum required: {min_version[0]}.{min_version[1]}")
        return False

def check_python_package(package_name, import_name=None):
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: not installed")
        return False

def check_system_tool(tool_name, version_flag="--version"):
    """Check if a system tool is available."""
    try:
        result = subprocess.run([tool_name, version_flag], 
                              capture_output=True, text=True, check=True)
        version_info = result.stdout.strip().split('\n')[0]
        print(f"✅ {tool_name}: {version_info}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ {tool_name}: not found")
        return False

def check_ep_annotator():
    """Check if EP_annotator is properly installed."""
    try:
        import ep_annotator
        version = getattr(ep_annotator, '__version__', 'unknown')
        print(f"✅ ep_annotator: {version}")
        return True
    except ImportError:
        print("❌ ep_annotator: not installed")
        print("   Please run: pip install -e .")
        return False

def main():
    """Main verification function."""
    print("EP_annotator Installation Verification")
    print("=" * 40)
    
    checks_passed = 0
    total_checks = 0
    
    # Check Python version
    print("\n1. Checking Python version...")
    total_checks += 1
    if check_python_version():
        checks_passed += 1
    
    # Check core Python packages
    print("\n2. Checking core Python packages...")
    core_packages = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('pybedtools', 'pybedtools'),
        ('intervaltree', 'intervaltree'),
        ('tqdm', 'tqdm'),
        ('PyYAML', 'yaml'),
    ]
    
    for package, import_name in core_packages:
        total_checks += 1
        if check_python_package(package, import_name):
            checks_passed += 1
    
    # Check visualization packages
    print("\n3. Checking visualization packages...")
    viz_packages = [
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
    ]
    
    for package, import_name in viz_packages:
        total_checks += 1
        if check_python_package(package, import_name):
            checks_passed += 1
    
    # Check system tools
    print("\n4. Checking system tools...")
    system_tools = [
        ('bedtools', '--version'),
        ('awk', '--version'),
        ('sort', '--version'),
        ('gzip', '--version'),
    ]
    
    for tool, flag in system_tools:
        total_checks += 1
        if check_system_tool(tool, flag):
            checks_passed += 1
    
    # Check EP_annotator installation
    print("\n5. Checking EP_annotator installation...")
    total_checks += 1
    if check_ep_annotator():
        checks_passed += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"Installation check complete: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 All dependencies are properly installed!")
        print("\nYou can now use EP_annotator. Try:")
        print("  python scripts/run_pipeline.py --help")
        return 0
    else:
        print(f"⚠️  {total_checks - checks_passed} dependencies are missing or incomplete.")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
        print("  # Install system tools (bedtools, etc.) using your package manager")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 