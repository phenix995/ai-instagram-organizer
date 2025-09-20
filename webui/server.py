"""FastAPI server providing a browser-based UI for the AI Instagram Organizer."""
from __future__ import annotations

import argparse
import base64
import os
import subprocess
import sys
import threading
import time
from collections import deque
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure the project root is on sys.path so the CLI module can be imported when
# the server is launched from the webui directory (e.g. inside the Docker
# container)
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from ai_instagram_organizer import (
    SUPPORTED_FORMATS,
    build_arg_parser,
    get_cli_arguments_metadata,
    get_default_cli_values,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="AI Instagram Organizer GUI",
    description="Web interface for configuring and running the AI Instagram Organizer",
    version="1.0.0",
)

# Enable local development from different hosts/ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class StartRequest(BaseModel):
    settings: Dict[str, Any]


class RunnerState:
    """Track the lifecycle of the running CLI process."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.process: Optional[subprocess.Popen[str]] = None
        self.logs: deque[str] = deque(maxlen=2000)
        self.command: List[str] = []
        self.start_time: Optional[float] = None
        self.finished_time: Optional[float] = None
        self.exit_code: Optional[int] = None

    def is_running(self) -> bool:
        with self.lock:
            return self.process is not None and self.process.poll() is None


state = RunnerState()


def _append_log(message: str) -> None:
    with state.lock:
        state.logs.append(message)


def _capture_process_output(process: subprocess.Popen[str]) -> None:
    """Capture stdout/stderr from the CLI process and store it in memory."""
    try:
        assert process.stdout is not None
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            _append_log(line.rstrip())
    finally:
        process.wait()
        with state.lock:
            state.exit_code = process.returncode
            state.finished_time = time.time()
            if state.process is process:
                state.process = None
            if process.returncode == 0:
                state.logs.append("✅ Process finished successfully")
            else:
                state.logs.append(f"⚠️ Process exited with code {process.returncode}")


def _build_command(settings: Dict[str, Any]) -> List[str]:
    """Convert UI settings into CLI arguments for the organizer script."""
    parser = build_arg_parser()
    action_map = {action.dest: action for action in parser._actions if action.dest != "help"}

    command: List[str] = [sys.executable, str(ROOT_DIR / "ai_instagram_organizer.py")]

    for dest, value in settings.items():
        if dest not in action_map:
            continue

        action = action_map[dest]

        if isinstance(action, argparse._StoreTrueAction):
            if value:
                command.append(action.option_strings[0])
            continue

        if value is None:
            continue

        if isinstance(value, str):
            if value.strip() == "":
                continue
            formatted_value = value
        else:
            formatted_value = str(value)

        flag = action.option_strings[0] if action.option_strings else f"--{dest}"
        command.extend([flag, formatted_value])

    return command


def _start_process(command: List[str]) -> None:
    with state.lock:
        if state.process is not None and state.process.poll() is None:
            raise RuntimeError("Process already running")

        state.logs.clear()
        state.logs.append("🚀 Launching AI Instagram Organizer...")
        state.command = command
        state.exit_code = None
        state.finished_time = None
        state.start_time = time.time()

        process = subprocess.Popen(
            command,
            cwd=ROOT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        state.process = process

    threading.Thread(target=_capture_process_output, args=(process,), daemon=True).start()


def _stop_process(force: bool = False) -> bool:
    with state.lock:
        process = state.process

    if process is None or process.poll() is not None:
        return False

    _append_log("🛑 Stopping process...")

    try:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if force:
                process.kill()
            else:
                raise
    finally:
        with state.lock:
            if state.process is process:
                state.process = None
            state.finished_time = time.time()
            state.exit_code = process.returncode

    return True


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="Missing web UI assets")
    return index_file.read_text(encoding="utf-8")


@app.get("/api/cli-metadata")
async def cli_metadata() -> Dict[str, Any]:
    return {"arguments": get_cli_arguments_metadata()}


@app.get("/api/defaults")
async def cli_defaults(config: str = Query("config.json", alias="config")) -> Dict[str, Any]:
    return get_default_cli_values(config)


@app.get("/api/status")
async def status(limit: int = 400) -> Dict[str, Any]:
    with state.lock:
        logs = list(state.logs)[-limit:]
        running = state.process is not None and state.process.poll() is None
        command = list(state.command)
        exit_code = state.exit_code
        started = state.start_time
        finished = state.finished_time

    return {
        "running": running,
        "logs": logs,
        "command": command,
        "exit_code": exit_code,
        "started_at": started,
        "finished_at": finished,
    }


@app.post("/api/start")
async def start_run(request: StartRequest) -> Dict[str, Any]:
    if state.is_running():
        raise HTTPException(status_code=409, detail="Organizer is already running")

    command = _build_command(request.settings)
    if len(command) <= 2:
        raise HTTPException(status_code=400, detail="No settings provided for the organizer")

    try:
        _start_process(command)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected failures
        raise HTTPException(status_code=500, detail=f"Could not start process: {exc}") from exc

    return {"status": "started", "command": command}


@app.post("/api/stop")
async def stop_run(force: bool = False) -> Dict[str, Any]:
    if not state.is_running():
        return {"status": "idle"}

    try:
        _stop_process(force=force)
    except subprocess.TimeoutExpired:
        _stop_process(force=True)
    except Exception as exc:  # pragma: no cover - unexpected failures
        raise HTTPException(status_code=500, detail=f"Failed to stop process: {exc}") from exc

    return {"status": "stopped"}


@app.post("/api/logs/clear")
async def clear_logs() -> Dict[str, str]:
    with state.lock:
        state.logs.clear()
    return {"status": "cleared"}


@app.get("/api/images")
async def fetch_images(folder: str, limit: int = 12) -> Dict[str, Any]:
    if not folder:
        return {"images": [], "error": "No folder provided"}

    folder_path = Path(folder).expanduser()

    if not folder_path.exists() or not folder_path.is_dir():
        return {"images": [], "error": "Folder not found"}

    images: List[Dict[str, Any]] = []
    supported = tuple(ext.lower() for ext in SUPPORTED_FORMATS)

    try:
        files = sorted(
            [p for p in folder_path.iterdir() if p.suffix.lower() in supported],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except PermissionError:
        return {"images": [], "error": "Permission denied for this folder"}

    for path in files[:limit]:
        try:
            with Image.open(path) as img:
                img.thumbnail((512, 512))
                buffer = BytesIO()
                format_name = "JPEG" if img.mode in {"RGB", "L", "P"} else "PNG"
                if format_name == "JPEG":
                    preview = img.convert("RGB")
                else:
                    preview = img.convert("RGBA") if "A" in img.getbands() else img.convert("RGB")
                preview.save(buffer, format=format_name)
                encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception:
            continue

        images.append({
            "path": str(path),
            "name": path.name,
            "data": f"data:image/{format_name.lower()};base64,{encoded}",
        })

    if not images:
        return {"images": [], "error": "No supported images found"}

    return {"images": images}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
