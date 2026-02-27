from sqlalchemy.orm import Session
from models import ParkingSlot, Booking
from schemas import BookingCreate

def get_all_slots(db: Session):
    return db.query(ParkingSlot).all()

def get_available_slots(db: Session):
    return db.query(ParkingSlot).filter(ParkingSlot.is_occupied == False).all()

def get_slot_by_id(db: Session, slot_id: int):
    return db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()

def create_booking(db: Session, booking: BookingCreate):
    slot = get_slot_by_id(db, booking.slot_id)
    if slot:
        slot.is_occupied = True
        slot.last_occupied_time = booking.start_time
    
    db_booking = Booking(
        slot_id=booking.slot_id,
        user_name=booking.user_name,
        start_time=booking.start_time
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def end_booking(db: Session, booking_id: int, end_time):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking:
        booking.end_time = end_time
        slot = get_slot_by_id(db, booking.slot_id)
        if slot:
            slot.is_occupied = False
        db.commit()
    return booking

def get_booking_history(db: Session, limit: int = 10):
    return db.query(Booking).order_by(Booking.start_time.desc()).limit(limit).all()
