from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import require_admin, require_editor
from models.group import Group
from models.user import User
from schemas.common import APIResponse
from schemas.group import GroupCreate, GroupRead, GroupUpdate

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=APIResponse[list[GroupRead]])
async def list_groups(db: AsyncSession = Depends(get_db)):
    """List all groups."""
    result = await db.execute(select(Group).order_by(Group.name))
    items = result.scalars().all()
    return APIResponse(
        success=True,
        data=[GroupRead.model_validate(g, from_attributes=True) for g in items],
    )


@router.post("", response_model=APIResponse[GroupRead], status_code=status.HTTP_201_CREATED)
async def create_group(
    body: GroupCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Create a new group."""
    group = Group(name=body.name, type=body.type, active=body.active)
    db.add(group)
    await db.flush()
    await db.refresh(group)
    return APIResponse(
        success=True,
        data=GroupRead.model_validate(group, from_attributes=True),
        message="Group created",
    )


@router.put("/{group_id}", response_model=APIResponse[GroupRead])
async def update_group(
    group_id: int,
    body: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Update a group."""
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    await db.flush()
    await db.refresh(group)
    return APIResponse(
        success=True,
        data=GroupRead.model_validate(group, from_attributes=True),
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a group."""
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
