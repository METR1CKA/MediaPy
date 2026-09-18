"""MediaPy Tkinter window."""

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, ttk

from mediapy.app import Job, Mode, Progress, run
from mediapy.download import ensure_ffmpeg
from mediapy.errors import InvalidUrl, MediaPyError, MissingFFmpeg, PathNotSelected
from mediapy.paths import safe_stem

Runner = Callable[..., Path]


def build_job(url: str, name: str, out_dir: Path | None, mode: Mode) -> Job:
    """Validate the form values and build a Job. Raises MediaPyError."""
    if not url or not url.strip():
        raise InvalidUrl("Enter a URL to download.")
    if out_dir is None:
        raise PathNotSelected("Select an output folder first.")
    safe_stem(name)
    return Job(url=url.strip(), name=name, out_dir=out_dir, mode=mode)


class MediaPyWindow:
    _POLL_MS = 100

    def __init__(self, root: tk.Tk, runner: Runner = run) -> None:
        self._root = root
        self._runner = runner
        self._queue: queue.Queue = queue.Queue()
        self._out_dir: Path | None = None
        self._worker: threading.Thread | None = None
        self._ffmpeg_ok = True
        self._build()
        self._check_ffmpeg()
        self._root.after(self._POLL_MS, self._poll)

    def _build(self) -> None:
        self._root.title("MediaPy")
        frame = ttk.Frame(self._root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        self._root.columnconfigure(0, weight=1)
        self._root.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(7, weight=1)

        ttk.Label(frame, text="URL:").grid(row=0, column=0, sticky="w", pady=3)
        self._url_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._url_var).grid(
            row=0, column=1, sticky="ew", pady=3
        )

        ttk.Label(frame, text="Nombre:").grid(row=1, column=0, sticky="w", pady=3)
        self._name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._name_var).grid(
            row=1, column=1, sticky="ew", pady=3
        )

        ttk.Button(frame, text="Elegir carpeta…", command=self._choose_dir).grid(
            row=2, column=0, sticky="w", pady=3
        )
        self._dir_label = ttk.Label(frame, text="Sin carpeta seleccionada")
        self._dir_label.grid(row=2, column=1, sticky="w")

        self._mode_var = tk.StringVar(value=str(Mode.VIDEO))
        modes = ttk.Frame(frame)
        modes.grid(row=3, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Radiobutton(
            modes, text="Video (MP4)", variable=self._mode_var, value=str(Mode.VIDEO)
        ).pack(side="left")
        ttk.Radiobutton(
            modes,
            text="Video + MP3",
            variable=self._mode_var,
            value=str(Mode.VIDEO_AND_MP3),
        ).pack(side="left", padx=(12, 0))
        ttk.Radiobutton(
            modes,
            text="Solo audio (MP3)",
            variable=self._mode_var,
            value=str(Mode.AUDIO_ONLY),
        ).pack(side="left", padx=(12, 0))

        self._download_btn = ttk.Button(
            frame, text="Descargar", command=self._on_download
        )
        self._download_btn.grid(row=4, column=0, sticky="w", pady=6)

        self._bar = ttk.Progressbar(frame, maximum=100, mode="determinate")
        self._bar.grid(row=5, column=0, columnspan=2, sticky="ew")

        self._step_label = ttk.Label(frame, text="")
        self._step_label.grid(row=6, column=0, columnspan=2, sticky="w")

        self._log = tk.Text(frame, height=10, state="disabled", wrap="word")
        self._log.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=(6, 0))

    def _check_ffmpeg(self) -> None:
        try:
            ensure_ffmpeg()
        except MissingFFmpeg as e:
            self._ffmpeg_ok = False
            self._log_line(str(e))
            self._log_line("Descargar queda deshabilitado hasta instalar ffmpeg.")
            self._download_btn.state(["disabled"])

    def _choose_dir(self) -> None:
        folder = filedialog.askdirectory(parent=self._root)
        if folder:
            self._set_out_dir(Path(folder))

    def _set_out_dir(self, path: Path) -> None:
        self._out_dir = path
        self._dir_label.configure(text=str(path))

    def _on_download(self) -> None:
        try:
            job = build_job(
                self._url_var.get(),
                self._name_var.get(),
                self._out_dir,
                Mode(self._mode_var.get()),
            )
        except MediaPyError as e:
            self._log_line(f"[ ! ] {e}")
            return
        if str(self._bar.cget("mode")) == "indeterminate":
            self._bar.stop()
        self._bar.configure(mode="determinate", value=0)
        self._step_label.configure(text="")
        self._log_line(f"Descargando {job.name} ({job.mode.value})...")
        self._download_btn.state(["disabled"])
        self._worker = threading.Thread(
            target=self._worker_main, args=(job,), daemon=True
        )
        self._worker.start()

    def _worker_main(self, job: Job) -> None:
        # Runs on the worker thread: an escaped exception would kill the
        # thread silently and leave the Download button disabled forever.
        try:
            result = self._runner(
                job,
                on_status=lambda text: self._queue.put(("status", text)),
                on_progress=lambda progress: self._queue.put(("progress", progress)),
            )
        except Exception as e:  # noqa: BLE001 - deliberate worker boundary
            self._queue.put(("error", str(e) or type(e).__name__))
        else:
            self._queue.put(("done", result))

    def _poll(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "status":
                    self._log_line(payload)
                elif kind == "progress":
                    self._apply_progress(payload)
                elif kind == "done":
                    self._finish(payload)
                elif kind == "error":
                    self._fail(payload)
        except queue.Empty:
            pass
        self._root.after(self._POLL_MS, self._poll)

    def _apply_progress(self, progress: Progress) -> None:
        self._step_label.configure(text=progress.label)
        if progress.fraction is None:
            if str(self._bar.cget("mode")) != "indeterminate":
                self._bar.configure(mode="indeterminate")
                self._bar.start(10)
        else:
            if str(self._bar.cget("mode")) == "indeterminate":
                self._bar.stop()
                self._bar.configure(mode="determinate")
            self._bar.configure(value=progress.fraction * 100)

    def _finish(self, result: Path) -> None:
        self._log_line(f"Guardado: {result}")
        self._end_run()

    def _fail(self, message: str) -> None:
        self._log_line(f"[ ! ] {message}")
        self._end_run()

    def _end_run(self) -> None:
        if str(self._bar.cget("mode")) == "indeterminate":
            self._bar.stop()
            self._bar.configure(mode="determinate")
        self._bar.configure(value=0)
        self._step_label.configure(text="")
        if self._ffmpeg_ok:
            self._download_btn.state(["!disabled"])

    def _log_line(self, text: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", f"{text}\n")
        self._log.see("end")
        self._log.configure(state="disabled")


def launch() -> None:
    """Open the MediaPy window."""
    root = tk.Tk()
    root.minsize(560, 460)
    MediaPyWindow(root)
    root.mainloop()
