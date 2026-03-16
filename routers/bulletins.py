from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from dependencies import require_admin, require_editor
from models.announcement import Announcement
from models.bulletin import Bulletin
from models.coordinator import Coordinator
from models.program import ProgramItem
from models.user import User
from schemas.bulletin import (
    AnnouncementInFull,
    BulletinCreate,
    BulletinFull,
    BulletinRead,
    BulletinUpdate,
    ProgramGrouped,
    ProgramItemInFull,
)
from schemas.common import APIResponse, Meta

router = APIRouter(prefix="/bulletins", tags=["bulletins"])


@router.get("", response_model=APIResponse[list[BulletinRead]])
async def list_bulletins(
    limit: int = 10,
    offset: int = 0,
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    """List all bulletins with pagination."""
    count_result = await db.execute(select(func.count(Bulletin.id)))
    total = count_result.scalar() or 0

    query = select(Bulletin)
    if order == "asc":
        query = query.order_by(Bulletin.id.asc())
    else:
        query = query.order_by(Bulletin.id.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    bulletins = result.scalars().all()

    data = [
        BulletinRead.model_validate(b, from_attributes=True)
        for b in bulletins
    ]
    return APIResponse(
        success=True,
        data=data,
        meta=Meta(total=total, limit=limit, offset=offset),
    )


@router.post("", response_model=APIResponse[BulletinRead], status_code=status.HTTP_201_CREATED)
async def create_bulletin(
    body: BulletinCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Create a new bulletin."""
    existing = await db.get(Bulletin, body.id)
    if existing:
        raise HTTPException(status_code=409, detail="Bulletin already exists")
    bulletin = Bulletin(
        id=body.id,
        date=body.date,
        lesson_code=body.lesson_code,
        lesson_title=body.lesson_title,
        sabbath_ends=body.sabbath_ends,
        next_sabbath=body.next_sabbath,
    )
    db.add(bulletin)
    await db.flush()
    await db.refresh(bulletin)
    return APIResponse(
        success=True,
        data=BulletinRead.model_validate(bulletin, from_attributes=True),
        message="Bulletin created",
    )


@router.get("/{bulletin_id}", response_model=APIResponse[BulletinRead])
async def get_bulletin(bulletin_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single bulletin by ID (header only)."""
    bulletin = await db.get(Bulletin, bulletin_id)
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    return APIResponse(
        success=True,
        data=BulletinRead.model_validate(bulletin, from_attributes=True),
    )


@router.put("/{bulletin_id}", response_model=APIResponse[BulletinRead])
async def update_bulletin(
    bulletin_id: str,
    body: BulletinUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Update a bulletin."""
    bulletin = await db.get(Bulletin, bulletin_id)
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bulletin, key, value)
    await db.flush()
    await db.refresh(bulletin)
    return APIResponse(
        success=True,
        data=BulletinRead.model_validate(bulletin, from_attributes=True),
    )


@router.delete("/{bulletin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bulletin(
    bulletin_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a bulletin and all its related data."""
    bulletin = await db.get(Bulletin, bulletin_id)
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    await db.delete(bulletin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{bulletin_id}/full", response_model=APIResponse[BulletinFull])
async def get_bulletin_full(bulletin_id: str, db: AsyncSession = Depends(get_db)):
    """Get a complete bulletin with all subcollections (programs, coordinators, announcements)."""
    result = await db.execute(
        select(Bulletin)
        .where(Bulletin.id == bulletin_id)
        .options(
            selectinload(Bulletin.program_items),
            selectinload(Bulletin.coordinators),
            selectinload(Bulletin.announcements),
        )
    )
    bulletin = result.scalar_one_or_none()
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")

    # Group program items by block
    lesson_study = []
    ss_program = []
    divine_service = []
    for item in sorted(bulletin.program_items, key=lambda x: x.sequence):
        pi = ProgramItemInFull.model_validate(item, from_attributes=True)
        if item.block == "lesson_study":
            lesson_study.append(pi)
        elif item.block == "ss_program":
            ss_program.append(pi)
        elif item.block == "divine_service":
            divine_service.append(pi)

    # Build coordinators dict
    coordinators = {}
    for c in bulletin.coordinators:
        coordinators[c.type] = c.value or ""

    # Build announcements list
    announcements = [
        AnnouncementInFull.model_validate(a, from_attributes=True)
        for a in sorted(bulletin.announcements, key=lambda x: x.sequence)
    ]

    data = BulletinFull(
        id=bulletin.id,
        date=bulletin.date,
        lesson_code=bulletin.lesson_code,
        lesson_title=bulletin.lesson_title,
        sabbath_ends=bulletin.sabbath_ends,
        next_sabbath=bulletin.next_sabbath,
        program=ProgramGrouped(
            lesson_study=lesson_study,
            ss_program=ss_program,
            divine_service=divine_service,
        ),
        coordinators=coordinators,
        announcements=announcements,
    )
    return APIResponse(success=True, data=data)
