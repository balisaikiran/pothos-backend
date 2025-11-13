"""
Vercel Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes
"""
import sys
import os
import traceback
from pathlib import Path

# CRITICAL: Define handler at module level immediately
# This ensures Vercel always has a handler, even if imports fail
try:
    from fastapi import FastAPI
    from mangum import Mangum
    
    # Create minimal app first
    minimal_app = FastAPI()
    
    @minimal_app.get("/")
    async def root():
        return {
            "status": "initializing",
            "message": "Backend is loading..."
        }
    
    handler = Mangum(minimal_app, lifespan="off")
except Exception as e:
    # If even basic imports fail, we're in trouble
    # Print error and create absolute minimal handler
    print(f"CRITICAL: Failed to create minimal handler: {e}", file=sys.stderr, flush=True)
    print(traceback.format_exc(), file=sys.stderr, flush=True)
    handler = None

# Now try to load the real backend
if handler is not None:
    try:
        print("INFO: Starting backend initialization...", file=sys.stderr, flush=True)
        
        # Get paths
        current_file = Path(__file__).resolve()
        api_dir = current_file.parent
        project_root = api_dir.parent
        backend_dir = project_root / "backend"
        server_file = backend_dir / "server.py"
        
        print(f"INFO: Current file: {current_file}", file=sys.stderr, flush=True)
        print(f"INFO: Backend dir: {backend_dir}", file=sys.stderr, flush=True)
        print(f"INFO: Server file exists: {server_file.exists()}", file=sys.stderr, flush=True)
        
        # Add to path
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Try to import server
        app = None
        import_error = None
        
        if server_file.exists():
            try:
                print("INFO: Attempting to load server.py...", file=sys.stderr, flush=True)
                import importlib.util
                spec = importlib.util.spec_from_file_location("server", server_file)
                if spec and spec.loader:
                    server_module = importlib.util.module_from_spec(spec)
                    # Wrap exec_module to catch any errors during module execution
                    try:
                        spec.loader.exec_module(server_module)
                        print("INFO: Module executed successfully", file=sys.stderr, flush=True)
                    except Exception as exec_error:
                        print(f"ERROR: Error executing server module: {exec_error}", file=sys.stderr, flush=True)
                        print(traceback.format_exc(), file=sys.stderr, flush=True)
                        raise exec_error
                    
                    # Try to get app attribute
                    if hasattr(server_module, 'app'):
                        app = server_module.app
                        print("INFO: ✅ Successfully loaded server module and got app", file=sys.stderr, flush=True)
                    else:
                        raise AttributeError("server module has no 'app' attribute")
                else:
                    raise ImportError("Failed to create module spec")
            except Exception as e:
                print(f"ERROR: Failed to load via importlib: {e}", file=sys.stderr, flush=True)
                print(traceback.format_exc(), file=sys.stderr, flush=True)
                import_error = str(e)
                
                # Try direct import
                try:
                    print("INFO: Trying direct import...", file=sys.stderr, flush=True)
                    from server import app
                    print("INFO: ✅ Direct import succeeded", file=sys.stderr, flush=True)
                    import_error = None
                except Exception as e2:
                    print(f"ERROR: Direct import also failed: {e2}", file=sys.stderr, flush=True)
                    print(traceback.format_exc(), file=sys.stderr, flush=True)
                    import_error = f"{str(e)} | {str(e2)}"
        else:
            import_error = f"server.py not found at {server_file}"
            print(f"ERROR: {import_error}", file=sys.stderr, flush=True)
        
        # If we got the app, create new handler
        if app is not None:
            try:
                print("INFO: Creating Mangum handler with real app...", file=sys.stderr, flush=True)
                from mangum import Mangum
                handler = Mangum(app, lifespan="off")
                print("INFO: ✅ Handler created successfully", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"ERROR: Failed to create handler: {e}", file=sys.stderr, flush=True)
                print(traceback.format_exc(), file=sys.stderr, flush=True)
        else:
            # Create error app
            print("WARN: App is None, creating error app", file=sys.stderr, flush=True)
            error_app = FastAPI()
            
            @error_app.get("/")
            async def error_root():
                return {
                    "error": "Failed to load backend",
                    "import_error": import_error,
                    "backend_path": str(backend_dir),
                    "server_exists": server_file.exists() if server_file else False
                }
            
            @error_app.get("/api/")
            async def api_root():
                return {
                    "error": "Failed to load backend",
                    "import_error": import_error
                }
            
            from mangum import Mangum
            handler = Mangum(error_app, lifespan="off")
            print("INFO: Created error app handler", file=sys.stderr, flush=True)
            
    except Exception as e:
        print(f"ERROR: Critical error during initialization: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        
        # Create error handler
        try:
            from fastapi import FastAPI
            from mangum import Mangum
            error_app = FastAPI()
            
            @error_app.get("/")
            async def critical_error():
                return {
                    "error": "Critical initialization error",
                    "message": str(e),
                    "type": type(e).__name__
                }
            
            handler = Mangum(error_app, lifespan="off")
        except:
            pass

# Final safety check
if handler is None:
    print("CRITICAL: Handler is None! This should never happen.", file=sys.stderr, flush=True)
    # Last resort - this will fail but at least we tried
    raise RuntimeError("Failed to create handler")

# Export for Vercel
__all__ = ["handler"]
