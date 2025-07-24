#!/usr/bin/env python3
"""
Quick test script to verify both versions work properly.
Run this after setup to ensure everything is configured correctly.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import requests
        print("✅ requests")
    except ImportError:
        print("❌ requests - run: pip install requests")
        return False
    
    try:
        import selenium
        print("✅ selenium")
    except ImportError:
        print("❌ selenium - run: pip install selenium")
        return False
    
    try:
        import genanki
        print("✅ genanki")
    except ImportError:
        print("❌ genanki - run: pip install genanki")
        return False
    
    try:
        import tqdm
        print("✅ tqdm")
    except ImportError:
        print("❌ tqdm - run: pip install tqdm")
        return False
    
    try:
        import PIL
        print("✅ Pillow (PIL)")
    except ImportError:
        print("❌ Pillow - run: pip install Pillow")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv - run: pip install python-dotenv")
        return False
    
    return True

def test_gui_support():
    """Test GUI support"""
    print("\n🖥️ Testing GUI support...")
    try:
        import tkinter
        print("✅ tkinter available - GUI file dialogs will work")
        return True
    except ImportError:
        print("⚠️  tkinter not available - will use command line prompts")
        return False

def test_modular_files():
    """Test that modular files exist"""
    print("\n📁 Testing modular files...")
    
    required_files = [
        "main.py",
        "utils.py", 
        "auth.py",
        "image_processing.py",
        "content_extraction.py",
        "sequential_extraction.py",
        "deck_scraping.py",
        "anki_export.py"
    ]
    
    all_present = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - missing!")
            all_present = False
    
    return all_present

def test_debug_file():
    """Test that debug file exists"""
    print("\n🔧 Testing debug file...")
    if os.path.exists("export_ucalgary_anki_debug.py"):
        print("✅ export_ucalgary_anki_debug.py")
        return True
    else:
        print("❌ export_ucalgary_anki_debug.py - missing!")
        return False

def main():
    print("🚀 UCalgary Anki Converter - System Test")
    print("=" * 50)
    
    imports_ok = test_imports()
    gui_ok = test_gui_support()
    modular_ok = test_modular_files()
    debug_ok = test_debug_file()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    if imports_ok and modular_ok:
        print("✅ Modular version ready!")
        print("   Run: python main.py")
    else:
        print("❌ Modular version has issues")
    
    if debug_ok and imports_ok:
        print("✅ Debug version ready!")
        print("   Run: python export_ucalgary_anki_debug.py")
    else:
        print("❌ Debug version has issues")
    
    if gui_ok:
        print("✅ GUI file dialogs available")
    else:
        print("⚠️  Using command line prompts")
    
    if imports_ok and (modular_ok or debug_ok):
        print("\n🎉 System is ready! Choose your preferred version and run it.")
    else:
        print("\n❌ System has issues. Run setup.sh to fix dependencies.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
