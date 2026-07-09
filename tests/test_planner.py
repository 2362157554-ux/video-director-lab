from video_director_lab.models import VideoRequest
from video_director_lab.planner import build_plan


def test_build_plan_routes_to_editable_jianying_draft():
    request = VideoRequest(
        brief="做一条60秒教育产品介绍视频，需要最后能在剪映里继续调字幕和素材。",
        target_duration_seconds=60,
        aspect_ratio="9:16",
        platform="xiaohongshu",
        wants_editable_draft=True,
        delivery_formats=("jianying", "mp4"),
    )

    plan = build_plan(request)

    route_names = {route.name for route in plan.routes}
    assert "pyJianYingDraft" in route_names
    assert "ffmpeg" in route_names
    assert plan.target_duration_seconds == 60
    assert plan.timeline[0].start_seconds == 0
    assert plan.timeline[-1].end_seconds == 60


def test_build_plan_routes_ui_motion_to_remotion():
    request = VideoRequest(
        brief="把产品界面、数据看板和流程闭环做成代码动画。",
        target_duration_seconds=30,
        aspect_ratio="16:9",
        wants_render=True,
    )

    plan = build_plan(request)

    assert any(route.name == "Remotion" for route in plan.routes)
    assert any(item.visual_task for item in plan.timeline)
