from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import require_admin, require_editor
from models.team import Team
from models.user import User
from schemas.common import APIResponse
from schemas.team import TeamCreate, TeamRead, TeamUpdate

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=APIResponse[list[TeamRead]])
async def list_teams(db: AsyncSession = Depends(get_db)):
    """List all teams."""
    result = await db.execute(select(Team).order_by(Team.name))
    items = result.scalars().all()
    return APIResponse(
        success=True,
        data=[TeamRead.model_validate(t, from_attributes=True) for t in items],
    )


@router.post("", response_model=APIResponse[TeamRead], status_code=status.HTTP_201_CREATED)
async def create_team(
    body: TeamCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Create a new team."""
    team = Team(name=body.name, type=body.type, active=body.active)
    db.add(team)
    await db.flush()
    await db.refresh(team)
    return APIResponse(
        success=True,
        data=TeamRead.model_validate(team, from_attributes=True),
        message="Team created",
    )


@router.put("/{team_id}", response_model=APIResponse[TeamRead])
async def update_team(
    team_id: int,
    body: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_editor),
):
    """Update a team."""
    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(team, key, value)
    await db.flush()
    await db.refresh(team)
    return APIResponse(
        success=True,
        data=TeamRead.model_validate(team, from_attributes=True),
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a team."""
    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    await db.delete(team)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
