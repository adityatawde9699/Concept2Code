from datetime import datetime

# In-memory mock storage
mock_users = {}
mock_sessions = {}

class MockUser:
    def __init__(self, name, email, vehicle_type=None):
        self.id = len(mock_users) + 1
        self.name = name
        self.email = email
        self.vehicle_type = vehicle_type
        self.created_at = datetime.utcnow()

def create_mock_user(name, email):
    user = MockUser(name, email)
    mock_users[email] = user
    return user

def authenticate_user(email, password="mock"):
    if email in mock_users:
        return mock_users[email]
    return None

def get_user_by_email(email):
    return mock_users.get(email)

def update_user_vehicle(email, vehicle_type):
    if email in mock_users:
        mock_users[email].vehicle_type = vehicle_type
        return mock_users[email]
    return None

def create_session(email):
    session_id = f"sess_{len(mock_sessions) + 1}_{email}"
    mock_sessions[session_id] = {
        "email": email,
        "created_at": datetime.utcnow()
    }
    return session_id

def get_session_user(session_id):
    if session_id in mock_sessions:
        email = mock_sessions[session_id]["email"]
        return get_user_by_email(email)
    return None
