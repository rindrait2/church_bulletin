from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import require_editor
from models.announcement import Announcement
from models.bulletin import Bulletin
from models.user import User
from schemas.announcement import AnnouncementCreate, AnnouncementRead, AnnouncementUpdate
from schemas.common import APIResponse

router = APIRouter(prefix="/bulletins/{bulletin_id}/announcements", tags=["announcements"])


async def _check_bulletin(bulletin_id: str, db: AsyncSession):
    bulletin = await db.get(Bulletin, bulletin_id)
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin not found")
    return bulletin


@router.get("", response_model=APIResponse[list[AnnouncementRead]])
async def list_announcements(bulletin_id: str, db: AsyncSession = Depends(get_db)):
    """List all announcements for a bulletin."""
    await _check_bulletin(bulletin_id, db)
    result = await db.execute(
        select(Announcement)
        .where(Announcement.bulletin_id == bulletin_id)
        .order_by(Announcement.sequence)
    )
    items = result.scalars().all()
    return APIResponse(
        success=True,
        data=[AnnouncementRead.model_validate(a, from_attributes=True) for a in items],
    )


@router.post("", response_model=APIResponse[AnnouncementRead], status_code=status.HTTP_201_CREATED)
async def create_announcement(
    bulletin_id: str,
    body: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Create a new announcement for a bulletin."""
    await _check_bulletin(bulletin_id, db)
    ann = Announcement(
        bulletin_id=bulletin_id,
        sequence=body.sequence,
        title=body.title,
        body=body.body,
        recurring=body.recurring,
        pinned=body.pinned,
    )
    db.add(ann)
    await db.flush()
    await db.refresh(ann)
    return APIResponse(
        success=True,
        data=AnnouncementRead.model_validate(ann, from_attributes=True),
        message="Announcement created",
    )


@router.put("/{ann_id}", response_model=APIResponse[AnnouncementRead])
async def update_announcement(
    bulletin_id: str,
    ann_id: int,
    body: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Update an announcement."""
    await _check_bulletin(bulletin_id, db)
    ann = await db.get(Announcement, ann_id)
    if not ann or ann.bulletin_id != bulletin_id:
        raise HTTPException(status_code=404, detail="Announcement not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ann, key, value)
    await db.flush()
    await db.refresh(ann)
    return APIResponse(
        success=True,
        data=AnnouncementRead.model_validate(ann, from_attributes=True),
    )


@router.delete("/{ann_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    bulletin_id: str,
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Delete an announcement."""
    await _check_bulletin(bulletin_id, db)
    ann = await db.get(Announcement, ann_id)
    if not ann or ann.bulletin_id != bulletin_id:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await db.delete(ann)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
