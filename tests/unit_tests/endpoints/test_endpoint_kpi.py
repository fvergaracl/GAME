from datetime import datetime

import pytest

from app.api.v1.endpoints.kpi import health_check


@pytest.mark.asyncio
async def test_health_check_returns_status_and_timestamp():
    response = await health_check()

    assert response["status"] == "KPI service is running"
    assert isinstance(response["timestamp"], datetime)
