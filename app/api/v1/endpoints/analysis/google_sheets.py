import math
import os
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.models.analysis import AnalysisHistory
from app.api.v1.models.requests import GoogleSheetsRequest, GoogleSheetsTestRequest
from app.api.v1.models.responses import FileUploadResponse
from app.api.v1.models.user import User
from app.core.analysis import AnalysisOrchestrator
from app.core.database import get_db
from connectors.google_sheets import GoogleSheetsConnector

from .utils import (
    MIN_ROWS,
    validate_dataframe,
    validate_row_count,
    deep_clean_for_json,
    sanitize_for_json,
)

router = APIRouter()


@router.post("/google-sheets", response_model=FileUploadResponse)
async def analyze_google_sheets(
    request: Request,
    sheets_request: GoogleSheetsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Connect to Google Sheets and analyze data."""
    orchestrator = AnalysisOrchestrator(user_id=current_user.id)

    try:
        config = sheets_request.sheet_config

        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            raise HTTPException(status_code=500, detail="Google credentials not configured")

        sheet_id = config.get('sheet_id')
        sheet_range = config.get('sheet_range', 'A1:Z1000')

        connector = GoogleSheetsConnector(sheet_id, sheet_range)
        df = connector.fetch_sheet()

        # Validate row count
        is_valid, error_msg = validate_row_count(len(df), "sheet")
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        validate_dataframe(df)

        preview_data = df.head(5).to_dict('records')
        cleaned_preview = [sanitize_for_json(row) for row in preview_data]

        results, exec_time = await orchestrator.analyze_dataframe(df, sheets_request.question or "")

        if results is None:
            results = {}

        analysis_results = {
            "success": results.get("success", False),
            "insights": results.get("insights", ""),
            "raw_insights": results.get("raw_insights", {}),
            "results": results.get("results", {}),
            "plan": results.get("plan", {"plan": []}),
            "warnings": results.get("warnings", []),
            "mapping": results.get("mapping", {}),
            "data_summary": {
                "rows": len(df),
                "columns": list(df.columns)
            },
            "execution_time": exec_time,
            "is_generic_overview": results.get("is_generic_overview", False)
        }

        cleaned_results = deep_clean_for_json(analysis_results)

        data_source = {
            "sheet_id": sheet_id[:8] + "...",
            "sheet_range": sheet_range,
            "rows": len(df),
            "columns": list(df.columns)
        }
        cleaned_data_source = deep_clean_for_json(data_source)

        history = AnalysisHistory(
            user_id=current_user.id,
            analysis_type="google_sheets",
            question=sheets_request.question or "General Overview",
            raw_results=cleaned_results,
            data_source=cleaned_data_source
        )
        db.add(history)
        db.commit()

        final_results = deep_clean_for_json(analysis_results)

        return FileUploadResponse(
            filename=f"google_sheet_{sheet_id[:8]}",
            rows=len(df),
            columns=list(df.columns),
            preview=cleaned_preview,
            analysis_results=final_results
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-google-sheets")
async def test_google_sheets_connection(
    request: Request,
    sheets_request: GoogleSheetsTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test Google Sheets connection and validate schema."""
    try:
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            raise HTTPException(status_code=500, detail="Google credentials not configured")

        connector = GoogleSheetsConnector(sheets_request.sheet_id, sheets_request.sheet_range)
        df = connector.fetch_sheet()

        # Validate row count
        is_valid, error_msg = validate_row_count(len(df), "sheet")
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        required_columns = ['date', 'revenue']
        df_columns_lower = [col.lower() for col in df.columns]

        missing = []
        found_columns = {}

        for req_col in required_columns:
            if req_col in df_columns_lower:
                original_col = df.columns[df_columns_lower.index(req_col)]
                found_columns[req_col] = original_col
            else:
                missing.append(req_col)

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing)}. Your sheet must contain 'date' and 'revenue' columns."
            )

        date_col = found_columns['date']
        try:
            pd.to_datetime(df[date_col], errors='raise')
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Date column '{date_col}' contains invalid date formats. Please ensure dates are in a recognized format (e.g., YYYY-MM-DD)."
            )

        revenue_col = found_columns['revenue']
        try:
            pd.to_numeric(df[revenue_col], errors='raise')
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Revenue column '{revenue_col}' contains non-numeric values. Please ensure revenue values are numbers."
            )

        preview_data = df.head(3).to_dict('records')
        cleaned_preview = [sanitize_for_json(row) for row in preview_data]

        response = {
            "status": "success",
            "message": f"✅ Successfully connected! Sheet has {len(df)} rows with valid schema.",
            "rows": len(df),
            "columns": list(df.columns),
            "preview": cleaned_preview,
            "found_columns": found_columns,
            "permission_status": connector.get_permission_status()
        }

        permission_warning = connector.get_permission_warning()
        if permission_warning:
            response["warning"] = permission_warning

        return sanitize_for_json(response)

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']