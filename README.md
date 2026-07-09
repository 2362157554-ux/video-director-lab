# Video Director Lab

Experimental Python foundation for a natural-language video director workflow.

## What exists

- Build structured video production plans from messy briefs.
- Route work across planning, Remotion, ffmpeg, AI video tools, and pyJianYingDraft.
- Check local production tools such as Node.js, npm, Python, ffmpeg, and pyJianYingDraft.
- Generate pyJianYingDraft-oriented draft specs and Python script skeletons.
- Inspect exported media with ffprobe when available.

## Quick start

```powershell
python -m pytest
python -m video_director_lab.cli plan "做一条60秒教育产品介绍视频，需要剪映里继续编辑" --duration 60 --editable-draft --format jianying
python -m video_director_lab.cli check-env
python -m video_director_lab.cli jianying-spec "做一条30秒产品介绍视频" --draft-name product-intro-v1 --output out/jianying-spec.json --script-output out/create_jianying_draft.py
```

## Current scope

This is not a full video editor yet. It is the code foundation for planning, execution routing, editable draft handoff, and quality gates.
