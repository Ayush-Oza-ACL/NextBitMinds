# tests/test_vlc_player.py
import pytest
from unittest.mock import Mock, patch
import vlc

from video_player import VLCPlayer

@pytest.fixture
def mock_vlc_instance():
    """A pytest fixture to mock the vlc.Instance."""
    with patch('vlc.Instance') as MockVLCInstance:
        mock_instance = Mock() # This is the mock for the actual vlc.Instance() object
        mock_player = Mock()
        mock_media = Mock() # A mock for the media object that media_new will return

        # Configure the mocked instance's methods
        mock_instance.media_player_new.return_value = mock_player
        mock_instance.media_new.return_value = mock_media # <--- NEW: Configure media_new

        MockVLCInstance.return_value = mock_instance # Ensure vlc.Instance() returns our configured mock_instance

        yield mock_instance # Yield the mocked instance object (i.e., the mock of the vlc.Instance() object)

@pytest.fixture
def vlc_player_instance(mock_vlc_instance):
    """Fixture to provide a VLCPlayer instance with mocked vlc.Instance."""
    return VLCPlayer(mock_vlc_instance)

# --- Test Cases for VLCPlayer ---

def test_vlc_player_init(mock_vlc_instance, vlc_player_instance):
    """
    Test that VLCPlayer's __init__ correctly initializes a VLC instance
    and creates a media player.
    """
    # Ensure media_player_new was called on the mocked instance
    mock_vlc_instance.media_player_new.assert_called_once()
    assert vlc_player_instance.player is not None
    assert vlc_player_instance._media_set is False

def test_set_window_handle(vlc_player_instance):
    """Test set_window_handle calls player.set_hwnd."""
    mock_hwnd = 12345
    vlc_player_instance.set_window_handle(mock_hwnd)
    vlc_player_instance.player.set_hwnd.assert_called_once_with(mock_hwnd)

def test_set_x_window_handle(vlc_player_instance):
    """Test set_x_window_handle calls player.set_xwindow."""
    mock_xwindow = 54321
    vlc_player_instance.set_x_window_handle(mock_xwindow)
    vlc_player_instance.player.set_xwindow.assert_called_once_with(mock_xwindow)

# MODIFIED: test_set_new_media now uses mock_vlc_instance
def test_set_new_media(vlc_player_instance, mock_vlc_instance): # Added mock_vlc_instance as arg
    """Test set_new_media correctly sets media and updates _media_set flag."""
    test_file_path = "../sample_videos/h264_q30.mp4"
    # Get the mock media object that mock_vlc_instance.media_new is configured to return
    mock_media_object_returned_by_instance = mock_vlc_instance.media_new.return_value
    vlc_player_instance.set_new_media(test_file_path)
    # Check that media_new was called on the mocked instance
    mock_vlc_instance.media_new.assert_called_once_with(test_file_path)
    # Check that player.set_media was called with the mocked media object
    vlc_player_instance.player.set_media.assert_called_once_with(mock_media_object_returned_by_instance)
    # Check that _media_set flag is updated
    assert vlc_player_instance._media_set is True

def test_play_starts_playback_if_media_set(vlc_player_instance):
    """Test play method calls player.play() when media is set."""
    vlc_player_instance._media_set = True # Manually set media_set for this test
    vlc_player_instance.play()
    vlc_player_instance.player.play.assert_called_once()

def test_play_does_nothing_if_media_not_set(vlc_player_instance):
    """Test play method does nothing when media is not set."""
    vlc_player_instance._media_set = False
    vlc_player_instance.play()
    vlc_player_instance.player.play.assert_not_called()

def test_pause_toggles_playback_if_media_set(vlc_player_instance):
    """Test pause method calls player.pause() when media is set."""
    vlc_player_instance._media_set = True
    vlc_player_instance.pause()
    vlc_player_instance.player.pause.assert_called_once()

def test_pause_does_nothing_if_media_not_set(vlc_player_instance):
    """Test pause method does nothing when media is not set."""
    vlc_player_instance._media_set = False
    vlc_player_instance.pause()
    vlc_player_instance.player.pause.assert_not_called()

def test_stop_stops_playback_and_resets_media_set(vlc_player_instance):
    """Test stop method calls player.stop() and resets _media_set flag."""
    vlc_player_instance._media_set = True
    vlc_player_instance.stop()
    vlc_player_instance.player.stop.assert_called_once()
    assert vlc_player_instance._media_set is False

def test_is_playing_returns_player_state(vlc_player_instance):
    """Test is_playing method correctly returns the player's playing state."""
    vlc_player_instance.player.is_playing.return_value = True
    assert vlc_player_instance.is_playing() is True
    vlc_player_instance.player.is_playing.assert_called_once()

    vlc_player_instance.player.is_playing.return_value = False
    # Reset mock call count to test again without previous calls interfering
    vlc_player_instance.player.is_playing.reset_mock()
    assert vlc_player_instance.is_playing() is False
    vlc_player_instance.player.is_playing.assert_called_once()

def test_get_time_returns_player_time(vlc_player_instance):
    """Test get_time method correctly returns the player's time."""
    mock_time = 5000 # milliseconds
    vlc_player_instance.player.get_time.return_value = mock_time
    assert vlc_player_instance.get_time() == mock_time
    vlc_player_instance.player.get_time.assert_called_once()

def test_is_media_set_returns_correct_flag(vlc_player_instance):
    """Test is_media_set returns the current state of _media_set."""
    vlc_player_instance._media_set = True
    assert vlc_player_instance.is_media_set() is True
    vlc_player_instance._media_set = False
    assert vlc_player_instance.is_media_set() is False
