"""
Vercel Serverless Function for FastAPI Backend
This file MUST export a 'handler' variable that is a Mangum instance.
"""

import sys

# Initialize handler - will be set below
handler = None

# Wrap everything in try-except to catch ALL exceptions
try:
    import traceback
    from pathlib import Path
    
    # Import FastAPI and Mangum - these MUST be available
    from fastapi import FastAPI
    from mangum import Mangum
    
    def create_error_app(message: str):
        """Create a FastAPI app that shows an error message"""
        app = FastAPI()
        @app.get("/")
        @app.get("/api/")
        @app.get("/api/{path:path}")
        async def error_handler(path: str = ""):
            return {
                "error": "Backend initialization failed",
                "message": message,
                "path": path
            }
        return app
    
    # Try to load the real backend
    try:
        print("INFO: Starting backend initialization...", file=sys.stderr, flush=True)
        
        # Get paths
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent / "backend"
        server_file = backend_dir / "server.py"
        
        print(f"INFO: Backend dir: {backend_dir}", file=sys.stderr, flush=True)
        print(f"INFO: Server file exists: {server_file.exists()}", file=sys.stderr, flush=True)
        
        # Add backend to path
        backend_path = str(backend_dir)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Try to import server
        app = None
        if server_file.exists():
            try:
                # Method 1: importlib
                import importlib.util
                spec = importlib.util.spec_from_file_location("server", server_file)
                if spec and spec.loader:
                    server_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(server_module)
                    if hasattr(server_module, 'app'):
                        app = server_module.app
                        print("INFO: ✅ Successfully loaded app from server", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"ERROR: importlib failed: {e}", file=sys.stderr, flush=True)
                # Try direct import
                try:
                    if 'server' in sys.modules:
                        del sys.modules['server']
                    from server import app
                    print("INFO: ✅ Direct import succeeded", file=sys.stderr, flush=True)
                except Exception as e2:
                    print(f"ERROR: Direct import failed: {e2}", file=sys.stderr, flush=True)
                    print(traceback.format_exc(), file=sys.stderr, flush=True)
        
        # Create handler with app or error app
        if app is not None:
            handler = Mangum(app, lifespan="off")
            print("INFO: ✅ Handler created with real app", file=sys.stderr, flush=True)
        else:
            # Create error app
            error_app = create_error_app("Failed to load backend server - check logs")
            handler = Mangum(error_app, lifespan="off")
            print("INFO: Created handler with error app", file=sys.stderr, flush=True)
    
    except Exception as e:
        # If anything fails, create error app
        print(f"ERROR: Exception during initialization: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        try:
            error_app = create_error_app(f"Initialization error: {type(e).__name__}: {str(e)}")
            handler = Mangum(error_app, lifespan="off")
            print("INFO: Created handler with error app after exception", file=sys.stderr, flush=True)
        except Exception as e2:
            print(f"FATAL: Cannot create error app: {e2}", file=sys.stderr, flush=True)
            # This should never happen if FastAPI/Mangum are installed
            # But if it does, we need to create something
            raise RuntimeError(f"Cannot create handler: {e2}. Original: {e}")

except BaseException as e:
    # Catch ALL exceptions including SystemExit
    # This should never happen if FastAPI/Mangum are installed
    try:
        import sys
        import traceback
        print(f"FATAL: Module-level exception: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        
        # Try to create emergency handler
        try:
            from fastapi import FastAPI
            from mangum import Mangum
            app = FastAPI()
            @app.get("/")
            @app.get("/api/")
            @app.get("/api/{path:path}")
            async def emergency(path: str = ""):
                return {
                    "error": "Critical initialization failure",
                    "type": type(e).__name__,
                    "message": str(e),
                    "path": path
                }
            handler = Mangum(app, lifespan="off")
            print("INFO: Created emergency handler", file=sys.stderr, flush=True)
        except Exception as e2:
            # If even this fails, FastAPI/Mangum are not available
            # This should never happen in Vercel if requirements.txt is correct
            print(f"FATAL: Emergency handler failed: {e2}", file=sys.stderr, flush=True)
            # We MUST have a handler, so raise to show the error clearly
            # This will cause FUNCTION_INVOCATION_FAILED, but at least we'll see the error
            raise RuntimeError(
                f"Cannot create handler. FastAPI/Mangum may not be installed. "
                f"Check api/requirements.txt includes 'mangum>=0.17.0' and 'fastapi'. "
                f"Original error: {e}"
            )
    except:
        # If even error handling fails, we're completely stuck
        # Raise to show error
        raise RuntimeError(f"Complete failure during module import: {e}")

# Export handler - MUST exist
__all__ = ["handler"]

# Final verification
if handler is None:
    raise RuntimeError(
        "Handler is None. This should be impossible. "
        "Check that mangum and fastapi are installed (api/requirements.txt)."
    )

print("INFO: ✅ Handler initialized successfully", file=sys.stderr, flush=True)
