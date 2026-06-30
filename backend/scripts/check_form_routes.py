from app.main import app

REQUIRED = [
    ("GET", "/form-options"),
    ("GET", "/production-runs"),
    ("POST", "/production-runs"),
    ("POST", "/production-events"),
    ("POST", "/material-behavior-events"),
    ("POST", "/material-blocks"),
    ("POST", "/daily-quality-inputs"),
    ("GET", "/public/app-info"),
    ("POST", "/auth/login"),
    ("GET", "/auth/me"),
]

for method, path in REQUIRED:
    ok = any(
        getattr(route, "path", None) == path
        and method in getattr(route, "methods", set())
        for route in app.routes
    )
    print(f"{'OK' if ok else 'MISSING':7} {method:6} {path}")
