from video_director_lab.jianying import build_jianying_draft_spec, render_pyjianying_script
from video_director_lab.models import TimelineItem, VideoPlan, VideoRequest


def test_build_jianying_draft_spec_keeps_editable_tracks():
    request = VideoRequest(
        brief="做一个可继续编辑的短视频草稿。",
        target_duration_seconds=12,
        wants_editable_draft=True,
    )
    plan = VideoPlan(
        title="editable-short",
        request=request,
        assumptions=("用户需要剪映里继续编辑",),
        routes=(),
        timeline=(
            TimelineItem(
                start_seconds=0,
                end_seconds=6,
                visual_task="开头画面",
                audio_task="开头讲述",
                on_screen_text="开头字幕",
            ),
            TimelineItem(
                start_seconds=6,
                end_seconds=12,
                visual_task="收尾画面",
                audio_task="收尾讲述",
                on_screen_text="收尾字幕",
            ),
        ),
        assets=(),
        deliverables=("jianying",),
    )

    spec = build_jianying_draft_spec(plan, draft_name="editable-short-v1")

    assert spec["draft"]["name"] == "editable-short-v1"
    assert spec["draft"]["editable"] is True
    assert [track["type"] for track in spec["tracks"]] == ["video", "text"]
    assert len(spec["tracks"][0]["clips"]) == 2
    assert spec["tracks"][1]["clips"][0]["text"] == "开头字幕"


def test_render_pyjianying_script_uses_real_api_entrypoints():
    request = VideoRequest(
        brief="生成剪映草稿",
        target_duration_seconds=6,
        wants_editable_draft=True,
        aspect_ratio="9:16",
    )
    plan = VideoPlan(
        title="draft",
        request=request,
        assumptions=(),
        routes=(),
        timeline=(
            TimelineItem(
                start_seconds=0,
                end_seconds=6,
                visual_task="占位画面",
                on_screen_text="字幕",
            ),
        ),
        assets=(),
        deliverables=("jianying",),
    )
    spec = build_jianying_draft_spec(plan, draft_name="draft-v1")

    script = render_pyjianying_script(spec)

    assert "draft.DraftFolder" in script
    assert 'create_draft("draft-v1", 1080, 1920)' in script
    assert "draft.TextSegment" in script
    assert "script.save()" in script
