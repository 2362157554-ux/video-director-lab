from video_director_lab.environment import ToolCheck, summarize_missing_tools


def test_summarize_missing_tools_only_reports_missing_items():
    checks = (
        ToolCheck(name="Node.js", command="node -v", available=True, detail="v20.0.0"),
        ToolCheck(name="ffmpeg", command="ffmpeg -version", available=False, detail="not found"),
        ToolCheck(
            name="pyJianYingDraft",
            command='python -c "import pyJianYingDraft"',
            available=False,
            detail="module missing",
        ),
    )

    missing = summarize_missing_tools(checks)

    assert missing == ("ffmpeg", "pyJianYingDraft")
