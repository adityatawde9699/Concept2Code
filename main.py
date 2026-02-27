from fastapi import FastAPI, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from database import engine, Base, get_db
import models
import crud
from ai_logic import recommend_best_slot, calculate_slot_score
from schemas import BookingCreate

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ParkWise")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    # Auto-seed on first run
    if db.query(models.ParkingSlot).count() == 0:
        crud.seed_parking_slots(db)

    slots = crud.get_all_slots(db)
    total_slots = len(slots)
    occupied = len([s for s in slots if s.is_occupied])
    available = total_slots - occupied

    # Group by zone for the progress bars
    zone_stats = {}
    for s in slots:
        z = s.zone
        if z not in zone_stats:
            zone_stats[z] = {"total": 0, "occupied": 0}
        zone_stats[z]["total"] += 1
        if s.is_occupied:
            zone_stats[z]["occupied"] += 1

    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_slots": total_slots,
        "occupied": occupied,
        "available": available,
        "zone_stats": zone_stats,
    })

# ─────────────────────────────────────────
#  Slots Listing
# ─────────────────────────────────────────
@app.get("/slots", response_class=HTMLResponse)
def show_slots(request: Request, zone: Optional[str] = None, db: Session = Depends(get_db)):
    slots = crud.get_all_slots(db)
    zones = sorted(set(s.zone for s in slots))

    slots_with_scores = []
    for s in slots:
        if zone and s.zone != zone:
            continue
        entry = {c.name: getattr(s, c.name) for c in s.__table__.columns}
        entry["score"] = calculate_slot_score(s)
        slots_with_scores.append(entry)

    return templates.TemplateResponse("slots.html", {
        "request": request,
        "slots": slots_with_scores,
        "zones": zones,
        "active_zone": zone,
    })

# ─────────────────────────────────────────
#  AI Recommendation
# ─────────────────────────────────────────
@app.get("/recommended", response_class=HTMLResponse)
def get_recommended(request: Request, db: Session = Depends(get_db)):
    slots = crud.get_all_slots(db)
    best_slot = recommend_best_slot(slots)
    score = calculate_slot_score(best_slot) if best_slot else 0

    return templates.TemplateResponse("recommendation.html", {
        "request": request,
        "best_slot": best_slot,
        "score": score,
    })

# ─────────────────────────────────────────
#  Booking Form
# ─────────────────────────────────────────
@app.get("/booking/{slot_id}", response_class=HTMLResponse)
def booking_form(slot_id: int, request: Request, db: Session = Depends(get_db)):
    slot = crud.get_slot_by_id(db, slot_id)
    now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
    return templates.TemplateResponse("booking.html", {
        "request": request,
        "slot": slot,
        "now_str": now_str,
    })

@app.post("/booking/{slot_id}", response_class=HTMLResponse)
def confirm_booking(
    slot_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_name: str = Form(...),
    phone_number: str = Form(""),
    vehicle_type: str = Form("Car"),
    vehicle_number: str = Form(""),
    start_time: str = Form(...),
    end_time: str = Form(""),
):
    # Parse datetimes
    try:
        start_dt = datetime.fromisoformat(start_time)
    except Exception:
        start_dt = datetime.utcnow()

    end_dt = None
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time)
        except Exception:
            end_dt = None

    booking_data = BookingCreate(
        slot_id=slot_id,
        user_name=user_name,
        phone_number=phone_number or None,
        vehicle_type=vehicle_type or None,
        vehicle_number=vehicle_number or None,
        start_time=start_dt,
        end_time=end_dt,
    )
    booking = crud.create_booking(db, booking_data)
    return RedirectResponse(url=f"/booking/confirm/{booking.id}", status_code=303)

# ─────────────────────────────────────────
#  Booking Confirmation Page
# ─────────────────────────────────────────
@app.get("/booking/confirm/{booking_id}", response_class=HTMLResponse)
def booking_confirmation(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = crud.get_booking_by_id(db, booking_id)
    return templates.TemplateResponse("confirmation.html", {
        "request": request,
        "booking": booking,
    })

# ─────────────────────────────────────────
#  End Booking / Check Out
# ─────────────────────────────────────────
@app.post("/end-booking/{booking_id}")
def end_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = crud.end_booking(db, booking_id)
    if booking:
        return {"status": "success", "booking_id": booking.id, "total_cost": booking.total_cost}
    return {"status": "error", "message": "Booking not found"}

# ─────────────────────────────────────────
#  History
# ─────────────────────────────────────────
@app.get("/history", response_class=HTMLResponse)
def booking_history(request: Request, db: Session = Depends(get_db)):
    bookings = crud.get_booking_history(db)
    return templates.TemplateResponse("history.html", {
        "request": request,
        "bookings": bookings,
    })

# ─────────────────────────────────────────
#  Seed Data (also auto-runs on /)
# ─────────────────────────────────────────
@app.get("/seed", response_class=HTMLResponse)
def seed_data(request: Request, db: Session = Depends(get_db)):
    count = crud.seed_parking_slots(db)
    return RedirectResponse(url=f"/?seeded={count}", status_code=303)

# ─────────────────────────────────────────
#  JSON API
# ─────────────────────────────────────────
@app.get("/api/slots")
def api_slots(db: Session = Depends(get_db)):
    slots = crud.get_all_slots(db)
    return [
        {
            "id": s.id,
            "slot_number": s.slot_number,
            "zone": s.zone,
            "is_occupied": s.is_occupied,
            "price_per_hour": s.price_per_hour,
        }
        for s in slots
    ]
