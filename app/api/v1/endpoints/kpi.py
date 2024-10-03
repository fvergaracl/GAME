from fastapi import APIRouter
from datetime import datetime

router = APIRouter(
    prefix="/kpi",
    tags=["kpi"],
)


summary_health_check = "Health Check"
description_health_check = """
## Health Check
### This endpoint checks the health of the KPI service.
<sub>**Id_endpoint:** health_check</sub>"""


@router.get(
    "/health_check",
    summary=summary_health_check,
    description=description_health_check,
)
async def health_check():
    """
    Check the health of the KPI service.

    Returns:
        dict: The health status of the KPI service.
    """
    return {"status": "KPI service is running", "timestamp": datetime.utcnow()}
