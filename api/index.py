"""
Vercel Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes

CRITICAL: Handler MUST be defined at module level for Vercel.
Any exception during module import will cause FUNCTION_INVOCATION_FAILED.
"""
import sys
import os
import traceback
from pathlib import Path

# Initialize handler to None - will be set below
handler = None

def create_error_app(error_message: str, error_details: dict = None):
    """Create a FastAPI app that returns error information"""
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    @app.get("/api/")
    @app.get("/api/{path:path}")
    async def error_handler(path: str = ""):
        return {
            "error": "Backend initialization failed",
            "message": error_message,
            "details": error_details or {},
            "path": path
        }
    
    return app

def create_handler():
    """
    Create the Mangum handler for Vercel.
    This function encapsulates all initialization logic to prevent
    module-level exceptions from causing FUNCTION_INVOCATION_FAILED.
    """
    try:
        from fastapi import FastAPI
        from mangum import Mangum
    except ImportError as e:
        # If basic imports fail, we can't create any handler
        print(f"CRITICAL: Failed to import FastAPI/Mangum: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        # Return None - will be handled below
        return None
    
    # Step 1: Try to load the real backend
    try:
        print("INFO: Starting backend initialization...", file=sys.stderr, flush=True)
        
        # Resolve paths
        current_file = Path(__file__).resolve()
        api_dir = current_file.parent
        project_root = api_dir.parent
        backend_dir = project_root / "backend"
        server_file = backend_dir / "server.py"
        
        print(f"INFO: Current file: {current_file}", file=sys.stderr, flush=True)
        print(f"INFO: Project root: {project_root}", file=sys.stderr, flush=True)
        print(f"INFO: Backend dir: {backend_dir}", file=sys.stderr, flush=True)
        print(f"INFO: Server file exists: {server_file.exists()}", file=sys.stderr, flush=True)
        
        # Add backend directory to Python path
        backend_path_str = str(backend_dir)
        if backend_path_str not in sys.path:
            sys.path.insert(0, backend_path_str)
            print(f"INFO: Added {backend_path_str} to sys.path", file=sys.stderr, flush=True)
        
        # Try to import the server module
        app = None
        import_error = None
        
        if not server_file.exists():
            import_error = f"server.py not found at {server_file}"
            print(f"ERROR: {import_error}", file=sys.stderr, flush=True)
        else:
            # Method 1: Try importlib (more reliable for serverless)
            try:
                print("INFO: Attempting to load server.py via importlib...", file=sys.stderr, flush=True)
                import importlib.util
                
                spec = importlib.util.spec_from_file_location("server", server_file)
                if spec is None or spec.loader is None:
                    raise ImportError("Failed to create module spec from server.py")
                
                server_module = importlib.util.module_from_spec(spec)
                
                # Execute the module - this is where errors often occur
                spec.loader.exec_module(server_module)
                print("INFO: Module executed successfully", file=sys.stderr, flush=True)
                
                # Get the app attribute
                if hasattr(server_module, 'app'):
                    app = server_module.app
                    print("INFO: ✅ Successfully loaded app from server module", file=sys.stderr, flush=True)
                else:
                    raise AttributeError("server module has no 'app' attribute")
                    
            except Exception as e:
                import_error = f"importlib failed: {str(e)}"
                print(f"ERROR: {import_error}", file=sys.stderr, flush=True)
                print(traceback.format_exc(), file=sys.stderr, flush=True)
                
                # Method 2: Try direct import as fallback
                try:
                    print("INFO: Trying direct import as fallback...", file=sys.stderr, flush=True)
                    # Clear any partial module from sys.modules
                    if 'server' in sys.modules:
                        del sys.modules['server']
                    
                    from server import app
                    print("INFO: ✅ Direct import succeeded", file=sys.stderr, flush=True)
                    import_error = None
                except Exception as e2:
                    import_error = f"{import_error} | direct import failed: {str(e2)}"
                    print(f"ERROR: Direct import also failed: {e2}", file=sys.stderr, flush=True)
                    print(traceback.format_exc(), file=sys.stderr, flush=True)
        
        # Step 2: Create handler with the loaded app (or error app)
        if app is not None:
            try:
                print("INFO: Creating Mangum handler with loaded app...", file=sys.stderr, flush=True)
                handler = Mangum(app, lifespan="off")
                print("INFO: ✅ Handler created successfully with real app", file=sys.stderr, flush=True)
                return handler
            except Exception as e:
                print(f"ERROR: Failed to create handler with app: {e}", file=sys.stderr, flush=True)
                print(traceback.format_exc(), file=sys.stderr, flush=True)
                # Fall through to create error app
        
        # Step 3: Create error app if we couldn't load the real app
        print("WARN: Could not load real app, creating error app", file=sys.stderr, flush=True)
        error_details = {
            "import_error": import_error,
            "backend_path": str(backend_dir),
            "server_exists": server_file.exists() if server_file else False,
            "python_path": sys.path[:3]  # First 3 entries for debugging
        }
        error_app = create_error_app("Failed to load backend server", error_details)
        handler = Mangum(error_app, lifespan="off")
        print("INFO: Created error app handler", file=sys.stderr, flush=True)
        return handler
        
    except Exception as e:
        # Catch-all for any unexpected errors during initialization
        print(f"ERROR: Unexpected error during handler creation: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        
        # Create minimal error app
        try:
            error_app = create_error_app(
                f"Critical initialization error: {str(e)}",
                {"error_type": type(e).__name__, "traceback": traceback.format_exc()}
            )
            handler = Mangum(error_app, lifespan="off")
            return handler
        except Exception as e2:
            print(f"CRITICAL: Even error app creation failed: {e2}", file=sys.stderr, flush=True)
            return None

# CRITICAL: Create handler at module level
# This MUST succeed or Vercel will return FUNCTION_INVOCATION_FAILED
handler = create_handler()

# Final safety check - ensure handler is never None
if handler is None:
    print("CRITICAL: Handler creation failed completely!", file=sys.stderr, flush=True)
    # Last resort: try to create absolute minimal handler
    try:
        from fastapi import FastAPI
        from mangum import Mangum
        minimal_app = FastAPI()
        
        @minimal_app.get("/")
        async def critical_failure():
            return {
                "error": "CRITICAL: Handler initialization failed",
                "message": "Unable to create any handler. Check Vercel function logs."
            }
        
        handler = Mangum(minimal_app, lifespan="off")
        print("INFO: Created absolute minimal handler as last resort", file=sys.stderr, flush=True)
    except Exception as e:
        # If even this fails, we're completely stuck
        # This should never happen, but if it does, we need to raise
        # so Vercel can report the error properly
        print(f"FATAL: Cannot create any handler: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        # Raise an error so Vercel logs it - better than silent failure
        raise RuntimeError(f"Failed to create handler: {e}") from e

# Export for Vercel - handler MUST be available at module level
__all__ = ["handler"]
