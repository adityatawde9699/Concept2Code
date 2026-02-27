from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session
from datetime import datetime

from database import engine, Base, get_db
import models
import crud
from ai_logic import recommend_best_slot, calculate_slot_score

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    slots = crud.get_all_slots(db)
    total_slots = len(slots)
    occupied = len([s for s in slots if s.is_occupied])
    available = total_slots - occupied
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_slots": total_slots,
        "occupied": occupied,
        "available": available
    })

@app.get("/slots", response_class=HTMLResponse)
def show_slots(request: Request, db: Session = Depends(get_db)):
    slots = crud.get_all_slots(db)
    slots_with_scores = [
        {**{c.name: getattr(s, c.name) for c in s.__table__.columns}, 
         "score": calculate_slot_score(s)} 
        for s in slots
    ]
    
    return templates.TemplateResponse("slots.html", {
        "request": request,
        "slots": slots_with_scores
    })

@app.get("/recommended", response_class=HTMLResponse)
def get_recommended(request: Request, db: Session = Depends(get_db)):
    slots = crud.get_all_slots(db)
    best_slot = recommend_best_slot(slots)
    
    return templates.TemplateResponse("recommendation.html", {
        "request": request,
        "best_slot": best_slot
    })

@app.get("/booking/{slot_id}", response_class=HTMLResponse)
def booking_form(slot_id: int, request: Request, db: Session = Depends(get_db)):
    slot = crud.get_slot_by_id(db, slot_id)
    
    return templates.TemplateResponse("booking.html", {
        "request": request,
        "slot": slot
    })

@app.post("/booking/{slot_id}")
def confirm_booking(slot_id: int, user_name: str, db: Session = Depends(get_db)):
    from schemas import BookingCreate
    
    booking_data = BookingCreate(
        slot_id=slot_id,
        user_name=user_name,
        start_time=datetime.utcnow()
    )
    booking = crud.create_booking(db, booking_data)
    return {"status": "success", "booking_id": booking.id}

@app.get("/history", response_class=HTMLResponse)
def booking_history(request: Request, db: Session = Depends(get_db)):
    bookings = crud.get_booking_history(db)
    
    return templates.TemplateResponse("history.html", {
        "request": request,
        "bookings": bookings
    })
