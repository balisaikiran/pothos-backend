"""
Vercel Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes

CRITICAL: Handler MUST be defined at module level for Vercel.
Any exception during module import will cause FUNCTION_INVOCATION_FAILED.

This version uses maximum defensive programming to ensure handler is ALWAYS defined.
"""
import sys
import os
import traceback
from pathlib import Path

def create_error_app(error_message: str, error_details: dict = None):
    """Create a FastAPI app that returns error information"""
    try:
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
    except Exception as e:
        # If even FastAPI import fails, we're in serious trouble
        print(f"CRITICAL: Cannot create error app: {e}", file=sys.stderr, flush=True)
        return None

def create_handler():
    """
    Create the Mangum handler for Vercel.
    This function MUST never raise an exception - it must always return a handler or None.
    """
    # Step 0: Import FastAPI and Mangum
    try:
        from fastapi import FastAPI
        from mangum import Mangum
    except ImportError as e:
        print(f"CRITICAL: Failed to import FastAPI/Mangum: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        return None
    
    # Step 1: Try to load the real backend
    try:
        print("INFO: Starting backend initialization...", file=sys.stderr, flush=True)
        
        # Resolve paths safely
        try:
            current_file = Path(__file__).resolve()
            api_dir = current_file.parent
            project_root = api_dir.parent
            backend_dir = project_root / "backend"
            server_file = backend_dir / "server.py"
            
            print(f"INFO: Current file: {current_file}", file=sys.stderr, flush=True)
            print(f"INFO: Project root: {project_root}", file=sys.stderr, flush=True)
            print(f"INFO: Backend dir: {backend_dir}", file=sys.stderr, flush=True)
            print(f"INFO: Server file exists: {server_file.exists()}", file=sys.stderr, flush=True)
        except Exception as path_error:
            print(f"ERROR: Path resolution failed: {path_error}", file=sys.stderr, flush=True)
            error_app = create_error_app("Path resolution failed", {"error": str(path_error)})
            if error_app:
                return Mangum(error_app, lifespan="off")
            return None
        
        # Add backend directory to Python path
        try:
            backend_path_str = str(backend_dir)
            if backend_path_str not in sys.path:
                sys.path.insert(0, backend_path_str)
                print(f"INFO: Added {backend_path_str} to sys.path", file=sys.stderr, flush=True)
        except Exception as path_error:
            print(f"WARN: Failed to add to sys.path: {path_error}", file=sys.stderr, flush=True)
            # Continue anyway - might still work
        
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
                
                # Execute the module - wrap in try-except to catch ANY error
                try:
                    spec.loader.exec_module(server_module)
                    print("INFO: Module executed successfully", file=sys.stderr, flush=True)
                except SyntaxError as syn_err:
                    import_error = f"Syntax error in server.py: {syn_err}"
                    print(f"ERROR: {import_error}", file=sys.stderr, flush=True)
                    print(traceback.format_exc(), file=sys.stderr, flush=True)
                    raise  # Re-raise to be caught by outer except
                except ImportError as imp_err:
                    import_error = f"Import error in server.py: {imp_err}"
                    print(f"ERROR: {import_error}", file=sys.stderr, flush=True)
                    print(traceback.format_exc(), file=sys.stderr, flush=True)
                    raise  # Re-raise to be caught by outer except
                except Exception as exec_err:
                    import_error = f"Error executing server.py: {exec_err}"
                    print(f"ERROR: {import_error}", file=sys.stderr, flush=True)
                    print(traceback.format_exc(), file=sys.stderr, flush=True)
                    raise  # Re-raise to be caught by outer except
                
                # Get the app attribute
                if hasattr(server_module, 'app'):
                    app = server_module.app
                    print("INFO: ✅ Successfully loaded app from server module", file=sys.stderr, flush=True)
                else:
                    raise AttributeError("server module has no 'app' attribute")
                    
            except (SyntaxError, ImportError, AttributeError, Exception) as e:
                import_error = f"importlib failed: {type(e).__name__}: {str(e)}"
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
                    import_error = f"{import_error} | direct import failed: {type(e2).__name__}: {str(e2)}"
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
        try:
            error_details = {
                "import_error": import_error,
                "backend_path": str(backend_dir),
                "server_exists": server_file.exists() if server_file else False,
                "python_path": sys.path[:3]  # First 3 entries for debugging
            }
            error_app = create_error_app("Failed to load backend server", error_details)
            if error_app:
                handler = Mangum(error_app, lifespan="off")
                print("INFO: Created error app handler", file=sys.stderr, flush=True)
                return handler
            else:
                print("ERROR: Failed to create error app", file=sys.stderr, flush=True)
                return None
        except Exception as e:
            print(f"ERROR: Failed to create error app handler: {e}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            return None
        
    except Exception as e:
        # Catch-all for any unexpected errors during initialization
        print(f"ERROR: Unexpected error during handler creation: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        
        # Create minimal error app
        try:
            error_app = create_error_app(
                f"Critical initialization error: {type(e).__name__}: {str(e)}",
                {"error_type": type(e).__name__, "traceback": traceback.format_exc()}
            )
            if error_app:
                handler = Mangum(error_app, lifespan="off")
                return handler
            return None
        except Exception as e2:
            print(f"CRITICAL: Even error app creation failed: {e2}", file=sys.stderr, flush=True)
            return None

# CRITICAL: Wrap handler creation in try-except to ensure NO exception escapes
# This is the absolute last line of defense against FUNCTION_INVOCATION_FAILED
try:
    handler = create_handler()
except Exception as e:
    # This should NEVER happen if create_handler() is implemented correctly
    # But we catch it anyway as a safety net
    print(f"FATAL: Exception during handler creation: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    print(traceback.format_exc(), file=sys.stderr, flush=True)
    handler = None

# Final safety check - ensure handler is never None
if handler is None:
    print("CRITICAL: Handler is None after creation!", file=sys.stderr, flush=True)
    # Last resort: try to create absolute minimal handler
    try:
        from fastapi import FastAPI
        from mangum import Mangum
        minimal_app = FastAPI()
        
        @minimal_app.get("/")
        @minimal_app.get("/api/")
        @minimal_app.get("/api/{path:path}")
        async def critical_failure(path: str = ""):
            return {
                "error": "CRITICAL: Handler initialization failed",
                "message": "Unable to create any handler. Check Vercel function logs.",
                "path": path
            }
        
        handler = Mangum(minimal_app, lifespan="off")
        print("INFO: Created absolute minimal handler as last resort", file=sys.stderr, flush=True)
    except Exception as e:
        # If even this fails, we MUST raise an error
        # Better to fail loudly than silently return None
        print(f"FATAL: Cannot create minimal handler: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        # Don't set handler - let it raise RuntimeError below
        handler = None

# Export for Vercel - handler MUST be available at module level
__all__ = ["handler"]

# Final verification
if handler is None:
    raise RuntimeError("Handler is still None after all fallbacks - this should be impossible")

print("INFO: ✅ Handler initialized successfully", file=sys.stderr, flush=True)
