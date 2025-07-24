import threading

# --- Globals shared across modules ---
segments_ref = {'list': []}  # Using a mutable dict to hold the list of segments
is_playing_ref = {'value': False} # Using a mutable dict to hold the boolean state
first_chunk_ready_event = threading.Event()