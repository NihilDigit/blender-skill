# Human-in-the-loop with headless Blender

Headless Blender is great for batch work but a poor fit for visual iteration without a feedback loop. This skill closes that gap by **always producing a preview PNG that the agent reads back into its own context**, so the agent sees what it built before talking to the human.

## The five HITL primitives

### 1. Auto preview (default `blendr run`)

After each script run, render a single 512×512 PNG to `preview.png`. Fast (~1s), enough to verify "did the right thing get built." The agent reads it via the Read tool, the image enters the multimodal context, and the agent self-corrects without asking the human.

When to use: every iteration. This is the default.

### 2. Contact sheet (`blendr sheet`)

Render front / right / top / iso into a 2×2 grid. Catches geometry bugs that a single view misses (e.g., the back face is wrong, or the model is hollow from above).

When to use: complex geometry, after major structural changes, when single preview "looks fine" but you suspect there's a problem.

### 3. Turntable (`blendr turntable`)

16-frame orbit around the origin. Each frame saved as a PNG in `turntable/`. Combine externally with `convert -delay 8 frame_*.png tt.gif` if you want a GIF.

When to use: showing the user a 3D model thoroughly; for animation review the human will eventually need to see motion anyway.

### 4. Open in GUI (`blendr open`)

Sometimes the human just needs to see it in 3D and turn it around. The wrapper opens the saved `.blend` in interactive Blender. The human can then zoom, rotate, edit materials, and either ask for changes or save and continue.

When to use: critical milestones, when material/lighting nuance matters, before exporting a "final" deliverable.

### 5. Inspect (`blendr inspect`)

Print scene summary (object count, polycount, camera, materials) without rendering. Cheap (~0.3s).

When to use: debugging "what did my script actually build", before committing to a full render.

## Suggested loop

```
                ┌──────────────┐
                │  user prompt │
                └──────┬───────┘
                       v
              ┌────────────────┐
              │ write script   │
              └──────┬─────────┘
                     v
              ┌──────────────────────┐
              │ blendr run script.py │
              └──────┬───────────────┘
                     v
              ┌────────────────────┐
              │ Read preview.png   │   ← agent self-check
              └──────┬─────────────┘
                     v
              ┌────────────────────┐
              │  looks right?      │
              └─┬─────────────┬────┘
            yes │             │ no
                v             v
          show user      edit script
                              │
                              └─ back to blendr run
```

## When to escalate to the human

Don't ask the human after every iteration — that defeats the agent loop. Ask when:

- The user's spec is ambiguous and the choice you'd make is non-obvious ("realistic or stylised?", "single material or PBR?")
- You've rendered 3+ iterations and they all look broken in the same way (probably a misunderstanding of the request)
- A subjective judgement is needed ("does this look like a skull to you?")
- About to do something irreversible (`blendr promote`, modifying `projects/`, exporting a "final" deliverable)

## Tips for fast loops

- Keep `--samples 16` for previews. Bumping to 256 makes each iter feel sluggish.
- Use `bh.cube` / `bh.plane` / `bh.mesh_from_pydata` instead of operators — they're faster and don't have context issues.
- The first run is always slowest (cold cache). Subsequent runs are ~30% faster.
- If you're tweaking only material parameters, consider modifying the `.blend` directly rather than re-running the whole script.

## Tips for users (humans)

- Use `blendr du` to see how much disk you're consuming. Auto-prune kicks in at 50 iters.
- Use `blendr promote <iter> <name>` to keep iters you like. Promoted iters live in `projects/` and are never pruned.
- The agent will Read every preview itself. You don't need to ask "show me what you made" — it'll be in the response automatically.
