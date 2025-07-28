import whisper
import ffmpeg
import numpy as np
import threading
import os # Import os module for path manipulation
from utils import first_chunk_ready_event, segments_ref

def format_timestamp(seconds):
    """Formats seconds into SRT time format (HH:MM:SS,milliseconds)."""
    # Use int() for seconds to avoid float precision issues when converting to HH:MM:SS
    # Then calculate milliseconds from the remaining fractional part
    milliseconds = int((seconds - int(seconds)) * 1000)
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"

def perform_chunked_translation(video_path, root, status_label_widget, ffmpeg_process_ref):
    """
    Extracts audio in chunks, transcribes original, translates, and stores both with timestamps.
    Signals when the first chunk is done.
    """
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

    # Determine output file names
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    original_transcript_file = f"{base_name}_original.srt"
    translated_transcript_file = f"{base_name}_translated.srt"

    # Open files for writing (using 'w' to overwrite if they exist)
    # Using 'utf-8' encoding for broader character support
    original_file = open(original_transcript_file, "w", encoding="utf-8")
    translated_file = open(translated_transcript_file, "w", encoding="utf-8")

    # Initialize SRT sequence numbers
    original_srt_sequence = 1
    translated_srt_sequence = 1

    # Store the ffmpeg process reference in the mutable dictionary
    ffmpeg_process_ref['process'] = (
        ffmpeg.input(video_path)
        .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar=sample_rate)
        .run_async(pipe_stdout=True, pipe_stderr=True)
    )

    chunk_offset = 0.0
    bytes_per_chunk = CHUNK_DURATION_S * sample_rate * 2 # 2 bytes/sample for s16le

    is_first_chunk = True
    status_label_widget.after(0, lambda: status_label_widget.config(text="Loading 'base' model..."))
    model = whisper.load_model("base")

    while chunk_offset < total_duration:
        status_text = f"Processing... ({int(chunk_offset)}s / {int(total_duration)}s)"
        root.after(0, lambda s=status_text: status_label_widget.config(text=s))

        in_bytes = ffmpeg_process_ref['process'].stdout.read(bytes_per_chunk)
        if not in_bytes:
            break

        audio_np = np.frombuffer(in_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Perform original transcription
        original_result = model.transcribe(audio_np, task="transcribe", fp16=False)
        for seg in original_result['segments']:
            start_time = seg['start'] + chunk_offset
            end_time = seg['end'] + chunk_offset
            original_file.write(f"{format_timestamp(start_time)} - {format_timestamp(end_time)} : ")
            original_file.write(f"{seg['text'].strip()}\n")
            original_srt_sequence += 1
        original_file.flush() # Ensure data is written to disk periodically

        # Perform translation
        translated_result = model.transcribe(audio_np, task="translate", fp16=False)
        for seg in translated_result['segments']:
            new_seg = seg.copy()
            new_seg['start'] += chunk_offset
            new_seg['end'] += chunk_offset
            segments_ref['list'].append(new_seg) # This is for your UI/internal use

            # Write translated segment to file
            translated_file.write(f"{format_timestamp(new_seg['start'])} - {format_timestamp(new_seg['end'])} : ")
            translated_file.write(f"{new_seg['text'].strip()}\n")
            translated_srt_sequence += 1
        translated_file.flush() # Ensure data is written to disk periodically

        # Signal that the first chunk is ready (for UI playback)
        if is_first_chunk:
            first_chunk_ready_event.set()
            is_first_chunk = False
            root.after(0, lambda: status_label_widget.config(text="Playing..."))

        chunk_offset += CHUNK_DURATION_S

    # Wait for the ffmpeg process to finish reading all data
    ffmpeg_process_ref['process'].wait()
    
    # If the first chunk was the *only* chunk, ensure the event is still set
    if is_first_chunk:
        first_chunk_ready_event.set()

    # Close the output files
    original_file.close()
    translated_file.close()

    root.after(0, lambda: status_label_widget.config(text="Translation and transcription complete."))
