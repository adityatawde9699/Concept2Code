from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SlotResponse(BaseModel):
    id: int
    slot_number: str
    is_occupied: bool
    zone: str
    last_occupied_time: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    slot_id: int
    user_name: str
    start_time: datetime

class BookingResponse(BaseModel):
    id: int
    slot_id: int
    user_name: str
    start_time: datetime
    end_time: Optional[datetime]
    
    class Config:
        from_attributes = True

class BookingWithSlot(BookingResponse):
    slot: SlotResponse
