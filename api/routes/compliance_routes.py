from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from apgi_framework.compliance.compliance_framework import get_compliance_framework

router = APIRouter(prefix="/v1/compliance", tags=["Compliance"])


@router.get("/export", response_model=Dict[str, Any])
async def export_compliance_evidence() -> Dict[str, Any]:
    """
    Export compliance evidence pack to compliance management system.
    This generates a comprehensive compliance report including active consent records,
    data classifications, and retention schedules.
    """
    try:
        compliance_framework = get_compliance_framework()
        report = compliance_framework.generate_compliance_report()
        return {"status": "success", "evidence_pack": report}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance report: {str(e)}",
        )
