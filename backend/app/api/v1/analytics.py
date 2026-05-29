"""Analytics API routes."""

from fastapi import APIRouter, Depends

from app.api.deps import get_analytics_service
from app.schemas.analytics import AnalyticsDashboard
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsDashboard:
    """Return communication analytics for the dashboard."""
    return await analytics_service.get_dashboard()
