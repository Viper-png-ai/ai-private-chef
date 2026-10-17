from fastapi import APIRouter, Depends, HTTPException, status

from hello_world.app.api.dependencies import get_current_user
from hello_world.app.models.schemas import (
    PantryItemCreate,
    PantryItemResponse,
    PantryItemUpdate,
    PantryListResponse,
    SuccessResponse,
)
from hello_world.app.services.pantry import (
    create_pantry_item,
    delete_pantry_item,
    list_pantry_items,
    update_pantry_item,
)


router = APIRouter(prefix="/pantry", tags=["pantry"])

@router.get("", response_model=PantryListResponse)
def get_pantry(
    user: dict[str, str] = Depends(get_current_user),
) -> PantryListResponse:
    return PantryListResponse(
        items=list_pantry_items(user["id"]),
    )

@router.post(
    "",
    response_model=PantryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_pantry_item(
    payload: PantryItemCreate,
    user: dict[str, str] = Depends(get_current_user),
) -> PantryItemResponse:
    item = create_pantry_item(
        user_id=user["id"],
        name=payload.name,
        quantity=payload.quantity,
        unit=payload.unit,
        expires_at=payload.expires_at,
    )
    return PantryItemResponse(**item)


@router.patch(
    "/{item_id}",
    response_model=PantryItemResponse,
)
def change_pantry_item(
    item_id: str,
    payload: PantryItemUpdate,
    user: dict[str, str] = Depends(get_current_user),
) -> PantryItemResponse:
    item = update_pantry_item(
        user_id=user["id"],
        item_id=item_id,
        changes=payload.model_dump(exclude_unset=True),
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="食材不存在。",
        )

    return PantryItemResponse(**item)


@router.delete(
    "/{item_id}",
    response_model=SuccessResponse,
)
def remove_pantry_item(
    item_id: str,
    user: dict[str, str] = Depends(get_current_user),
) -> SuccessResponse:
    deleted = delete_pantry_item(
        user_id=user["id"],
        item_id=item_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="食材不存在。",
        )

    return SuccessResponse(success=True)