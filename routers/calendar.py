from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import require_admin
from models.calendar_event import CalendarEvent
from models.user import User
from schemas.calendar_event import CalendarEventCreate, CalendarEventRead, CalendarEventUpdate
from schemas.common import APIResponse

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("", response_model=APIResponse[list[CalendarEventRead]])
async def list_calendar(db: AsyncSession = Depends(get_db)):
    """List all active recurring calendar events."""
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.active == True).order_by(CalendarEvent.id)
    )
    items = result.scalars().all()
    return APIResponse(
        success=True,
        data=[CalendarEventRead.model_validate(e, from_attributes=True) for e in items],
    )


@router.post("", response_model=APIResponse[CalendarEventRead], status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    body: CalendarEventCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Create a new calendar event."""
    event = CalendarEvent(
        day=body.day,
        time=body.time,
        name=body.name,
        location=body.location,
        active=body.active,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return APIResponse(
        success=True,
        data=CalendarEventRead.model_validate(event, from_attributes=True),
        message="Calendar event created",
    )


@router.put("/{event_id}", response_model=APIResponse[CalendarEventRead])
async def update_calendar_event(
    event_id: int,
    body: CalendarEventUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Update a calendar event."""
    event = await db.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    await db.flush()
    await db.refresh(event)
    return APIResponse(
        success=True,
        data=CalendarEventRead.model_validate(event, from_attributes=True),
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a calendar event."""
    event = await db.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    await db.delete(event)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
