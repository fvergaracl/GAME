from datetime import datetime

from fastapi import APIRouter

router = APIRouter(
    prefix="/kpi",
    tags=["kpi"],
)


summary_health_check = "Health Check"
response_example_health_check = {
    "status": "KPI service is running",
    "timestamp": "2026-02-10T18:30:00Z",
}

responses_health_check = {
    200: {
        "description": "KPI service is healthy",
        "content": {"application/json": {"example": response_example_health_check}},
    },
    500: {
        "description": "Internal server error while evaluating health status",
        "content": {
            "application/json": {
                "example": {"detail": "Error when checking KPI health"}
            }
        },
    },
}

description_health_check = """
Returns a lightweight availability signal for the KPI API service.

### Authentication
- No authentication required.

### Success (200)
Returns:
- `status`: service health message
- `timestamp`: UTC timestamp of the health response generation

### Error Cases
- `500`: unexpected runtime failure while generating the health response

<sub>**Id_endpoint:** `health_check`</sub>"""


@router.get(
    "/health_check",
    summary=summary_health_check,
    description=description_health_check,
    responses=responses_health_check,
)
async def health_check():
    """
    Check the health of the KPI service.

    Returns:
        dict: The health status of the KPI service.
    """
    return {"status": "KPI service is running", "timestamp": datetime.utcnow()}
