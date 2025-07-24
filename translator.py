import whisper
import ffmpeg
import numpy as np
import threading
from utils import first_chunk_ready_event, segments_ref

def perform_chunked_translation(video_path, root, status_label_widget, ffmpeg_process_ref):
    """
    Extracts audio in chunks, translates them, and signals when the first chunk is done.
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
        status_text = f"Translating... ({int(chunk_offset)}s / {int(total_duration)}s)"
        root.after(0, lambda s=status_text: status_label_widget.config(text=s))

        in_bytes = ffmpeg_process_ref['process'].stdout.read(bytes_per_chunk)
        if not in_bytes:
            break

        audio_np = np.frombuffer(in_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        result = model.transcribe(audio_np, task="translate", fp16=False)

        for seg in result['segments']:
            new_seg = seg.copy()
            new_seg['start'] += chunk_offset
            new_seg['end'] += chunk_offset
            segments_ref['list'].append(new_seg)

        # Signal that the first chunk is ready
        if is_first_chunk:
            first_chunk_ready_event.set()
            is_first_chunk = False
            root.after(0, lambda: status_label_widget.config(text="Playing..."))

        chunk_offset += CHUNK_DURATION_S

    ffmpeg_process_ref['process'].wait()
    # If the first chunk was the *only* chunk, ensure the event is still set
    if is_first_chunk:
        first_chunk_ready_event.set()

    root.after(0, lambda: status_label_widget.config(text="Translation complete."))