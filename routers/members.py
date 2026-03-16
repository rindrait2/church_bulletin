from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from dependencies import require_admin, require_editor
from models.member import Member, MemberRole
from models.program import ProgramItem
from models.user import User
from schemas.common import APIResponse, Meta
from schemas.member import MemberCreate, MemberRead, MemberUpdate
from schemas.program import ProgramItemRead

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=APIResponse[list[MemberRead]])
async def list_members(
    role: str | None = None,
    active: bool | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """List members with optional filters for role, active status, and name search."""
    query = select(Member).options(selectinload(Member.roles))
    count_query = select(func.count(Member.id))

    if active is not None:
        query = query.where(Member.active == active)
        count_query = count_query.where(Member.active == active)
    if q:
        query = query.where(Member.name.ilike(f"%{q}%"))
        count_query = count_query.where(Member.name.ilike(f"%{q}%"))
    if role:
        query = query.join(MemberRole).where(MemberRole.role == role)
        count_query = count_query.join(MemberRole).where(MemberRole.role == role)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Member.name).limit(limit).offset(offset)
    result = await db.execute(query)
    members = result.scalars().unique().all()

    return APIResponse(
        success=True,
        data=[MemberRead.model_validate(m, from_attributes=True) for m in members],
        meta=Meta(total=total, limit=limit, offset=offset),
    )


@router.post("", response_model=APIResponse[MemberRead], status_code=status.HTTP_201_CREATED)
async def create_member(
    body: MemberCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Create a new member."""
    member = Member(
        name=body.name,
        email=body.email,
        phone=body.phone,
        active=body.active,
    )
    db.add(member)
    await db.flush()
    for role_name in body.roles:
        db.add(MemberRole(member_id=member.id, role=role_name))
    await db.flush()
    await db.refresh(member)
    result = await db.execute(
        select(Member).where(Member.id == member.id).options(selectinload(Member.roles))
    )
    member = result.scalar_one()
    return APIResponse(
        success=True,
        data=MemberRead.model_validate(member, from_attributes=True),
        message="Member created",
    )


@router.get("/{member_id}", response_model=APIResponse[MemberRead])
async def get_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Get a single member by ID."""
    result = await db.execute(
        select(Member).where(Member.id == member_id).options(selectinload(Member.roles))
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return APIResponse(
        success=True,
        data=MemberRead.model_validate(member, from_attributes=True),
    )


@router.put("/{member_id}", response_model=APIResponse[MemberRead])
async def update_member(
    member_id: int,
    body: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Update a member."""
    result = await db.execute(
        select(Member).where(Member.id == member_id).options(selectinload(Member.roles))
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    update_data = body.model_dump(exclude_unset=True)
    roles_data = update_data.pop("roles", None)
    for key, value in update_data.items():
        setattr(member, key, value)
    if roles_data is not None:
        # Clear existing roles and add new ones
        for r in member.roles:
            await db.delete(r)
        await db.flush()
        for role_name in roles_data:
            db.add(MemberRole(member_id=member.id, role=role_name))
    await db.flush()
    await db.refresh(member)
    result = await db.execute(
        select(Member).where(Member.id == member.id).options(selectinload(Member.roles))
    )
    member = result.scalar_one()
    return APIResponse(
        success=True,
        data=MemberRead.model_validate(member, from_attributes=True),
    )


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a member."""
    member = await db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{member_id}/history", response_model=APIResponse[list[ProgramItemRead]])
async def member_history(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Get all program items assigned to this member (matched by name)."""
    member = await db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    result = await db.execute(
        select(ProgramItem)
        .where(ProgramItem.person.ilike(f"%{member.name}%"))
        .order_by(ProgramItem.bulletin_id.desc(), ProgramItem.sequence)
    )
    items = result.scalars().all()
    return APIResponse(
        success=True,
        data=[ProgramItemRead.model_validate(i, from_attributes=True) for i in items],
    )
