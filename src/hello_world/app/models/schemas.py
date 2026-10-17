from pydantic import BaseModel,Field

class PresignRequest(BaseModel):
    filename:str = Field(min_length=1,max_length=255)
    content_type:str = Field(min_length=1,max_length=120)
    session_id:str = Field(min_length=1,max_length=120)

class PresignResponse(BaseModel):
    method:str
    upload_url:str
    headers:dict[str,str]
    object_key:str
    public_url:str
    expires_in:int

class ChatRequest(BaseModel):
    message:str = Field(min_length=1,max_length=4000)
    session_id:str = Field(min_length=1,max_length=120)
    image_url:str | None = None

class HistoryMessage(BaseModel):
    role:str
    content:str

class HistoryResponse(BaseModel):
    messages:list[HistoryMessage]

class SuccessResponse(BaseModel):
    success:bool

class SessionItem(BaseModel):
    session_id: str
    title: str


class SessionListResponse(BaseModel):
    sessions: list[SessionItem]


class AuthRequest(BaseModel):
    username:str = Field(
        min_length=1,
        max_length=120,
        pattern=r"^[A-Za-z0-9_\u4e00-\u9fff.-]+$",
    )
    password:str = Field(
        min_length=1,
        max_length=72,
    )

class UserResponse(BaseModel):
    id:str
    username:str
    created_at:str

class PantryItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    quantity: float = Field(gt=0, le=10000)
    unit: str = Field(min_length=1, max_length=20)
    expires_at: str | None = None


class PantryItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    quantity: float | None = Field(default=None, gt=0, le=10000)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    expires_at: str | None = None


class PantryItemResponse(BaseModel):
    id: str
    name: str
    quantity: float
    unit: str
    expires_at: str | None
    created_at: str
    updated_at: str


class PantryListResponse(BaseModel):
    items: list[PantryItemResponse]