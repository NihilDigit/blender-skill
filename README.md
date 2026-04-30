# blender-skill

A headless [Blender](https://www.blender.org/) workflow optimised for AI agents (e.g. [Claude Code](https://claude.com/claude-code)). Drives Blender from a small CLI (`blendr`), auto-renders a preview after every script run, and organises outputs into versioned iteration folders so the agent and the human can both follow what changed.

The key design idea: **the agent reads its own preview PNG back into context after every run**, closing the human-in-the-loop gap that headless Blender normally suffers from. The agent self-corrects before showing the human, and the human only needs to look when the agent says "I think this is right".

## Why headless instead of MCP?

Two reasonable architectures exist:

| | Headless CLI (this skill) | [Official Blender MCP server](https://www.blender.org/lab/mcp-server/) |
|---|---|---|
| Setup | install Blender, clone, install.sh | install Blender, install addon, enable, keep open |
| Blender state | cold-start each run (~0.5s) | persistent session |
| Reproducibility | strong — script is the artifact | weaker — relies on session state |
| Best for | scripted/agent workflows, CI, batch | interactive iteration with viewport |
| Security | normal sandboxing | unsandboxed RCE in addon |

This skill is **not a replacement** for the MCP server when you want a live Blender session. It's a different — and for AI-agent workflows, often better — way of working.

## Quick start

```bash
# 1. Install Blender 5.1+
sudo pacman -S blender    # arch / cachyos
brew install --cask blender    # macOS
# ...

# 2. Clone and install the skill
git clone https://github.com/<you>/blender-skill ~/projects/blender-skill
cd ~/projects/blender-skill
./install.sh

# 3. Verify
blendr doctor

# 4. Run a template
blendr new hello --name first
blendr run ~/blender-work/iters/iter_0001_first/script.py
```

The agent (Claude Code etc.) discovers the skill via `~/.claude/skills/blender-skill/SKILL.md` and invokes `blendr` from the user's PATH (the install script symlinks it to `~/.local/bin`).

## What's in the box

```
blender-skill/
├── SKILL.md              # the skill manifest the agent reads
├── README.md             # this file
├── LICENSE               # MIT
├── install.sh            # symlinks skill into ~/.claude/skills, blendr into ~/.local/bin
├── bin/
│   └── blendr            # CLI wrapper (pure-stdlib Python, no deps)
├── lib/                  # loaded inside Blender's bundled Python
│   ├── blendr_prelude.py     # runs first, sets up sys.path
│   ├── blendr_runtime.py     # default scene config + finalize hook
│   ├── blendr_helpers.py     # bpy convenience API
│   ├── blendr_preview.py     # contact sheet / turntable
│   └── blendr_finalize.py    # runs last, saves .blend + renders preview
├── templates/            # starter scripts: hello / procedural mesh / PBR / GLB export
└── docs/
    ├── HITL.md           # human-in-the-loop loop pattern
    ├── PITFALLS.md       # gotchas when scripting Blender headlessly
    └── EXAMPLES.md       # more example scripts
```

## CLI

```
blendr run <script.py>          run script + auto preview (the default loop)
blendr render <script.py>       same as run, force preview
blendr sheet <script.py>        4-view 2x2 contact sheet (front/right/top/iso)
blendr turntable <script.py>    16-frame orbital sequence

blendr inspect <.blend>         scene summary (objects, polys, camera)
blendr open <iter|.blend>       open in Blender GUI
blendr promote <iter> <name>    keep an iter forever (move to projects/)

blendr prune [--keep N]         trash old iters
blendr du                       disk usage
blendr templates                list bundled templates
blendr new <template>           start a fresh iter from a template
blendr doctor                   health check
```

## Output layout

Every run lives in a fresh, numbered directory:

```
$BLENDER_WORK_DIR/                 (default ~/blender-work)
├── iters/
│   ├── iter_0001_hello/
│   │   ├── script.py              copy of the script that produced this
│   │   ├── scene.blend            saved Blender file
│   │   └── preview.png            auto-rendered preview
│   └── iter_0042_skull/
│       └── ...
├── projects/                      promoted iters live here, never pruned
├── renders/                       full-quality renders (manually managed)
├── assets/                        downloaded HDRIs / models
└── cache/                         temp files
```

## Configuration

Override via environment variables:

| Var | Default | Purpose |
|---|---|---|
| `BLENDER_BIN` | `which blender` | Path to blender executable |
| `BLENDER_WORK_DIR` | `~/blender-work` | Output root |
| `BLENDR_KEEP` | `50` | Iters to keep before auto-pruning |

Example, putting outputs on a data disk:

```bash
echo 'set -gx BLENDER_WORK_DIR /mnt/data/blender-work' >> ~/.config/fish/config.fish
```

## Writing scripts

All templates and your own scripts should follow this shape:

```python
import blendr_helpers as bh

bh.empty_scene()                  # wipe defaults

# Build geometry using bpy.data.* (NOT bpy.ops.mesh.primitive_*)
cube = bh.cube("Hero")

# Material
mat = bh.principled("Red", base_color=(0.85, 0.15, 0.15, 1.0))
bh.assign_material(cube, mat)

# Camera + lighting
bh.add_camera(location=(4, -4, 3), look_at=(0, 0, 0))
bh.three_point_light()
bh.set_world_color((0.05, 0.05, 0.06))

# That's it — blendr_finalize will save the .blend and render preview.png
```

See `docs/EXAMPLES.md` for richer examples and `docs/PITFALLS.md` for the most common headless-Blender footguns.

## Contributing

PRs welcome. Two areas of particular interest:

1. **More helpers**: subdivision modifier, modifier stacks, geometry nodes scaffolding
2. **More templates**: especially "everyday" stuff like product mockups, isometric scenes, character rigs

Smoke test before submitting:

```bash
./install.sh
blendr doctor
blendr run templates/hello.py && \
blendr run templates/procedural_mesh.py && \
blendr run templates/pbr_material.py && \
blendr sheet templates/hello.py
```

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

Built atop [Blender's Python API](https://docs.blender.org/api/current/). Inspired by the Blender MCP discussion in the [Blender developer forum](https://devtalk.blender.org/t/i-would-love-to-help-write-the-mcp-for-blender-can-i-get-involved-in-that/43367) and existing MCP implementations like [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp), but takes a deliberately different (script-based, not session-based) tack.
