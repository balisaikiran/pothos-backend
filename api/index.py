"""
Vercel Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes

CRITICAL: Handler MUST be defined at module level for Vercel.
ANY exception during module import will cause FUNCTION_INVOCATION_FAILED.

This version wraps EVERYTHING in try-except to ensure handler is ALWAYS defined.
"""

# CRITICAL: Wrap entire module in try-except to catch ANY exception
try:
    import sys
    import os
    import traceback
    from pathlib import Path
    
    # Initialize handler variable FIRST
    handler = None
    
    def create_minimal_error_app(error_message: str):
        """Create absolute minimal FastAPI app for errors"""
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
                    "path": path,
                    "note": "Check Vercel function logs for details"
                }
            
            return app
        except Exception as e:
            print(f"CRITICAL: Cannot create error app: {e}", file=sys.stderr, flush=True)
            return None
    
    def create_handler():
        """
        Create the Mangum handler for Vercel.
        This function MUST never raise an exception - it must always return a handler.
        """
        # Step 0: Import FastAPI and Mangum - CRITICAL imports
        try:
            from fastapi import FastAPI
            from mangum import Mangum
        except ImportError as e:
            error_msg = f"Failed to import FastAPI/Mangum: {e}"
            print(f"CRITICAL: {error_msg}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            # Try to create minimal app anyway
            try:
                error_app = create_minimal_error_app(error_msg)
                if error_app:
                    from mangum import Mangum
                    return Mangum(error_app, lifespan="off")
            except:
                pass
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
                error_msg = f"Path resolution failed: {path_error}"
                print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
                error_app = create_minimal_error_app(error_msg)
                if error_app:
                    from mangum import Mangum
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
                # Continue anyway
            
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
                    
                    # Execute the module - catch ALL possible exceptions
                    try:
                        spec.loader.exec_module(server_module)
                        print("INFO: Module executed successfully", file=sys.stderr, flush=True)
                    except Exception as exec_err:
                        import_error = f"Error executing server.py: {type(exec_err).__name__}: {exec_err}"
                        print(f"ERROR: {import_error}", file=sys.stderr, flush=True)
                        print(traceback.format_exc(), file=sys.stderr, flush=True)
                        raise
                    
                    # Get the app attribute
                    if hasattr(server_module, 'app'):
                        app = server_module.app
                        print("INFO: ✅ Successfully loaded app from server module", file=sys.stderr, flush=True)
                    else:
                        raise AttributeError("server module has no 'app' attribute")
                        
                except Exception as e:
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
                    from mangum import Mangum
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
                error_app = create_minimal_error_app(f"Failed to load backend: {import_error or 'Unknown error'}")
                if error_app:
                    from mangum import Mangum
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
            error_type = type(e).__name__
            error_msg = f"Unexpected error: {error_type}: {str(e)}"
            print(f"ERROR: {error_msg}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            
            # Create minimal error app
            try:
                error_app = create_minimal_error_app(error_msg)
                if error_app:
                    from mangum import Mangum
                    handler = Mangum(error_app, lifespan="off")
                    return handler
                return None
            except Exception as e2:
                print(f"CRITICAL: Even error app creation failed: {e2}", file=sys.stderr, flush=True)
                return None
    
    # CRITICAL: Create handler - wrap in try-except
    try:
        handler = create_handler()
    except BaseException as e:  # Catch ALL exceptions including SystemExit
        error_type = type(e).__name__
        print(f"FATAL: Exception during handler creation: {error_type}: {e}", file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        handler = None
    
    # Final safety check - ensure handler is NEVER None
    if handler is None:
        print("CRITICAL: Handler is None after creation! Creating minimal fallback...", file=sys.stderr, flush=True)
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
                    "message": "Unable to create handler. Check Vercel function logs.",
                    "path": path
                }
            
            handler = Mangum(minimal_app, lifespan="off")
            print("INFO: Created absolute minimal handler as last resort", file=sys.stderr, flush=True)
        except BaseException as e:
            # If even this fails, we're completely stuck
            # But we MUST have a handler - create a minimal one that will at least work
            print(f"FATAL: Cannot create minimal handler: {e}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            # Force import and create handler - this MUST work
            try:
                import fastapi
                import mangum
                # If we get here, imports work - try one more time
                minimal_app = fastapi.FastAPI()
                @minimal_app.get("/")
                async def fail():
                    return {"error": "Handler init failed - check logs"}
                handler = mangum.Mangum(minimal_app, lifespan="off")
                print("INFO: Created handler after forced import", file=sys.stderr, flush=True)
            except:
                # Absolute last resort - this should never happen
                print("FATAL: All handler creation attempts failed", file=sys.stderr, flush=True)
                # Set to None - will be handled by outer try-except
                handler = None
    
    # Export for Vercel
    __all__ = ["handler"]
    
    # Final verification
    if handler is None:
        # This should be impossible, but if it happens, we need to know
        print("FATAL: Handler is still None after all attempts!", file=sys.stderr, flush=True)
        # Don't raise - let the outer try-except handle it
        raise RuntimeError("Handler is None - this should be impossible")
    
    print("INFO: ✅ Handler initialized successfully", file=sys.stderr, flush=True)

except BaseException as e:
    # ABSOLUTE LAST RESORT: If ANYTHING fails, create minimal handler
    # This catches exceptions that occur even during import of this module
    import sys
    import traceback
    
    print(f"FATAL: Module-level exception: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    print(traceback.format_exc(), file=sys.stderr, flush=True)
    
    # Try to create absolute minimal handler
    try:
        from fastapi import FastAPI
        from mangum import Mangum
        emergency_app = FastAPI()
        
        @emergency_app.get("/")
        @emergency_app.get("/api/")
        @emergency_app.get("/api/{path:path}")
        async def emergency_handler(path: str = ""):
            return {
                "error": "Module initialization failed",
                "message": f"{type(e).__name__}: {str(e)}",
                "path": path,
                "note": "Check Vercel function logs"
            }
        
        handler = Mangum(emergency_app, lifespan="off")
        __all__ = ["handler"]
        print("INFO: Created emergency handler after module-level exception", file=sys.stderr, flush=True)
    except Exception as e2:
        # If even this fails, we're completely stuck
        # But we MUST export something
        print(f"FATAL: Cannot create emergency handler: {e2}", file=sys.stderr, flush=True)
        # Create a minimal callable that Vercel can at least invoke
        # This is the absolute last resort
        class EmergencyHandler:
            def __call__(self, event, context):
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"error": "Complete initialization failure - check logs"}'
                }
        handler = EmergencyHandler()
        __all__ = ["handler"]
        print("INFO: Created EmergencyHandler stub", file=sys.stderr, flush=True)
