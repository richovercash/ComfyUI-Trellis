#!/usr/bin/env python3
"""
Packaging script for ComfyUI-Trellis extension
"""

import os
import sys
import shutil
import subprocess
import zipfile
import argparse
from datetime import datetime

# Version info
VERSION = "0.1.0"
NAME = "ComfyUI-Trellis"
AUTHOR = "Your Name"
DESCRIPTION = "Trellis 3D model generation integration for ComfyUI"

# File paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")

# Files to include in the package
INCLUDE_FILES = [
    "comfyui_trellis_node.py",
    "trellis_advanced_nodes.py",
    "trellis_viewer_node.py",
    "trellis_utils.py",
    "trellis_config.py",
    "__init__.py",
    "README.md",
    "config.json",
]

# Directories to include in the package
INCLUDE_DIRS = [
    "examples",
]

# Files to exclude even if in an included directory
EXCLUDE_FILES = [
    ".DS_Store",
    "Thumbs.db",
    "*.pyc",
    "__pycache__",
]

def clean_build_dir():
    """Clean build directory"""
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

def clean_dist_dir():
    """Clean dist directory"""
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR)

def copy_files():
    """Copy files to build directory"""
    # Copy individual files
    for file in INCLUDE_FILES:
        src_path = os.path.join(SCRIPT_DIR, file)
        if os.path.exists(src_path):
            dst_path = os.path.join(BUILD_DIR, file)
            # Create destination directory if needed
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"Copied: {file}")
        else:
            print(f"Warning: File not found: {file}")
    
    # Copy directories
    for directory in INCLUDE_DIRS:
        src_dir = os.path.join(SCRIPT_DIR, directory)
        if os.path.exists(src_dir) and os.path.isdir(src_dir):
            dst_dir = os.path.join(BUILD_DIR, directory)
            shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns(*EXCLUDE_FILES))
            print(f"Copied directory: {directory}")
        else:
            print(f"Warning: Directory not found: {directory}")

def create_package(version=None):
    """Create zip package"""
    if version is None:
        # Use current date and time as version if not specified
        version = datetime.now().strftime("%Y%m%d%H%M")
    
    # Create zip file
    zip_filename = f"{NAME}-{version}.zip"
    zip_path = os.path.join(DIST_DIR, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Zip all files in the build directory
        for root, _, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, BUILD_DIR)
                zipf.write(file_path, os.path.join(NAME, rel_path))
    
    print(f"Created package: {zip_path}")
    return zip_path

def create_wheel():
    """Create wheel package using setuptools"""
    # Create temporary setup.py
    setup_py = os.path.join(BUILD_DIR, "setup.py")
    with open(setup_py, 'w') as f:
        f.write(f'''
from setuptools import setup, find_packages

setup(
    name="{NAME.lower().replace('-', '_')}",
    version="{VERSION}",
    description="{DESCRIPTION}",
    author="{AUTHOR}",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/{NAME}",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "websockets>=10.0",
        "aiohttp>=3.8.0",
        "pillow>=9.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
''')
    
    # Create MANIFEST.in
    manifest_in = os.path.join(BUILD_DIR, "MANIFEST.in")
    with open(manifest_in, 'w') as f:
        f.write('''
include README.md
include config.json
recursive-include examples *
''')
    
    # Run setup.py to build wheel
    cwd = os.getcwd()
    os.chdir(BUILD_DIR)
    try:
        subprocess.run([sys.executable, 'setup.py', 'bdist_wheel'], check=True)
        # Copy wheel to dist directory
        wheel_dir = os.path.join(BUILD_DIR, 'dist')
        if os.path.exists(wheel_dir):
            for file in os.listdir(wheel_dir):
                if file.endswith('.whl'):
                    src_path = os.path.join(wheel_dir, file)
                    dst_path = os.path.join(DIST_DIR, file)
                    shutil.copy2(src_path, dst_path)
                    print(f"Created wheel: {dst_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating wheel: {e}")
    finally:
        os.chdir(cwd)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Package ComfyUI-Trellis extension")
    parser.add_argument('--version', help='Package version')
    parser.add_argument('--wheel', action='store_true', help='Create wheel package')
    parser.add_argument('--clean', action='store_true', help='Clean build and dist directories')
    
    args = parser.parse_args()
    
    # Clean directories if requested
    if args.clean:
        clean_build_dir()
        clean_dist_dir()
        print("Cleaned build and dist directories")
        return
    
    # Always clean build directory
    clean_build_dir()
    
    # Create dist directory if it doesn't exist
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
    
    # Copy files to build directory
    copy_files()
    
    # Create packages
    create_package(args.version or VERSION)
    
    # Create wheel if requested
    if args.wheel:
        create_wheel()
    
    print("Packaging complete!")

if __name__ == "__main__":
    main()
