# tests/test_translator_logic.py
import pytest
from unittest.mock import Mock, patch
import threading
import numpy as np
import os

# Assume translator.py and utils.py are in the same directory as tests
from translator import perform_chunked_translation
from utils import first_chunk_ready_event, segments_ref, is_playing_ref


# --- Fixtures for Mocking External Libraries ---

@pytest.fixture(autouse=True) # autouse means this fixture runs for every test
def reset_global_state():
    """Resets global state variables before each test."""
    segments_ref['list'].clear()
    is_playing_ref['value'] = False
    first_chunk_ready_event.clear()

@pytest.fixture
def mock_ffmpeg_probe():
    """Mocks ffmpeg.probe to return a dummy video duration and audio stream."""
    with patch('ffmpeg.probe') as mock_probe:
        mock_probe.return_value = {
            'format': {'duration': '30.0'}, # 30 seconds duration
            'streams': [{'codec_type': 'audio', 'index': 0}] # Assume an audio stream exists
        }
        yield mock_probe

@pytest.fixture
def mock_ffmpeg_input():
    """Mocks ffmpeg.input().output().run_async() for audio stream simulation."""
    with patch('ffmpeg.input') as mock_input:
        mock_process = Mock()
        mock_process.stdout = Mock()
        # Configure stdout.read() to return chunks of dummy audio data
        # We'll make it return 3 chunks then empty string to simulate end of file
        mock_process.stdout.read.side_effect = [
            b'\x00' * (10 * 16000 * 2), # 10 seconds of dummy s16le audio
            b'\x00' * (10 * 16000 * 2),
            b'\x00' * (10 * 16000 * 2),
            b'' # End of file
        ]
        mock_process.poll.return_value = None # Assume process is running until .wait()
        mock_process.wait.return_value = 0 # Assume process exits cleanly

        mock_input.return_value.output.return_value.run_async.return_value = mock_process
        yield mock_input

@pytest.fixture
def mock_whisper_model():
    """Mocks whisper.load_model and the transcribe method."""
    with patch('whisper.load_model') as mock_load_model:
        mock_model_instance = Mock()
        # Configure transcribe to return dummy segments for each 10-second chunk
        mock_model_instance.transcribe.side_effect = [
            {'segments': [{'start': 0.0, 'end': 5.0, 'text': 'Hello world first chunk.'},
                          {'start': 5.0, 'end': 10.0, 'text': 'This is chunk one.'}]},
            {'segments': [{'start': 0.0, 'end': 4.0, 'text': 'Second chunk here.'},
                          {'start': 4.0, 'end': 8.0, 'text': 'More text.'}]},
            {'segments': [{'start': 0.0, 'end': 3.0, 'text': 'Final segment.'}]},
            # No more side_effect entries if there are no more chunks
        ]
        mock_load_model.return_value = mock_model_instance
        yield mock_load_model

@pytest.fixture
def mock_root_after():
    """Mocks root.after to prevent Tkinter GUI calls from failing in tests."""
    mock_root = Mock()
    mock_root.after.return_value = None # Ensure it doesn't try to schedule real Tkinter calls
    yield mock_root

@pytest.fixture
def mock_status_label():
    """Mocks the status_label_widget config method."""
    mock_label = Mock()
    yield mock_label

# --- Test Cases for perform_chunked_translation ---

def test_translation_process_completes_and_segments_are_added(
    mock_ffmpeg_probe, mock_ffmpeg_input, mock_whisper_model, mock_root_after, mock_status_label
):
    """
    Tests that the translation process runs to completion, segments are added to global state,
    and status updates are made.
    """
    test_video_path = "../sample_videos/h264_q30.mp4"

    # Run the function in a thread as it's designed for background execution
    translation_thread = threading.Thread(
        target=perform_chunked_translation,
        args=(test_video_path, mock_root_after, mock_status_label, {'process': None})
    )
    translation_thread.start()
    translation_thread.join(timeout=5) # Give it some time to run
    # Assert ffmpeg.probe was called
    mock_ffmpeg_probe.assert_called_once_with(test_video_path)
    # Assert ffmpeg.input and run_async were called
    mock_ffmpeg_input.assert_called_once_with(test_video_path)
    mock_ffmpeg_input.return_value.output.return_value.run_async.assert_called_once()
    # Assert whisper model was loaded and transcribe was called for each chunk
    mock_whisper_model.assert_called_once_with("base")
    assert mock_whisper_model.return_value.transcribe.call_count == 3 # 3 chunks from side_effect

    # Assert segments were added to the global list and adjusted for offset
    assert len(segments_ref['list']) == 5 # 2+2+1 segments from side_effect
    assert segments_ref['list'][0]['text'] == 'Hello world first chunk.'
    assert segments_ref['list'][0]['start'] == 0.0
    assert segments_ref['list'][1]['text'] == 'This is chunk one.'
    assert segments_ref['list'][1]['start'] == 5.0 # Original + 0 offset
    assert segments_ref['list'][2]['text'] == 'Second chunk here.'
    assert segments_ref['list'][2]['start'] == 10.0 # Original + 10 offset
    assert segments_ref['list'][3]['text'] == 'More text.'
    assert segments_ref['list'][3]['start'] == 14.0 # Original + 10 offset
    assert segments_ref['list'][4]['text'] == 'Final segment.'
    assert segments_ref['list'][4]['start'] == 20.0 # Original + 20 offset

    # Assert first_chunk_ready_event was set
    assert first_chunk_ready_event.is_set()
