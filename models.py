from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class ParkingSlot(Base):
    __tablename__ = "parking_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String, unique=True, index=True)
    is_occupied = Column(Boolean, default=False)
    zone = Column(String)
    price_per_hour = Column(Float, default=50.0)
    vehicle_types = Column(String, default="Car,Bike,SUV")  # comma-separated
    last_occupied_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bookings = relationship("Booking", back_populates="slot")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"))
    user_name = Column(String)
    phone_number = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)
    vehicle_number = Column(String, nullable=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    total_cost = Column(Float, nullable=True)
    status = Column(String, default="active")  # active | completed
    
    slot = relationship("ParkingSlot", back_populates="bookings")

class UserListing(Base):
    __tablename__ = "user_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    title = Column(String)
    location = Column(String)
    price_per_hour = Column(Float)
    available_from = Column(DateTime)
    available_to = Column(DateTime, nullable=True)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
