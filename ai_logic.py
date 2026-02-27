from datetime import datetime, timedelta
from models import ParkingSlot

ZONE_SCORES = {"A": 100, "B": 70, "C": 40}
AVG_PARKING_DURATION = 60

def calculate_slot_score(slot: ParkingSlot) -> int:
    score = 0
    
    score += ZONE_SCORES.get(slot.zone, 0)
    
    if not slot.is_occupied:
        score += 50
    else:
        estimated_free = predict_free_time(slot)
        if estimated_free < 15:
            score += 30
    
    return score

def predict_free_time(slot: ParkingSlot) -> int:
    if not slot.is_occupied or not slot.last_occupied_time:
        return 0
    
    elapsed = (datetime.utcnow() - slot.last_occupied_time).total_seconds() / 60
    remaining = max(0, AVG_PARKING_DURATION - elapsed)
    return int(remaining)

def recommend_best_slot(slots: list) -> ParkingSlot or None:
    if not slots:
        return None
    
    best_slot = max(slots, key=lambda s: calculate_slot_score(s))
    return best_slot
