import tkinter as tk
from tkinter import filedialog
import whisper
import vlc
import threading
import os
import ffmpeg
import numpy as np

# --- Globals ---
segments = []
is_playing = False
player = None
ffmpeg_process = None

# --- Core Functions ---

def perform_chunked_translation(video_path, root, status_label_widget, model, first_chunk_ready_event):
    """
    Extracts audio in chunks, translates them, and signals when the first chunk is done.
    """
    global segments, ffmpeg_process
    CHUNK_DURATION_S = 10  # Chunk size updated to 10 seconds

    try:
        probe = ffmpeg.probe(video_path)
        audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
        if audio_stream is None:
            root.after(0, lambda: status_label_widget.config(text="Error: No audio stream found."))
            return
        
        sample_rate = 16000 # Whisper's required sample rate
        total_duration = float(probe['format']['duration'])

    except ffmpeg.Error as e:
        print(f"ffmpeg error: {e.stderr}")
        root.after(0, lambda: status_label_widget.config(text="Error: ffmpeg failed. Is it installed?"))
        return

    ffmpeg_process = ( # Change 'process' to 'ffmpeg_process'
        ffmpeg.input(video_path)
        .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar=sample_rate)
        .run_async(pipe_stdout=True, pipe_stderr=True)
    )
    

    chunk_offset = 0.0
    bytes_per_chunk = CHUNK_DURATION_S * sample_rate * 2 # 2 bytes/sample for s16le

    is_first_chunk = True
    while chunk_offset < total_duration:
        status_text = f"Translating... ({int(chunk_offset)}s / {int(total_duration)}s)"
        root.after(0, lambda s=status_text: status_label_widget.config(text=s))
        
        in_bytes = ffmpeg_process.stdout.read(bytes_per_chunk)
        if not in_bytes:
            break

        audio_np = np.frombuffer(in_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        result = model.transcribe(audio_np, task="translate", fp16=False)

        for seg in result['segments']:
            new_seg = seg.copy()
            new_seg['start'] += chunk_offset
            new_seg['end'] += chunk_offset
            segments.append(new_seg)
        
        # **NEW**: Signal that the first chunk is ready
        if is_first_chunk:
            first_chunk_ready_event.set()
            is_first_chunk = False
            root.after(0, lambda: status_label_widget.config(text="Playing..."))

        chunk_offset += CHUNK_DURATION_S

    ffmpeg_process.wait()
    # If the first chunk was the *only* chunk, ensure the event is still set
    if is_first_chunk:
        first_chunk_ready_event.set()
        
    root.after(0, lambda: status_label_widget.config(text="Translation complete."))


def sync_translation(root, translation_label_widget):
    """Checks video time and updates the translation label."""
    global is_playing, player
    if not is_playing or not player:
        # Keep checking even if not playing, in case playback starts
        root.after(250, lambda: sync_translation(root, translation_label_widget))
        return

    current_time = player.get_time() / 1000.0
    current_text = ""
    for segment in segments:
        if segment['start'] <= current_time <= segment['end']:
            current_text = segment['text'].strip()
            break
    
    translation_label_widget.config(text=current_text)
    root.after(250, lambda: sync_translation(root, translation_label_widget))

def toggle_pause_play():
    """Toggles the video pause state and updates the button text."""
    if player.is_playing():
        player.pause()
        pause_play_button.config(text="Play >")
    else:
        # The pause() method also unpauses the player
        player.pause()
        pause_play_button.config(text="Pause ||")


def load_and_translate_refined(root, translation_label_widget, status_label_widget):
    """
    Handles file loading, waits for the first chunk, then plays.
    """
    global segments, is_playing, player

    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv")])
    if not file_path:
        return
    
    btn.pack_forget()

    if player and player.is_playing():
        player.stop()
    is_playing = False
    segments.clear()
    translation_label_widget.config(text="Translation will appear here...")
    status_label_widget.config(text=f"Selected: {os.path.basename(file_path)}")

    # Prepare media for playback, but don't play it yet
    media = instance.media_new(file_path)
    player.set_media(media)
    
    # Event to signal when the first chunk is ready
    first_chunk_ready_event = threading.Event()

    # This function will check the event and start playback
    def check_and_start_playback():
        global is_playing
        if first_chunk_ready_event.is_set():
            player.play()
            is_playing = True
            pause_play_button.pack(pady=10) # Add this line to show the button
        else:
            # If not ready, check again in 100ms
            root.after(100, check_and_start_playback)

    def background_task():
        """Loads model and runs the chunked translation."""
        global ffmpeg_process
        status_label_widget.after(0, lambda: status_label_widget.config(text="Loading 'medium' model..."))
        model = whisper.load_model("base")
        perform_chunked_translation(file_path, root, status_label_widget, model, first_chunk_ready_event)

    # --- Start the process ---
    # 1. Start the subtitle display loop
    sync_translation(root, translation_label_widget)
    # 2. Start the background job for loading and translating
    threading.Thread(target=background_task, daemon=True).start()
    # 3. Start polling to check when to begin playback
    check_and_start_playback()


def on_exit(root):
    """Handles clean shutdown."""
    global is_playing, player, ffmpeg_process
    print("Exiting...")
    if ffmpeg_process and ffmpeg_process.poll() is None:
        print("Terminating ffmpeg process...")
        ffmpeg_process.kill()
    if player:
        player.stop()
    is_playing = False
    root.quit()
    root.destroy()

# --- GUI and VLC Setup ---
root = tk.Tk()
root.title("Video Translator (Refined)")

instance = vlc.Instance('--no-xlib')
player = instance.media_player_new()

root.protocol("WM_DELETE_WINDOW", lambda: on_exit(root))

video_panel = tk.Frame(root, width=854, height=480, bg="black")
video_panel.pack(pady=10)

root.update()
video_id = video_panel.winfo_id()
if os.name == 'nt':
    player.set_hwnd(video_id)
else:
    player.set_xwindow(video_id)

translation_label = tk.Label(root, text="Translation will appear here...", wraplength=800, font=("Arial", 14), justify="center")
translation_label.pack(pady=5)
status_label = tk.Label(root, text="Please open a video file to begin.", font=("Arial", 10), fg="grey")
status_label.pack(pady=5)

btn = tk.Button(root, text="Open Video & Translate", command=lambda: load_and_translate_refined(root, translation_label, status_label))
pause_play_button = tk.Button(root, text="Pause ||", command=lambda: toggle_pause_play())
# pause_play_button.pack_forget()
btn.pack(pady=10)

root.mainloop()