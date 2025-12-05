"""
Reporting Router
Manages saved reports, star schema queries, and data aggregations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.routers.auth import get_current_user, UserData
from src.services.reporting_service import ReportingService
from src.core.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    connection_id: str
    query_config: Dict[str, Any]
    visualization_config: Optional[Dict[str, Any]] = {}


class ReportResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


class ReportExecuteRequest(BaseModel):
    filters: Optional[Dict[str, Any]] = {}
    limit: Optional[int] = 1000


@router.post("/", response_model=ReportResponse)
async def create_report(
    report: ReportCreate,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Create a new saved report"""
    try:
        reporting_service = ReportingService(db)
        report_id = await reporting_service.create_report(
            organization_id=current_user.organization_id,
            name=report.name,
            description=report.description,
            query_config=report.query_config,
            visualization_config=report.visualization_config
        )
        
        saved_report = await reporting_service.get_report(report_id)
        return ReportResponse(
            id=saved_report.id,
            name=saved_report.name,
            description=saved_report.description,
            created_at=saved_report.created_at,
            updated_at=saved_report.updated_at
        )
    except Exception as e:
        logger.error(f"Failed to create report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """List all reports for the organization"""
    try:
        reporting_service = ReportingService(db)
        reports = await reporting_service.list_reports(current_user.organization_id)
        
        return [
            ReportResponse(
                id=report.id,
                name=report.name,
                description=report.description,
                created_at=report.created_at,
                updated_at=report.updated_at
            )
            for report in reports
        ]
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Get report details"""
    try:
        reporting_service = ReportingService(db)
        report = await reporting_service.get_report(report_id)
        
        if report.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return ReportResponse(
            id=report.id,
            name=report.name,
            description=report.description,
            created_at=report.created_at,
            updated_at=report.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{report_id}/execute")
async def execute_report(
    report_id: str,
    request: ReportExecuteRequest,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Execute a saved report and return results"""
    try:
        reporting_service = ReportingService(db)
        report = await reporting_service.get_report(report_id)
        
        if report.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Report not found")
        
        results = await reporting_service.execute_report(
            report_id,
            filters=request.filters,
            limit=request.limit
        )
        
        return {
            "report_id": report_id,
            "report_name": report.name,
            "data": results["data"],
            "columns": results["columns"],
            "row_count": results["row_count"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: UserData = Depends(get_current_user),
    db = Depends(get_session)
):
    """Delete a report"""
    try:
        reporting_service = ReportingService(db)
        report = await reporting_service.get_report(report_id)
        
        if report.organization_id != current_user.organization_id:
            raise HTTPException(status_code=404, detail="Report not found")
        
        await reporting_service.delete_report(report_id)
        return {"message": "Report deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
