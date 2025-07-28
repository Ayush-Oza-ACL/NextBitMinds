import vlc

class VLCPlayer:
    def __init__(self, vlc_instance):
        self.instance = vlc_instance
        self.player = self.instance.media_player_new()
        self._media_set = False # Track if media has been set

    def set_window_handle(self, window_id):
        """Sets the window handle for video output (for Windows)."""
        self.player.set_hwnd(window_id)

    def set_x_window_handle(self, window_id):
        """Sets the X window handle for video output (for Linux/Unix)."""
        self.player.set_xwindow(window_id)

    def set_new_media(self, file_path):
        """Sets a new media file for playback."""
        media = self.instance.media_new(file_path)
        self.player.set_media(media)
        self._media_set = True

    def play(self):
        """Starts playback."""
        if self._media_set:
            self.player.play()

    def pause(self):
        """Pauses or unpauses playback."""
        if self._media_set:
            self.player.pause()

    def stop(self):
        """Stops playback."""
        if self._media_set:
            self.player.stop()
            self._media_set = False # Reset media_set flag on stop

    def is_playing(self):
        """Checks if the player is currently playing."""
        return self.player.is_playing()

    def get_time(self):
        """Returns the current playback time in milliseconds."""
        return self.player.get_time()

    def is_media_set(self):
        """Returns True if media has been loaded into the player."""
        return self._media_set