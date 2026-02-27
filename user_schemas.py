from pydantic import BaseModel
from typing import Optional

class UserProfile(BaseModel):
    name: str
    email: str
    vehicle_type: str
    
    class Config:
        from_attributes = True
