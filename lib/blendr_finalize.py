"""blendr_finalize — runs last inside Blender, after the user script.

Saves the .blend and renders a preview unless the user opted out.
Imports happen here (not at module load) so user scripts can mutate
blendr_runtime.state if they need to.
"""
import blendr_runtime
blendr_runtime.finalize()
