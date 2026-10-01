from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.shipments import router as shipments_router
from app.api.v1.vehicles import router as vehicles_router
from app.api.v1.drivers import router as drivers_router
from app.api.v1.routes import router as routes_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.ml import router as ml_router
from app.api.v1.rag import router as rag_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.agent import router as agent_router, assistant_router
from app.api.v1.ai import router as ai_router
from app.api.v1.settings import router as settings_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(shipments_router)
api_v1_router.include_router(vehicles_router)
api_v1_router.include_router(drivers_router)
api_v1_router.include_router(routes_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(ml_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(assistant_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(settings_router)

__all__ = ["api_v1_router"]
