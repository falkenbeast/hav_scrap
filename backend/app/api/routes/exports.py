"""
Export Management API Endpoints.
Provides REST interface for generating, querying, downloading, and removing
Excel placement intelligence deliverables.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.export import ExportGenerateRequest, ExportHistoryResponse, ExportListResponse
from app.services.export_service import export_service

logger = logging.getLogger("hav_scrap")

router = APIRouter(prefix="/exports", tags=["Excel Deliverables & Reports"])


@router.post("/generate", response_model=ExportHistoryResponse, summary="Generate structured Excel workbook")
async def generate_export(
    request: ExportGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers OpenPyXL placement workbook generation across requested categories.
    Saves the .xlsx workbook to data/exports/ and logs an audit record in the database.
    """
    try:
        history = export_service.generate_export(
            db=db,
            export_type=request.export_type,
            include_sheets=request.include_sheets,
            filters=request.filters
        )

        resp = ExportHistoryResponse.model_validate(history)
        resp.download_url = f"/api/exports/{history.id}/download"
        return resp
    except Exception as e:
        logger.error(f"Error during export generation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Excel report: {str(e)}"
        )


@router.get("", response_model=ExportListResponse, summary="List past Excel export history")
async def list_exports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieves all past placement intelligence export history with download links.
    """
    try:
        data = export_service.list_exports(db, page=page, page_size=page_size)
        items_resp = []
        for item in data["items"]:
            resp_item = ExportHistoryResponse.model_validate(item)
            resp_item.download_url = f"/api/exports/{item.id}/download"
            items_resp.append(resp_item)

        return ExportListResponse(items=items_resp, total=data["total"])
    except Exception as e:
        logger.error(f"Error fetching export list: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{export_id}", response_model=ExportHistoryResponse, summary="Get export metadata by ID")
async def get_export(
    export_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves metadata for a specific export record.
    """
    history = export_service.get_export_by_id(db, export_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export record with ID {export_id} not found."
        )

    resp = ExportHistoryResponse.model_validate(history)
    resp.download_url = f"/api/exports/{history.id}/download"
    return resp


@router.get("/{export_id}/download", summary="Download Excel workbook file")
async def download_export(
    export_id: int,
    db: Session = Depends(get_db)
):
    """
    Streams the physical .xlsx file directly to the client with appropriate attachment headers.
    """
    history = export_service.get_export_by_id(db, export_id)
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export record with ID {export_id} not found."
        )

    file_path = export_service.get_export_file_path(db, export_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical file for export '{history.filename}' does not exist on disk."
        )

    return FileResponse(
        path=str(file_path),
        filename=history.filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{history.filename}"'
        }
    )


@router.delete("/{export_id}", summary="Delete export deliverable")
async def delete_export(
    export_id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes both the database record and the physical .xlsx file from data/exports/.
    """
    success = export_service.delete_export(db, export_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export record with ID {export_id} not found."
        )
    return {"message": f"Export {export_id} successfully removed."}

