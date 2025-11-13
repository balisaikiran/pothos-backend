"""
Vercel Serverless Function for FastAPI Backend
CRITICAL: Handler MUST be defined - NO exceptions can escape
"""

import sys

# Initialize handler FIRST - before any imports
handler = None

# ABSOLUTE LAST RESORT: Wrap EVERYTHING including imports
try:
    # Import basic modules first
    import traceback
    from pathlib import Path
    
    # Try to import FastAPI and Mangum
    # If these fail, we'll create a stub handler
    fastapi_available = False
    mangum_available = False
    
    try:
        from fastapi import FastAPI
        fastapi_available = True
    except ImportError as e:
        print(f"WARN: FastAPI not available: {e}", file=sys.stderr, flush=True)
    
    try:
        from mangum import Mangum
        mangum_available = True
    except ImportError as e:
        print(f"WARN: Mangum not available: {e}", file=sys.stderr, flush=True)
    
    # If both are available, try to load backend
    if fastapi_available and mangum_available:
        try:
            print("INFO: Starting backend initialization...", file=sys.stderr, flush=True)
            
            # Get paths
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent / "backend"
            server_file = backend_dir / "server.py"
            
            print(f"INFO: Backend dir: {backend_dir}", file=sys.stderr, flush=True)
            print(f"INFO: Server exists: {server_file.exists()}", file=sys.stderr, flush=True)
            
            # Add to path
            backend_path = str(backend_dir)
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            # Try to load server
            app = None
            if server_file.exists():
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("server", server_file)
                    if spec and spec.loader:
                        server_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(server_module)
                        if hasattr(server_module, 'app'):
                            app = server_module.app
                            print("INFO: ✅ Loaded app from server", file=sys.stderr, flush=True)
                except Exception as e:
                    print(f"ERROR: importlib failed: {e}", file=sys.stderr, flush=True)
                    print(traceback.format_exc(), file=sys.stderr, flush=True)
                    # Try direct import
                    try:
                        if 'server' in sys.modules:
                            del sys.modules['server']
                        from server import app
                        print("INFO: ✅ Direct import worked", file=sys.stderr, flush=True)
                    except Exception as e2:
                        print(f"ERROR: Direct import failed: {e2}", file=sys.stderr, flush=True)
                        print(traceback.format_exc(), file=sys.stderr, flush=True)
            
            # Create handler
            if app is not None:
                handler = Mangum(app, lifespan="off")
                print("INFO: ✅ Handler created with app", file=sys.stderr, flush=True)
            else:
                # Create error app
                error_app = FastAPI()
                @error_app.get("/")
                @error_app.get("/api/")
                @error_app.get("/api/{path:path}")
                async def error_handler(path: str = ""):
                    return {
                        "error": "Backend failed to load",
                        "message": "Check Vercel function logs",
                        "path": path
                    }
                handler = Mangum(error_app, lifespan="off")
                print("INFO: Created error app handler", file=sys.stderr, flush=True)
        
        except Exception as e:
            print(f"ERROR: Backend loading failed: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            # Create error app
            try:
                error_app = FastAPI()
                @error_app.get("/")
                @error_app.get("/api/")
                @error_app.get("/api/{path:path}")
                async def error_handler(path: str = ""):
                    return {
                        "error": "Initialization failed",
                        "type": type(e).__name__,
                        "message": str(e),
                        "path": path
                    }
                handler = Mangum(error_app, lifespan="off")
                print("INFO: Created error app after exception", file=sys.stderr, flush=True)
            except Exception as e2:
                print(f"FATAL: Cannot create error app: {e2}", file=sys.stderr, flush=True)
                handler = None
    
    # If FastAPI/Mangum not available, create stub
    if handler is None:
        print("WARN: FastAPI/Mangum not available, creating stub handler", file=sys.stderr, flush=True)
        # Create a minimal callable that at least exists
        class StubHandler:
            def __call__(self, event, context):
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"error": "FastAPI/Mangum not installed. Check api/requirements.txt"}'
                }
        handler = StubHandler()
        print("INFO: Created stub handler", file=sys.stderr, flush=True)

except BaseException as e:
    # Catch EVERYTHING - including SystemExit, KeyboardInterrupt, etc.
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
                    "error": "Critical failure",
                    "type": type(e).__name__,
                    "message": str(e),
                    "path": path
                }
            handler = Mangum(app, lifespan="off")
            print("INFO: Created emergency handler", file=sys.stderr, flush=True)
        except Exception as e2:
            print(f"FATAL: Emergency handler failed: {e2}", file=sys.stderr, flush=True)
            # Create stub handler as absolute last resort
            class EmergencyStub:
                def __call__(self, event, context):
                    return {
                        "statusCode": 500,
                        "headers": {"Content-Type": "application/json"},
                        "body": f'{{"error": "Complete failure: {type(e).__name__}: {str(e)}"}}'
                    }
            handler = EmergencyStub()
            print("INFO: Created emergency stub handler", file=sys.stderr, flush=True)
    except:
        # If even error handling fails, create minimal stub
        class FinalStub:
            def __call__(self, event, context):
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"error": "Handler initialization completely failed"}'
                }
        handler = FinalStub()
        print("INFO: Created final stub handler", file=sys.stderr, flush=True)

# Export handler - MUST exist
__all__ = ["handler"]

# Final check - handler MUST exist
if handler is None:
    # This should be impossible, but if it happens, create stub
    class NoneStub:
        def __call__(self, event, context):
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": "Handler is None - check logs"}'
            }
    handler = NoneStub()
    print("WARN: Handler was None, created stub", file=sys.stderr, flush=True)

print("INFO: ✅ Handler initialized", file=sys.stderr, flush=True)
