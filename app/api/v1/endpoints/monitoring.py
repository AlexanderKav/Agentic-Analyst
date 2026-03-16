# app/api/v1/endpoints/monitoring.py
from fastapi import APIRouter
from datetime import datetime, timedelta

from app.api.v1.models.responses import HealthResponse
from agents.monitoring import get_cost_tracker, get_performance_tracker, get_audit_logger

# ✅ Make sure this line is present
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@router.get("/costs")
async def get_costs(days: int = 7):
    """Get cost tracking data"""
    tracker = get_cost_tracker()
    return tracker.get_cost_report(days=days)

@router.get("/performance")
async def get_performance():
    """Get performance metrics"""
    tracker = get_performance_tracker()
    return tracker.get_all_stats()

@router.get("/audit")
async def get_audit_logs(
    user: str = None,
    agent: str = None,
    action: str = None,
    days: int = 7
):
    """Get audit logs"""
    logger = get_audit_logger()
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return logger.query_audit(
        user=user,
        agent=agent,
        action_type=action,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )