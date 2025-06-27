from fastapi import APIRouter
from .Sargam.Stage1 import router as stage1

router = APIRouter()

# ✅ Register all routes dynamically
router.include_router(stage1)
#router.include_router(socket_router)
# ✅ API to list available routes
@router.get("/", tags=["Routes"])
async def list_routes():
    return {
        "available_routes": [
            {"name": "Stage1", "url": "/stage1"},
        ]
    }
