# cad-3d

Parametric 3D modeling with [CadQuery](https://cadquery.readthedocs.io/en/latest/) — code-first CAD in Python.

## Run

```bash
uv run main.py
```

Exports STL + STEP into `out/` (gitignored — models are code, exports are build artifacts).

`main.py` is the starter: a parametric mounting plate (rounded corners, 4× M4 counterbored holes). Change the parameters at the top, re-run, re-export.

## Viewing models

- Quick look: open the `.stl` in macOS Quick Look / Preview.
- Interactive editing: [CQ-editor](https://github.com/CadQuery/CQ-editor) or the `jupyter-cadquery` viewer.
- `.step` is the lossless format for slicers/CAD interchange; `.stl` for direct printing.

## Stack

- Python 3.12 (pinned in `.python-version` — CadQuery's OCP wheels lag latest Python)
- uv for env + deps (`uv add <pkg>` to extend)
