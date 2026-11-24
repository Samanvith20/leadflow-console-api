from app.main import app


def test_lead_and_dashboard_routes_are_registered() -> None:
    methods_by_path: dict[str, set[str]] = {}
    for route in app.routes:
        if hasattr(route, "methods"):
            methods_by_path.setdefault(route.path, set()).update(route.methods)

    assert {"GET"} <= methods_by_path["/api/v1/dashboard"]
    assert {"GET"} <= methods_by_path["/api/v1/leads"]
    assert {"GET", "PATCH"} <= methods_by_path["/api/v1/leads/{lead_id}"]
