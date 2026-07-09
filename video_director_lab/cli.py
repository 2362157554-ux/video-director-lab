from __future__ import annotations

import argparse
import json
from pathlib import Path

from video_director_lab.environment import run_environment_checks
from video_director_lab.jianying import (
    build_jianying_draft_spec,
    write_jianying_draft_spec,
    write_pyjianying_script,
)
from video_director_lab.models import VideoRequest
from video_director_lab.planner import build_plan
from video_director_lab.quality import inspect_media


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="video-director-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="Build a structured video production plan.")
    plan_parser.add_argument("brief")
    plan_parser.add_argument("--duration", type=int)
    plan_parser.add_argument("--aspect-ratio", default="9:16")
    plan_parser.add_argument("--platform", default="")
    plan_parser.add_argument("--source", action="append", default=[])
    plan_parser.add_argument("--format", action="append", default=[])
    plan_parser.add_argument("--editable-draft", action="store_true")
    plan_parser.add_argument("--render", action="store_true")
    plan_parser.add_argument("--json", action="store_true")

    env_parser = subparsers.add_parser("check-env", help="Check local video production tools.")
    env_parser.add_argument("--no-jianying", action="store_true")

    spec_parser = subparsers.add_parser(
        "jianying-spec",
        help="Write a pyJianYingDraft-oriented execution spec.",
    )
    spec_parser.add_argument("brief")
    spec_parser.add_argument("--draft-name", required=True)
    spec_parser.add_argument("--output", required=True)
    spec_parser.add_argument("--script-output")
    spec_parser.add_argument("--duration", type=int)
    spec_parser.add_argument("--source", action="append", default=[])

    quality_parser = subparsers.add_parser("quality", help="Inspect an exported media file.")
    quality_parser.add_argument("path")

    args = parser.parse_args(argv)

    if args.command == "plan":
        request = _request_from_args(args)
        plan = build_plan(request)
        if args.json:
            print(json.dumps(_plan_to_dict(plan), ensure_ascii=False, indent=2))
        else:
            _print_plan(plan)
        return 0

    if args.command == "check-env":
        checks = run_environment_checks(include_jianying=not args.no_jianying)
        for check in checks:
            status = "ok" if check.available else "missing"
            print(f"{status}\t{check.name}\t{check.command}\t{check.detail}")
        return 0 if all(check.available for check in checks) else 2

    if args.command == "jianying-spec":
        request = VideoRequest(
            brief=args.brief,
            target_duration_seconds=args.duration,
            wants_editable_draft=True,
            source_files=tuple(Path(item) for item in args.source),
            delivery_formats=("jianying",),
        )
        plan = build_plan(request)
        spec = build_jianying_draft_spec(plan, draft_name=args.draft_name)
        output_path = write_jianying_draft_spec(spec, Path(args.output))
        print(output_path)
        if args.script_output:
            print(write_pyjianying_script(spec, Path(args.script_output)))
        return 0

    if args.command == "quality":
        report = inspect_media(Path(args.path))
        print(json.dumps(report.__dict__ | {"path": str(report.path)}, ensure_ascii=False, indent=2))
        return 0 if report.exists else 2

    return 1


def _request_from_args(args: argparse.Namespace) -> VideoRequest:
    return VideoRequest(
        brief=args.brief,
        target_duration_seconds=args.duration,
        aspect_ratio=args.aspect_ratio,
        platform=args.platform,
        wants_editable_draft=args.editable_draft,
        wants_render=args.render,
        source_files=tuple(Path(item) for item in args.source),
        delivery_formats=tuple(args.format),
    )


def _print_plan(plan) -> None:
    print(f"# {plan.title}")
    print()
    for assumption in plan.assumptions:
        print(f"- 假设：{assumption}")
    print()
    print("## Routes")
    for route in plan.routes:
        print(f"- {route.name}: {route.purpose} -> {route.output}")
    print()
    print("## Timeline")
    for item in plan.timeline:
        print(f"- {item.start_seconds:02d}-{item.end_seconds:02d}s {item.visual_task}")


def _plan_to_dict(plan) -> dict:
    return {
        "title": plan.title,
        "assumptions": list(plan.assumptions),
        "routes": [route.__dict__ for route in plan.routes],
        "timeline": [item.__dict__ for item in plan.timeline],
        "assets": [
            {"path": str(asset.path), "kind": asset.kind, "role": asset.role}
            for asset in plan.assets
        ],
        "deliverables": list(plan.deliverables),
    }


if __name__ == "__main__":
    raise SystemExit(main())
