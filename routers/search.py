from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.announcement import Announcement
from models.bulletin import Bulletin
from models.coordinator import Coordinator
from models.member import Member
from models.program import ProgramItem
from schemas.common import APIResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=APIResponse[dict])
async def search(
    q: str = "",
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Search across program items, announcements, coordinators, and members."""
    if not q:
        return APIResponse(
            success=True,
            data={"programs": [], "announcements": [], "coordinators": [], "members": []},
        )

    results: dict = {}
    search_term = f"%{q}%"

    # Search program_items
    if not type or type == "programs":
        query = (
            select(ProgramItem, Bulletin.date)
            .join(Bulletin, ProgramItem.bulletin_id == Bulletin.id)
            .where(
                or_(
                    ProgramItem.role.ilike(search_term),
                    ProgramItem.note.ilike(search_term),
                    ProgramItem.person.ilike(search_term),
                )
            )
            .order_by(ProgramItem.bulletin_id.desc())
        )
        result = await db.execute(query)
        rows = result.all()
        results["programs"] = [
            {
                "id": item.id,
                "bulletinId": item.bulletin_id,
                "bulletinDate": date,
                "block": item.block,
                "role": item.role,
                "note": item.note,
                "person": item.person,
            }
            for item, date in rows
        ]

    # Search announcements
    if not type or type == "announcements":
        query = (
            select(Announcement, Bulletin.date)
            .join(Bulletin, Announcement.bulletin_id == Bulletin.id)
            .where(
                or_(
                    Announcement.title.ilike(search_term),
                    Announcement.body.ilike(search_term),
                )
            )
            .order_by(Announcement.bulletin_id.desc())
        )
        result = await db.execute(query)
        rows = result.all()
        results["announcements"] = [
            {
                "id": ann.id,
                "bulletinId": ann.bulletin_id,
                "bulletinDate": date,
                "title": ann.title,
                "body": ann.body,
            }
            for ann, date in rows
        ]

    # Search coordinators
    if not type or type == "coordinators":
        query = (
            select(Coordinator, Bulletin.date)
            .join(Bulletin, Coordinator.bulletin_id == Bulletin.id)
            .where(Coordinator.value.ilike(search_term))
            .order_by(Coordinator.bulletin_id.desc())
        )
        result = await db.execute(query)
        rows = result.all()
        results["coordinators"] = [
            {
                "id": coord.id,
                "bulletinId": coord.bulletin_id,
                "bulletinDate": date,
                "type": coord.type,
                "value": coord.value,
            }
            for coord, date in rows
        ]

    # Search members
    if not type or type == "members":
        query = select(Member).where(Member.name.ilike(search_term)).order_by(Member.name)
        result = await db.execute(query)
        members = result.scalars().all()
        results["members"] = [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "phone": m.phone,
            }
            for m in members
        ]

    return APIResponse(success=True, data=results)
