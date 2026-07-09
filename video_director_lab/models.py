from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


AssetKind = Literal["video", "audio", "image", "document", "subtitle", "unknown"]
RouteReadiness = Literal["ready", "needs_tool", "needs_confirmation", "planning_only"]


@dataclass(frozen=True)
class Asset:
    path: Path
    kind: AssetKind = "unknown"
    role: str = ""


@dataclass(frozen=True)
class VideoRequest:
    brief: str
    target_duration_seconds: int | None = None
    aspect_ratio: str = "9:16"
    platform: str = ""
    language: str = "zh-CN"
    wants_editable_draft: bool = False
    wants_render: bool = False
    source_files: tuple[Path, ...] = ()
    delivery_formats: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProductionRoute:
    name: str
    purpose: str
    required_tools: tuple[str, ...]
    readiness: RouteReadiness
    output: str


@dataclass(frozen=True)
class TimelineItem:
    start_seconds: int
    end_seconds: int
    visual_task: str
    audio_task: str = ""
    on_screen_text: str = ""
    tool_hint: str = ""


@dataclass(frozen=True)
class VideoPlan:
    title: str
    request: VideoRequest
    assumptions: tuple[str, ...]
    routes: tuple[ProductionRoute, ...]
    timeline: tuple[TimelineItem, ...]
    assets: tuple[Asset, ...] = ()
    deliverables: tuple[str, ...] = field(default_factory=tuple)

    @property
    def target_duration_seconds(self) -> int | None:
        return self.request.target_duration_seconds
