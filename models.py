from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class ParkingSlot(Base):
    __tablename__ = "parking_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String, unique=True, index=True)
    is_occupied = Column(Boolean, default=False)
    zone = Column(String)
    last_occupied_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bookings = relationship("Booking", back_populates="slot")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"))
    user_name = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    
    slot = relationship("ParkingSlot", back_populates="bookings")
