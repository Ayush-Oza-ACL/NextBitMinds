import tkinter as tk
from tkinter import filedialog
import os
import threading
from translator import perform_chunked_translation
from utils import first_chunk_ready_event, is_playing_ref, segments_ref

class VideoTranslatorApp:
    def __init__(self, root, player_instance, ffmpeg_process_ref):
        self.root = root
        self.player = player_instance
        self.ffmpeg_process_ref = ffmpeg_process_ref

        self.video_panel = tk.Frame(root, width=854, height=480, bg="black")
        self.video_panel.pack(pady=10)

        root.update()
        video_id = self.video_panel.winfo_id()
        if os.name == 'nt':
            self.player.set_window_handle(video_id)
        else:
            self.player.set_x_window_handle(video_id)

        self.translation_label = tk.Label(root, text="Translation will appear here...", wraplength=800, font=("Arial", 14), justify="center")
        self.translation_label.pack(pady=5)

        self.status_label = tk.Label(root, text="Please open a video file to begin.", font=("Arial", 10), fg="grey")
        self.status_label.pack(pady=5)

        self.open_button = tk.Button(root, text="Open Video & Translate", command=self._load_and_translate)
        self.open_button.pack(pady=10)

        self.pause_play_button = tk.Button(root, text="Pause ||", command=self._toggle_pause_play)
        self.pause_play_button.pack_forget() # Initially hidden

        # Start the sync translation loop
        self._sync_translation()

    def _sync_translation(self):
        """Checks video time and updates the translation label."""
        if not is_playing_ref['value'] or not self.player.is_media_set():
            self.root.after(250, self._sync_translation)
            return

        current_time = self.player.get_time() / 1000.0
        current_text = ""
        for segment in segments_ref['list']:
            if segment['start'] <= current_time <= segment['end']:
                current_text = segment['text'].strip()
                break

        self.translation_label.config(text=current_text)
        self.root.after(250, self._sync_translation)

    def _toggle_pause_play(self):
        """Toggles the video pause state and updates the button text."""
        if self.player.is_playing():
            self.player.pause()
            self.pause_play_button.config(text="Play >")
        else:
            self.player.play()
            self.pause_play_button.config(text="Pause ||")

    def _load_and_translate(self):
        """
        Handles file loading, waits for the first chunk, then plays.
        """
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv")])
        if not file_path:
            return

        self.open_button.pack_forget()

        if self.player.is_playing():
            self.player.stop()
        is_playing_ref['value'] = False
        segments_ref['list'].clear()
        self.translation_label.config(text="Translation will appear here...")
        self.status_label.config(text=f"Selected: {os.path.basename(file_path)}")

        # Prepare media for playback, but don't play it yet
        self.player.set_new_media(file_path)

        # Reset the event for a new translation
        first_chunk_ready_event.clear()

        # This function will check the event and start playback
        def check_and_start_playback():
            if first_chunk_ready_event.is_set():
                self.player.play()
                is_playing_ref['value'] = True
                self.pause_play_button.pack(pady=10) # Show the button
            else:
                # If not ready, check again in 100ms
                self.root.after(100, check_and_start_playback)

        def background_translation_task():
            """Runs the chunked translation in a separate thread."""
            perform_chunked_translation(file_path, self.root, self.status_label, self.ffmpeg_process_ref)

        # Start the background job for loading and translating
        threading.Thread(target=background_translation_task, daemon=True).start()
        # Start polling to check when to begin playback
        check_and_start_playback()