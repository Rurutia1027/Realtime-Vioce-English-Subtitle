import threading
import time
import tkinter as tk
from queue import Empty, Full, Queue

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 92
FALLBACK_CHUNK_SECONDS = 4
QUEUE_MAXSIZE = 3


class FallbackRecorder:
    def __init__(self, model_name="tiny.en", sample_rate=16000, chunk_seconds=FALLBACK_CHUNK_SECONDS):
        import sounddevice as sd
        from faster_whisper import WhisperModel

        self.sd = sd
        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self.model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=2,
            num_workers=1,
        )

    def text(self):
        frame_count = int(self.sample_rate * self.chunk_seconds)
        audio = self.sd.rec(frame_count, samplerate=self.sample_rate, channels=1, dtype="float32")
        self.sd.wait()
        mono_audio = audio[:, 0]
        segments, _ = self.model.transcribe(
            mono_audio,
            language="en",
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return " ".join(seg.text.strip() for seg in segments if seg.text.strip())


class LiveCaptionOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Live Caption Overlay")
        self.root.configure(bg="#111111")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self._position_at_bottom()

        self.queue = Queue(maxsize=QUEUE_MAXSIZE)
        self.current_line = "Listening..."
        self.running = True
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._last_error_time = 0.0

        self._build_ui()

        try:
            from RealtimeSTT import AudioToTextRecorder

            self.recorder = AudioToTextRecorder(
                model="tiny.en",
                language="en",
                spinner=False,
                post_speech_silence_duration=1.2,
            )
        except Exception:
            self.recorder = FallbackRecorder()

        self.worker = threading.Thread(target=self._capture_loop, daemon=True)
        self.worker.start()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Escape>", lambda _event: self._on_close())
        self.root.bind("<ButtonPress-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._on_drag)
        self.root.after(100, self._drain_queue)

    def _position_at_bottom(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - WINDOW_WIDTH) // 2
        y = screen_height - WINDOW_HEIGHT - 40
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _build_ui(self):
        self.caption_label = tk.Label(
            self.root,
            text=self.current_line,
            bg="#111111",
            fg="#f5f5f5",
            justify="center",
            anchor="center",
            font=("Arial", 28, "bold"),
            wraplength=WINDOW_WIDTH - 24,
        )
        self.caption_label.pack(fill="both", expand=True, padx=14, pady=8)
        self.caption_label.bind("<ButtonPress-1>", self._start_drag)
        self.caption_label.bind("<B1-Motion>", self._on_drag)

    def _start_drag(self, event):
        self._drag_offset_x = event.x_root - self.root.winfo_x()
        self._drag_offset_y = event.y_root - self.root.winfo_y()

    def _on_drag(self, event):
        new_x = event.x_root - self._drag_offset_x
        new_y = event.y_root - self._drag_offset_y
        self.root.geometry(f"+{new_x}+{new_y}")

    def _capture_loop(self):
        while self.running:
            try:
                text = self.recorder.text().strip()
                if text:
                    self._push_latest(text)
            except Exception as exc:
                now = time.time()
                # Throttle repeated errors to prevent queue growth and OOM.
                if now - self._last_error_time >= 2.0:
                    self._last_error_time = now
                    self._push_latest(f"[ERROR] {exc}")
                time.sleep(0.25)

    def _push_latest(self, text):
        try:
            self.queue.put_nowait(text)
        except Full:
            try:
                self.queue.get_nowait()
            except Empty:
                pass
            self.queue.put_nowait(text)

    def _drain_queue(self):
        while True:
            try:
                message = self.queue.get_nowait()
            except Empty:
                break
            self._append_line(message)

        if self.running:
            self.root.after(100, self._drain_queue)

    def _append_line(self, text):
        clean_text = " ".join(text.split())
        self.current_line = clean_text
        self.caption_label.config(text=self.current_line)

    def _on_close(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LiveCaptionOverlay()
    app.run()
