"""blendr_prelude — runs first inside Blender, before the user script.

Two responsibilities:
  1. Make `import blendr_helpers`, `import blendr_runtime` work from any
     user script by injecting BLENDR_LIB_DIR into sys.path.
  2. Configure sensible default scene settings so even an empty user
     script produces something renderable.
"""
import os
import sys

_lib = os.environ.get("BLENDR_LIB_DIR")
if _lib and _lib not in sys.path:
    sys.path.insert(0, _lib)

import bpy  # noqa: E402
import blendr_runtime  # noqa: E402

# Apply CYCLES+CPU defaults to whatever scene exists (user script may override).
blendr_runtime.configure_preview_engine()
