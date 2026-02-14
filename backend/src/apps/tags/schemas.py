from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class TagBase(BaseModel):
    name: str
    type: str = "other" # lighting, subject, location, other

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: str
    count: int

    model_config = ConfigDict(from_attributes=True)

class TagUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    count: Optional[int] = None
