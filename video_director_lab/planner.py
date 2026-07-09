from __future__ import annotations

import re
from pathlib import Path

from video_director_lab.models import (
    Asset,
    AssetKind,
    ProductionRoute,
    TimelineItem,
    VideoPlan,
    VideoRequest,
)


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
DOCUMENT_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".docx", ".md", ".txt"}


def build_plan(request: VideoRequest) -> VideoPlan:
    duration = request.target_duration_seconds or _infer_duration(request.brief) or 60
    assets = tuple(_classify_asset(path) for path in request.source_files)
    routes = _select_routes(request, assets)
    timeline = _build_default_timeline(request, duration, routes)
    deliverables = _select_deliverables(request, routes)

    return VideoPlan(
        title=_make_title(request.brief),
        request=request,
        assumptions=_build_assumptions(request, duration),
        routes=routes,
        timeline=timeline,
        assets=assets,
        deliverables=deliverables,
    )


def _select_routes(request: VideoRequest, assets: tuple[Asset, ...]) -> tuple[ProductionRoute, ...]:
    routes: list[ProductionRoute] = []
    formats = {item.lower() for item in request.delivery_formats}
    brief = request.brief.lower()
    has_video_or_audio = any(asset.kind in {"video", "audio"} for asset in assets)

    if request.wants_editable_draft or "jianying" in formats or "剪映" in request.brief:
        routes.append(
            ProductionRoute(
                name="pyJianYingDraft",
                purpose="生成可在剪映中继续编辑的草稿工程",
                required_tools=("Python", "pyJianYingDraft", "剪映"),
                readiness="needs_tool",
                output="剪映草稿目录",
            )
        )

    if request.wants_render or _looks_like_code_motion(brief):
        routes.append(
            ProductionRoute(
                name="Remotion",
                purpose="生成代码驱动的界面动画、数据动效和字幕包装",
                required_tools=("Node.js", "npm", "Remotion"),
                readiness="needs_tool",
                output="Remotion project / rendered mp4",
            )
        )

    if has_video_or_audio or "mp4" in formats or "mov" in formats:
        routes.append(
            ProductionRoute(
                name="ffmpeg",
                purpose="转码、拼接、抽帧、音频合成和成片质检",
                required_tools=("ffmpeg", "ffprobe"),
                readiness="needs_tool",
                output="mp4 / mov / probe report",
            )
        )

    if _looks_like_ai_video(request.brief):
        routes.append(
            ProductionRoute(
                name="AI video tool",
                purpose="生成真实场景、人物动作、环境氛围或概念镜头",
                required_tools=("user-selected AI video service",),
                readiness="needs_confirmation",
                output="generated clips / prompts",
            )
        )

    if not routes:
        routes.append(
            ProductionRoute(
                name="planning",
                purpose="先整理剪辑结构、素材清单和执行路线",
                required_tools=(),
                readiness="planning_only",
                output="edit brief / timeline",
            )
        )

    return tuple(routes)


def _build_default_timeline(
    request: VideoRequest,
    duration: int,
    routes: tuple[ProductionRoute, ...],
) -> tuple[TimelineItem, ...]:
    first = max(3, min(5, duration // 10))
    middle_end = max(first + 1, duration - max(6, duration // 8))
    default_tool = routes[0].name if routes else ""

    return (
        TimelineItem(
            start_seconds=0,
            end_seconds=first,
            visual_task="建立第一屏钩子，明确观众为什么要继续看",
            audio_task="直接进入问题或结果，不做冗长铺垫",
            on_screen_text="核心钩子",
            tool_hint=default_tool,
        ),
        TimelineItem(
            start_seconds=first,
            end_seconds=middle_end,
            visual_task="展开主要信息节拍，穿插素材、界面、数据或演示镜头",
            audio_task="按一条主线解释，不把所有素材都塞进来",
            on_screen_text="分段屏幕字",
            tool_hint=default_tool,
        ),
        TimelineItem(
            start_seconds=middle_end,
            end_seconds=duration,
            visual_task="收束观点或交付下一步行动",
            audio_task="给出明确结论或下一步",
            on_screen_text="结论 / 下一步",
            tool_hint=default_tool,
        ),
    )


def _select_deliverables(
    request: VideoRequest,
    routes: tuple[ProductionRoute, ...],
) -> tuple[str, ...]:
    deliverables = set(request.delivery_formats)
    route_names = {route.name for route in routes}

    if "pyJianYingDraft" in route_names:
        deliverables.add("jianying")
    if "Remotion" in route_names:
        deliverables.add("remotion-project")
    if "ffmpeg" in route_names:
        deliverables.add("mp4")

    deliverables.add("timeline")
    deliverables.add("asset-checklist")
    return tuple(sorted(deliverables))


def _build_assumptions(request: VideoRequest, duration: int) -> tuple[str, ...]:
    assumptions = [f"目标时长按 {duration} 秒处理。"]
    if not request.platform:
        assumptions.append("平台未指定，默认按通用短视频流程处理。")
    if request.wants_editable_draft:
        assumptions.append("用户需要可继续编辑的草稿工程。")
    return tuple(assumptions)


def _classify_asset(path: Path) -> Asset:
    suffix = path.suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        kind: AssetKind = "video"
    elif suffix in AUDIO_EXTENSIONS:
        kind = "audio"
    elif suffix in IMAGE_EXTENSIONS:
        kind = "image"
    elif suffix in DOCUMENT_EXTENSIONS:
        kind = "document"
    elif suffix in {".srt", ".vtt"}:
        kind = "subtitle"
    else:
        kind = "unknown"
    return Asset(path=path, kind=kind)


def _infer_duration(brief: str) -> int | None:
    match = re.search(r"(\d{1,3})\s*(?:秒|s|sec|seconds)", brief, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _make_title(brief: str) -> str:
    title = re.sub(r"\s+", " ", brief).strip()
    return title[:36] or "untitled-video"


def _looks_like_code_motion(brief: str) -> bool:
    keywords = ("ui", "interface", "dashboard", "数据", "看板", "界面", "动画", "流程", "代码")
    return any(keyword in brief for keyword in keywords)


def _looks_like_ai_video(brief: str) -> bool:
    keywords = ("真实场景", "人物", "镜头运动", "氛围", "可灵", "runway", "pika", "hyperframes", "即梦")
    return any(keyword.lower() in brief.lower() for keyword in keywords)
