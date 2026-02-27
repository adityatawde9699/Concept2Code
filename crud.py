from sqlalchemy.orm import Session
from models import ParkingSlot, Booking
from schemas import BookingCreate
from datetime import datetime

def get_all_slots(db: Session):
    return db.query(ParkingSlot).all()

def get_available_slots(db: Session):
    return db.query(ParkingSlot).filter(ParkingSlot.is_occupied == False).all()

def get_slot_by_id(db: Session, slot_id: int):
    return db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()

def create_booking(db: Session, booking: BookingCreate):
    slot = get_slot_by_id(db, booking.slot_id)
    
    # Calculate cost
    total_cost = None
    if booking.end_time and slot:
        duration_hours = (booking.end_time - booking.start_time).total_seconds() / 3600
        total_cost = round(duration_hours * slot.price_per_hour, 2)
    
    if slot:
        slot.is_occupied = True
        slot.last_occupied_time = booking.start_time
    
    db_booking = Booking(
        slot_id=booking.slot_id,
        user_name=booking.user_name,
        phone_number=booking.phone_number,
        vehicle_type=booking.vehicle_type,
        vehicle_number=booking.vehicle_number,
        start_time=booking.start_time,
        end_time=booking.end_time,
        total_cost=total_cost,
        status="active"
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def end_booking(db: Session, booking_id: int):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking:
        end_time = datetime.utcnow()
        booking.end_time = end_time
        booking.status = "completed"
        slot = get_slot_by_id(db, booking.slot_id)
        if slot:
            slot.is_occupied = False
            # Recalculate cost based on actual time
            duration_hours = (end_time - booking.start_time).total_seconds() / 3600
            booking.total_cost = round(duration_hours * slot.price_per_hour, 2)
        db.commit()
    return booking

def get_booking_by_id(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()

def get_booking_history(db: Session, limit: int = 50):
    return db.query(Booking).order_by(Booking.start_time.desc()).limit(limit).all()

def seed_parking_slots(db: Session):
    """Seed demo parking data if DB is empty."""
    existing = db.query(ParkingSlot).count()
    if existing > 0:
        return existing
    
    zones = {
        "A": {"price": 80.0, "count": 6, "label": "Premium"},
        "B": {"price": 50.0, "count": 8, "label": "Standard"},
        "C": {"price": 30.0, "count": 6, "label": "Economy"},
    }
    
    count = 0
    for zone, config in zones.items():
        for i in range(1, config["count"] + 1):
            slot = ParkingSlot(
                slot_number=f"{zone}{i:02d}",
                zone=zone,
                price_per_hour=config["price"],
                vehicle_types="Car,Bike,SUV",
                is_occupied=(i % 3 == 0),  # some occupied for demo
            )
            db.add(slot)
            count += 1
    
    db.commit()
    return count
