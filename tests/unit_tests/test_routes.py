from app.api.v1.routes import routers, routes


def test_routes_returns_underlying_router_routes():
    result = routes()

    assert result is routers.routes
    assert len(result) > 0
