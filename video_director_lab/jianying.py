from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from video_director_lab.models import VideoPlan


def build_jianying_draft_spec(
    plan: VideoPlan,
    draft_name: str,
    draft_root: Path | None = None,
) -> dict[str, Any]:
    """Build an editable draft execution spec for pyJianYingDraft.

    The spec is intentionally tool-facing JSON. A later adapter can translate
    this into concrete pyJianYingDraft API calls once the target Jianying version
    and draft directory are known.
    """

    video_clips = []
    text_clips = []
    for index, item in enumerate(plan.timeline, start=1):
        clip_id = f"clip-{index:02d}"
        video_clips.append(
            {
                "id": clip_id,
                "start": item.start_seconds,
                "end": item.end_seconds,
                "visual_task": item.visual_task,
                "tool_hint": item.tool_hint or "pyJianYingDraft",
                "source": None,
            }
        )

        if item.on_screen_text:
            text_clips.append(
                {
                    "id": f"text-{index:02d}",
                    "start": item.start_seconds,
                    "end": item.end_seconds,
                    "text": item.on_screen_text,
                    "style": "safe-area subtitle",
                }
            )

    return {
        "draft": {
            "name": draft_name,
            "editable": True,
            "draft_root": str(draft_root) if draft_root else None,
            "aspect_ratio": plan.request.aspect_ratio,
            "duration_seconds": plan.target_duration_seconds,
        },
        "tracks": [
            {"type": "video", "name": "V1", "clips": video_clips},
            {"type": "text", "name": "T1", "clips": text_clips},
        ],
        "assets": [
            {"path": str(asset.path), "kind": asset.kind, "role": asset.role}
            for asset in plan.assets
        ],
        "handoff": {
            "open_in_jianying": True,
            "auto_export": "only when supported by local Jianying version",
            "verification": (
                "草稿目录中出现新草稿；素材路径可访问；如导出成片，继续用 ffprobe 检查。"
            ),
        },
    }


def write_jianying_draft_spec(spec: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def render_pyjianying_script(spec: dict[str, Any]) -> str:
    """Render a Python script that creates a Jianying draft from a spec.

    The generated script uses public pyJianYingDraft entrypoints documented by
    the project: DraftFolder.create_draft, TrackSpec, VideoSegment, TextSegment,
    add_segment, and save. Clips without a concrete media source are left as
    comments, because pyJianYingDraft cannot create a video segment without a
    local asset path.
    """

    draft_info = spec["draft"]
    width, height = _canvas_size(draft_info.get("aspect_ratio", "9:16"))
    draft_root = draft_info.get("draft_root") or "<JianyingPro Drafts path>"
    draft_name = draft_info["name"]

    lines = [
        "from pathlib import Path",
        "",
        "import pyJianYingDraft as draft",
        "from pyJianYingDraft import trange",
        "",
        f"draft_folder = draft.DraftFolder(r{json.dumps(str(draft_root), ensure_ascii=False)})",
        f"script = draft_folder.create_draft({json.dumps(draft_name, ensure_ascii=False)}, {width}, {height})",
        'script.append_track(draft.TrackSpec(draft.TrackType.video, "V1"))',
        'script.append_track(draft.TrackSpec(draft.TrackType.text, "T1"))',
        "",
    ]

    for track in spec.get("tracks", []):
        if track["type"] == "video":
            lines.extend(_render_video_track(track))
        if track["type"] == "text":
            lines.extend(_render_text_track(track))

    lines.extend(["script.save()", ""])
    return "\n".join(lines)


def write_pyjianying_script(spec: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_pyjianying_script(spec), encoding="utf-8")
    return output_path


def _render_video_track(track: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for clip in track.get("clips", []):
        source = clip.get("source")
        start = _seconds_to_label(clip["start"])
        duration = _seconds_to_label(clip["end"] - clip["start"])
        if not source:
            lines.append(
                f"# {clip['id']}: add a video/image source for {start}-{clip['end']}s "
                f"({clip.get('visual_task', 'visual task')})"
            )
            continue
        variable = clip["id"].replace("-", "_")
        lines.append(f"{variable} = draft.VideoSegment(r{source!r}, trange({start!r}, {duration!r}))")
        lines.append(f'script.add_segment({variable}, "V1")')
    if lines:
        lines.append("")
    return lines


def _render_text_track(track: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for clip in track.get("clips", []):
        start = _seconds_to_label(clip["start"])
        duration = _seconds_to_label(clip["end"] - clip["start"])
        variable = clip["id"].replace("-", "_")
        lines.append(
            f"{variable} = draft.TextSegment({clip['text']!r}, trange({start!r}, {duration!r}))"
        )
        lines.append(f'script.add_segment({variable}, "T1")')
    if lines:
        lines.append("")
    return lines


def _canvas_size(aspect_ratio: str) -> tuple[int, int]:
    if aspect_ratio == "9:16":
        return 1080, 1920
    if aspect_ratio == "1:1":
        return 1080, 1080
    return 1920, 1080


def _seconds_to_label(seconds: int | float) -> str:
    if float(seconds).is_integer():
        return f"{int(seconds)}s"
    return f"{seconds}s"
