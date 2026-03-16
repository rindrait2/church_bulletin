from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import require_editor
from models.bulletin import Bulletin
from models.coordinator import Coordinator
from models.user import User
from schemas.common import APIResponse
from schemas.coordinator import CoordinatorRead, CoordinatorUpdate

router = APIRouter(tags=["coordinators"])


@router.get(
    "/bulletins/{bulletin_id}/coordinators",
    response_model=APIResponse[list[CoordinatorRead]],
)
async def list_coordinators(bulletin_id: str, db: AsyncSession = Depends(get_db)):
    """List all coordinators for a bulletin."""
    bulletin = await db.get(Bulletin, bulletin_id)
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    result = await db.execute(
        select(Coordinator).where(Coordinator.bulletin_id == bulletin_id)
    )
    items = result.scalars().all()
    return APIResponse(
        success=True,
        data=[CoordinatorRead.model_validate(c, from_attributes=True) for c in items],
    )


@router.put(
    "/bulletins/{bulletin_id}/coordinators/{coord_type}",
    response_model=APIResponse[CoordinatorRead],
)
async def upsert_coordinator(
    bulletin_id: str,
    coord_type: str,
    body: CoordinatorUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Create or update a coordinator entry for a bulletin."""
    bulletin = await db.get(Bulletin, bulletin_id)
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    result = await db.execute(
        select(Coordinator).where(
            Coordinator.bulletin_id == bulletin_id,
            Coordinator.type == coord_type,
        )
    )
    coord = result.scalar_one_or_none()
    if coord:
        coord.value = body.value
    else:
        coord = Coordinator(
            bulletin_id=bulletin_id, type=coord_type, value=body.value
        )
        db.add(coord)
    await db.flush()
    await db.refresh(coord)
    return APIResponse(
        success=True,
        data=CoordinatorRead.model_validate(coord, from_attributes=True),
    )


@router.get("/coordinators", response_model=APIResponse[list[dict]])
async def coordinators_range(
    db: AsyncSession = Depends(get_db),
    from_date: str | None = None,
    to: str | None = None,
):
    """Get coordinators across a range of bulletins by date."""
    query = (
        select(Coordinator, Bulletin.date)
        .join(Bulletin, Coordinator.bulletin_id == Bulletin.id)
    )
    if from_date:
        query = query.where(Bulletin.id >= from_date)
    if to:
        query = query.where(Bulletin.id <= to)
    query = query.order_by(Bulletin.id)

    result = await db.execute(query)
    rows = result.all()

    data = []
    for coord, bulletin_date in rows:
        data.append({
            "id": coord.id,
            "bulletinId": coord.bulletin_id,
            "bulletinDate": bulletin_date,
            "type": coord.type,
            "value": coord.value,
        })
    return APIResponse(success=True, data=data)
