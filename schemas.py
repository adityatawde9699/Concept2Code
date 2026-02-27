from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SlotResponse(BaseModel):
    id: int
    slot_number: str
    is_occupied: bool
    zone: str
    price_per_hour: float
    vehicle_types: str
    last_occupied_time: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    slot_id: int
    user_name: str
    phone_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None

class BookingResponse(BaseModel):
    id: int
    slot_id: int
    user_name: str
    phone_number: Optional[str]
    vehicle_type: Optional[str]
    vehicle_number: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    total_cost: Optional[float]
    status: str
    
    class Config:
        from_attributes = True

class BookingWithSlot(BookingResponse):
    slot: SlotResponse
