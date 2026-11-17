---
name: horror-2d-cartoon-shorts-mcp
description: Creates 60-second vertical 2D horror cartoon shorts (60 beats, 1 FPS) using local puppet rigs, free Edge-TTS, procedural horror SFX, and Render HTTP download links.
---

# 60-Second Horror 2D Cartoon Shorts Producer

## Core Format & Pacing Rules
1. **Strict 1-Second Cadence:** Every 60-second video MUST contain **60 distinct beats** (`second` `0` through `59`), changing every 1.0 second.
2. **Voiceover Word Count:** Write a tight **135–150 word** horror narration script (~2.3 to 2.5 words per second).
3. **5-Beat Horror Arc:**
   * **Seconds 00–05 (The Dread Hook):** Open with *"Did you know..."* or an eerie rule/warning.
   * **Seconds 06–21 (Eerie Setup):** Establish the setting (`corridor`, `security_room`, `woods`) and concrete clues.
   * **Seconds 22–40 (Uncanny Escalation):** Introduce the `shadow_stalker` (`peeking` / `lurking`) while the `night_guard` reacts (`nervous` -> `confused`).
   * **Seconds 41–54 (The Jump Climax):** Trigger `lunging` stalker pose, `shocked` / `possessed` guard face, `shake` / `flash_red` FX, and `stinger` SFX.
   * **Seconds 55–59 (Looping Outro):** Close with *"One thing is clear..."* so the ending loops seamlessly back into Second 00.

## Mandatory MCP Execution Workflow
1. Call `init_horror_project(topic)` to create the workspace.
2. Call `build_horror_assets(project_slug)` to generate the 2D horror backgrounds and layered Night Guard & Shadow Stalker puppet sprites.
3. Write the 135–150 word horror narration script and 60-second beat array (`second` 0..59), then call `save_horror_short_json(project_slug, title, description, full_voiceover, beats_json)`.
4. Call `generate_horror_voiceover(project_slug)` to synthesize `voice.mp3` via free Edge-TTS.
5. Call `render_horror_stage_video(project_slug)` to render `render.mp4` and return the direct HTTP download URL.
