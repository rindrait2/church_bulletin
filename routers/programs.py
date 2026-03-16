from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import require_editor
from models.bulletin import Bulletin
from models.program import ProgramItem
from models.user import User
from schemas.bulletin import ProgramItemInFull
from schemas.common import APIResponse
from schemas.program import ProgramItemCreate, ProgramItemRead, ProgramItemUpdate, ReorderItem

router = APIRouter(prefix="/bulletins/{bulletin_id}/programs", tags=["programs"])


async def _check_bulletin(bulletin_id: str, db: AsyncSession):
    bulletin = await db.get(Bulletin, bulletin_id)
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    return bulletin


@router.get("", response_model=APIResponse[dict])
async def list_programs(bulletin_id: str, db: AsyncSession = Depends(get_db)):
    """List program items for a bulletin, grouped by block."""
    await _check_bulletin(bulletin_id, db)
    result = await db.execute(
        select(ProgramItem)
        .where(ProgramItem.bulletin_id == bulletin_id)
        .order_by(ProgramItem.sequence)
    )
    items = result.scalars().all()

    grouped = {"lessonStudy": [], "ssProgram": [], "divineService": []}
    block_map = {
        "lesson_study": "lessonStudy",
        "ss_program": "ssProgram",
        "divine_service": "divineService",
    }
    for item in items:
        key = block_map.get(item.block)
        if key:
            grouped[key].append(
                ProgramItemInFull.model_validate(item, from_attributes=True).model_dump(by_alias=True)
            )

    return APIResponse(success=True, data=grouped)


@router.post("", response_model=APIResponse[ProgramItemRead], status_code=status.HTTP_201_CREATED)
async def create_program(
    bulletin_id: str,
    body: ProgramItemCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Create a new program item for a bulletin."""
    await _check_bulletin(bulletin_id, db)
    item = ProgramItem(
        bulletin_id=bulletin_id,
        block=body.block,
        sequence=body.sequence,
        role=body.role,
        note=body.note,
        person=body.person,
        is_sermon=body.is_sermon,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return APIResponse(
        success=True,
        data=ProgramItemRead.model_validate(item, from_attributes=True),
        message="Program item created",
    )


@router.put("/{item_id}", response_model=APIResponse[ProgramItemRead])
async def update_program(
    bulletin_id: str,
    item_id: int,
    body: ProgramItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Update a program item."""
    await _check_bulletin(bulletin_id, db)
    item = await db.get(ProgramItem, item_id)
    if not item or item.bulletin_id != bulletin_id:
        raise HTTPException(status_code=404, detail="Program item not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    await db.flush()
    await db.refresh(item)
    return APIResponse(
        success=True,
        data=ProgramItemRead.model_validate(item, from_attributes=True),
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    bulletin_id: str,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Delete a program item."""
    await _check_bulletin(bulletin_id, db)
    item = await db.get(ProgramItem, item_id)
    if not item or item.bulletin_id != bulletin_id:
        raise HTTPException(status_code=404, detail="Program item not found")
    await db.delete(item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/reorder", response_model=APIResponse)
async def reorder_programs(
    bulletin_id: str,
    body: list[ReorderItem],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Reorder program items by updating their sequence numbers."""
    await _check_bulletin(bulletin_id, db)
    for item_data in body:
        item = await db.get(ProgramItem, item_data.id)
        if item and item.bulletin_id == bulletin_id:
            item.sequence = item_data.sequence
    await db.flush()
    return APIResponse(success=True, message="Reorder complete")
