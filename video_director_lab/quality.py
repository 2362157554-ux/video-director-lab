from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MediaQualityReport:
    path: Path
    exists: bool
    size_bytes: int = 0
    ffprobe_available: bool = False
    metadata: dict[str, Any] | None = None
    error: str = ""


def inspect_media(path: Path) -> MediaQualityReport:
    if not path.exists():
        return MediaQualityReport(path=path, exists=False, error="file does not exist")

    try:
        result = subprocess.run(
            (
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except OSError as exc:
        return MediaQualityReport(
            path=path,
            exists=True,
            size_bytes=path.stat().st_size,
            ffprobe_available=False,
            error=str(exc),
        )

    metadata = None
    if result.returncode == 0 and result.stdout:
        metadata = json.loads(result.stdout)

    return MediaQualityReport(
        path=path,
        exists=True,
        size_bytes=path.stat().st_size,
        ffprobe_available=result.returncode == 0,
        metadata=metadata,
        error="" if result.returncode == 0 else result.stderr.strip(),
    )
