from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import require_admin
from models.contact import Contact
from models.user import User
from schemas.common import APIResponse
from schemas.contact import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=APIResponse[list[ContactRead]])
async def list_contacts(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all contacts, optionally filtered by category."""
    query = select(Contact).order_by(Contact.display_order, Contact.id)
    if category:
        query = query.where(Contact.category == category)
    result = await db.execute(query)
    items = result.scalars().all()
    return APIResponse(
        success=True,
        data=[ContactRead.model_validate(c, from_attributes=True) for c in items],
    )


@router.post("", response_model=APIResponse[ContactRead], status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Create a new contact."""
    contact = Contact(
        name=body.name,
        category=body.category,
        email=body.email,
        phone=body.phone,
        display_order=body.display_order,
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return APIResponse(
        success=True,
        data=ContactRead.model_validate(contact, from_attributes=True),
        message="Contact created",
    )


@router.put("/{contact_id}", response_model=APIResponse[ContactRead])
async def update_contact(
    contact_id: int,
    body: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Update a contact."""
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)
    await db.flush()
    await db.refresh(contact)
    return APIResponse(
        success=True,
        data=ContactRead.model_validate(contact, from_attributes=True),
    )


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a contact."""
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    await db.delete(contact)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
