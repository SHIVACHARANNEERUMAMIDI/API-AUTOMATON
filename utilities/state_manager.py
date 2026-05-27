import json
import os

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Logs", "last_state.json")

def save_state(key, value):
    """Saves a value to the state file."""
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                state = json.load(f)
            except json.JSONDecodeError:
                state = {}
    
    state[key] = value
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_state(key):
    """Retrieves a value from the state file."""
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        try:
            state = json.load(f)
            return state.get(key)
        except json.JSONDecodeError:
            return None

def clear_state():
    """Clears the state file."""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
