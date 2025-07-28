import tkinter as tk
from gui import VideoTranslatorApp
from video_player import VLCPlayer
import vlc
import os

def on_exit(root, player_instance, ffmpeg_process_ref):
    """Handles clean shutdown."""
    print("Exiting...")
    # Terminate ffmpeg process if it's running
    if ffmpeg_process_ref['process'] and ffmpeg_process_ref['process'].poll() is None:
        print("Terminating ffmpeg process...")
        ffmpeg_process_ref['process'].kill()
    if player_instance:
        player_instance.stop()
    root.quit()
    root.destroy()

def main():
    root = tk.Tk()
    root.title("Video Translator (Refined)")

    # Initialize VLC instance
    instance = vlc.Instance('--no-xlib')
    player_instance = VLCPlayer(instance)

    # Dictionary to hold the ffmpeg process reference, allowing it to be passed by reference
    ffmpeg_process_ref = {'process': None}

    app = VideoTranslatorApp(root, player_instance, ffmpeg_process_ref)

    # Set up the exit protocol
    root.protocol("WM_DELETE_WINDOW", lambda: on_exit(root, player_instance, ffmpeg_process_ref))

    root.mainloop()

if __name__ == "__main__":
    main()