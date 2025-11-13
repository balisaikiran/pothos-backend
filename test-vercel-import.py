#!/usr/bin/env python3
"""
Test script to simulate Vercel's import behavior
Run this locally to see if there are any import-time errors
"""
import sys
import traceback

print("=" * 60)
print("Testing Vercel Import Simulation")
print("=" * 60)

try:
    print("\n1. Testing basic imports...")
    import sys
    import os
    import traceback
    from pathlib import Path
    print("   ✅ Basic imports OK")
    
    print("\n2. Testing FastAPI/Mangum imports...")
    from fastapi import FastAPI
    from mangum import Mangum
    print("   ✅ FastAPI/Mangum imports OK")
    
    print("\n3. Testing api/index.py import...")
    # Add api directory to path
    import sys
    from pathlib import Path
    api_dir = Path(__file__).parent / "api"
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))
    
    # Try to import index module
    import importlib.util
    index_file = api_dir / "index.py"
    spec = importlib.util.spec_from_file_location("index", index_file)
    if spec and spec.loader:
        print(f"   📁 Loading {index_file}...")
        index_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(index_module)
        print("   ✅ Module executed successfully")
        
        if hasattr(index_module, 'handler'):
            handler = index_module.handler
            print(f"   ✅ Handler exists: {type(handler)}")
            
            if handler is None:
                print("   ❌ ERROR: Handler is None!")
                sys.exit(1)
            else:
                print("   ✅ Handler is not None - SUCCESS!")
        else:
            print("   ❌ ERROR: Module has no 'handler' attribute!")
            sys.exit(1)
    else:
        print("   ❌ ERROR: Failed to create module spec")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Import should work on Vercel.")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    print("\nTraceback:")
    print(traceback.format_exc())
    sys.exit(1)

