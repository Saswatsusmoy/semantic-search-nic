"""
Version compatibility checker for the NIC Semantic Search application
"""

import pkg_resources
import sys
import platform

def check_versions():
    """Check compatibility of critical packages and Python version"""
    print("System Version Information:")
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    
    # Required packages with their minimum versions
    required_packages = {
        'faiss-cpu': '1.7.0',  # Or faiss-gpu
        'flask': '2.0.0',
        'pymongo': '3.12.0',
        'sentence-transformers': '2.0.0',
        'numpy': '1.19.0',
        'torch': '1.7.0'
    }
    
    # Check installed packages
    installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    
    print("\nPackage Version Check:")
    all_compatible = True
    
    for package, min_version in required_packages.items():
        if package in installed_packages:
            installed_version = installed_packages[package]
            is_compatible = pkg_resources.parse_version(installed_version) >= pkg_resources.parse_version(min_version)
            
            status = "✓" if is_compatible else "✗"
            compatibility = "Compatible" if is_compatible else "Not compatible"
            
            print(f"{status} {package}: {installed_version} (required: >={min_version}) - {compatibility}")
            
            if not is_compatible:
                all_compatible = False
        else:
            print(f"✗ {package}: Not installed (required: >={min_version})")
            all_compatible = False
    
    # Python version check
    min_python = (3, 7)
    current_python = sys.version_info[:2]
    python_compatible = current_python >= min_python
    
    if not python_compatible:
        print(f"\n✗ Python version {'.'.join(map(str, current_python))} is not compatible. "
              f"Minimum required: {'.'.join(map(str, min_python))}")
        all_compatible = False
    
    # Summary
    print("\nOverall compatibility:", "✓ Compatible" if all_compatible else "✗ Not fully compatible")
    
    return all_compatible

if __name__ == "__main__":
    check_versions()
