from app.main import app


def test_authentication_routes_are_registered() -> None:
    routes = {route.path for route in app.routes}

    assert {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/change-password",
    }.issubset(routes)
