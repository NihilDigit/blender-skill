#!/usr/bin/env bash
# Install blender-skill into ~/.claude/skills and put `blendr` on PATH.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="${HOME}/.claude/skills/blender-skill"
BIN_DIR="${HOME}/.local/bin"

# 1. Sanity check: blender is installed
if ! command -v blender >/dev/null 2>&1; then
    echo "ERROR: blender not found in PATH. Install it first:"
    echo "  Arch:   sudo pacman -S blender"
    echo "  macOS:  brew install --cask blender"
    echo "  Ubuntu: sudo apt install blender"
    exit 1
fi

BLENDER_VER=$(blender --version 2>/dev/null | head -1 | awk '{print $2}')
echo "✓ blender: ${BLENDER_VER}"

# 2. Symlink the skill dir
mkdir -p "$(dirname "$SKILL_DIR")"
if [[ -L "$SKILL_DIR" || -e "$SKILL_DIR" ]]; then
    echo "→ replacing existing $SKILL_DIR"
    rm -rf "$SKILL_DIR"
fi
ln -s "$REPO_DIR" "$SKILL_DIR"
echo "✓ skill: $SKILL_DIR -> $REPO_DIR"

# 3. Symlink blendr CLI
mkdir -p "$BIN_DIR"
ln -sf "$REPO_DIR/bin/blendr" "$BIN_DIR/blendr"
echo "✓ blendr: $BIN_DIR/blendr -> $REPO_DIR/bin/blendr"

# 4. PATH check
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)  echo
        echo "WARN: $BIN_DIR is not on your PATH. Add it:"
        echo "  bash/zsh:  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        echo "  fish:      fish_add_path ~/.local/bin"
        ;;
esac

# 5. Run doctor
echo
"$BIN_DIR/blendr" doctor || true

cat <<EOF

Done. Try it out:
  blendr templates
  blendr new hello --name first-cube
  blendr run ~/blender-work/iters/iter_0001_first-cube/script.py
EOF
