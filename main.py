from fastapi import FastAPI, Depends, Form, Request, Cookie
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
from mock_auth import (
    create_mock_user, authenticate_user, get_user_by_email,
    update_user_vehicle, create_session, get_session_user
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ParkWise")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─────────────────────────────────────────
#  Login / Auth Helpers
# ─────────────────────────────────────────

def get_current_user(session_id: Optional[str] = Cookie(None)):
    if session_id:
        return get_session_user(session_id)
    return None

# ─────────────────────────────────────────
#  Login Page
# ─────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), name: str = Form(...)):
    user = get_user_by_email(email)
    if not user:
        user = create_mock_user(name, email)
    else:
        # Reset vehicle type on new login to force selection
        update_user_vehicle(email, None)
    
    session_id = create_session(email)
    response = RedirectResponse(url="/vehicle-type", status_code=303)
    response.set_cookie("session_id", session_id, max_age=86400)
    return response

# ─────────────────────────────────────────
#  Vehicle Type Selection
# ─────────────────────────────────────────
@app.get("/vehicle-type", response_class=HTMLResponse)
def vehicle_type_page(request: Request, session_id: Optional[str] = Cookie(None)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    if user.vehicle_type:
        return RedirectResponse(url="/find-parking", status_code=303)
    
    return templates.TemplateResponse("vehicle-type.html", {
        "request": request,
        "user": user
    })

@app.post("/vehicle-type", response_class=HTMLResponse)
def set_vehicle_type(request: Request, session_id: Optional[str] = Cookie(None), vehicle_type: str = Form(...)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    update_user_vehicle(user.email, vehicle_type)
    return RedirectResponse(url="/home", status_code=303)

# ─────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────
@app.get("/home", response_class=HTMLResponse)
def home_dashboard(request: Request, session_id: Optional[str] = Cookie(None)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,
    })

# ─────────────────────────────────────────
#  List Parking Feature
# ─────────────────────────────────────────
@app.get("/list-parking", response_class=HTMLResponse)
def list_parking_form(request: Request, session_id: Optional[str] = Cookie(None)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
    return templates.TemplateResponse("list-parking.html", {
        "request": request,
        "user": user,
        "now_str": now_str,
    })

@app.post("/list-parking", response_class=HTMLResponse)
def create_parking_listing(
    request: Request,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
    title: str = Form(...),
    location: str = Form(...),
    price_per_hour: float = Form(...),
    available_from: str = Form(...),
    available_to: str = Form(""),
    description: str = Form(""),
):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    try:
        available_from_dt = datetime.fromisoformat(available_from)
    except Exception:
        available_from_dt = datetime.utcnow()
    
    available_to_dt = None
    if available_to:
        try:
            available_to_dt = datetime.fromisoformat(available_to)
        except Exception:
            available_to_dt = None
    
    # Create listing
    new_listing = models.UserListing(
        user_email=user.email,
        title=title,
        location=location,
        price_per_hour=price_per_hour,
        available_from=available_from_dt,
        available_to=available_to_dt,
        description=description,
    )
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    
    return RedirectResponse(url="/listing-success", status_code=303)

@app.get("/listing-success", response_class=HTMLResponse)
def listing_success(request: Request, session_id: Optional[str] = Cookie(None)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("listing-success.html", {
        "request": request,
        "user": user,
    })

# ─────────────────────────────────────────
#  Slots Listing
# ─────────────────────────────────────────
@app.get("/find-parking", response_class=HTMLResponse)
def find_parking(request: Request, session_id: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Auto-seed on first run
    if db.query(models.ParkingSlot).count() == 0:
        crud.seed_parking_slots(db)
    
    slots = crud.get_all_slots(db)
    
    # Calculate scores for all slots
    slots_with_scores = []
    for s in slots:
        entry = {c.name: getattr(s, c.name) for c in s.__table__.columns}
        entry["score"] = calculate_slot_score(s)
        slots_with_scores.append(entry)
    
    # Get top 3 recommendations (only available slots)
    available_slots = [s for s in slots_with_scores if not s["is_occupied"]]
    top_3 = sorted(available_slots, key=lambda x: x["score"], reverse=True)[:3]
    
    # Get all available slots grouped by zone
    all_available = available_slots
    zones = sorted(set(s["zone"] for s in all_available))
    
    return templates.TemplateResponse("find-parking.html", {
        "request": request,
        "user": user,
        "top_recommendations": top_3,
        "all_available": all_available,
        "zones": zones,
    })

@app.get("/slots", response_class=HTMLResponse)
def show_all_slots(request: Request, session_id: Optional[str] = Cookie(None), zone: Optional[str] = None, db: Session = Depends(get_db)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
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
        "user": user,
        "slots": slots_with_scores,
        "zones": zones,
        "active_zone": zone,
    })

@app.get("/booking/{slot_id}", response_class=HTMLResponse)
def booking_form(slot_id: int, request: Request, session_id: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    slot = crud.get_slot_by_id(db, slot_id)
    now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
    return templates.TemplateResponse("booking.html", {
        "request": request,
        "user": user,
        "slot": slot,
        "now_str": now_str,
    })

@app.post("/booking/{slot_id}", response_class=HTMLResponse)
def confirm_booking(
    slot_id: int,
    request: Request,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
    user_name: str = Form(...),
    phone_number: str = Form(""),
    vehicle_type: str = Form("Car"),
    vehicle_number: str = Form(""),
    start_time: str = Form(...),
    end_time: str = Form(""),
):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
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

@app.get("/booking/confirm/{booking_id}", response_class=HTMLResponse)
def booking_confirmation(booking_id: int, request: Request, session_id: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    booking = crud.get_booking_by_id(db, booking_id)
    return templates.TemplateResponse("confirmation.html", {
        "request": request,
        "user": user,
        "booking": booking,
    })

@app.post("/end-booking/{booking_id}")
def end_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = crud.end_booking(db, booking_id)
    if booking:
        return {"status": "success", "booking_id": booking.id, "total_cost": booking.total_cost}
    return {"status": "error", "message": "Booking not found"}

@app.get("/history", response_class=HTMLResponse)
def booking_history(request: Request, session_id: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    user = get_session_user(session_id)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    bookings = crud.get_booking_history(db)
    return templates.TemplateResponse("history.html", {
        "request": request,
        "user": user,
        "bookings": bookings,
    })

@app.get("/logout", response_class=HTMLResponse)
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_id")
    return response

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
