# merge_ipynb.py  (outputs kept)
import sys
from copy import deepcopy
from pathlib import Path
import nbformat as nbf

# Usage:
#   python merge_ipynb.py part_1.ipynb part_2.ipynb HW2_all.ipynb
# Optional:
#   add --clear-outputs at the end if you ever want a clean merge

if len(sys.argv) < 4:
    print("Usage: python merge_ipynb.py <in1.ipynb> <in2.ipynb> ... <out.ipynb> [--clear-outputs]")
    sys.exit(1)

args = sys.argv[1:]
clear_outputs = False
if args[-1] == "--clear-outputs":
    clear_outputs = True
    args = args[:-1]

*in_paths, out_path = args  # <-- correct unpacking

merged = nbf.v4.new_notebook()
first = True

for p in in_paths:
    p = Path(p)
    nb = nbf.read(str(p), as_version=4)
    if first:
        merged.metadata = deepcopy(nb.metadata)
        first = False
    else:
        # merge widget metadata if present so interactive outputs survive
        for k in ("widgets",):
            if k in nb.metadata:
                merged.metadata.setdefault(k, {})
                merged.metadata[k].update(deepcopy(nb.metadata[k]))

    # visual divider so you can see where each file starts
    merged.cells.append(nbf.v4.new_markdown_cell(f"# ---\n### {p.name}\n"))

    for cell in nb.cells:
        c = deepcopy(cell)
        if clear_outputs and c.cell_type == "code":
            c.outputs = []
            c.execution_count = None
        merged.cells.append(c)

nbf.write(merged, out_path)
print(
    f"Merged {len(in_paths)} notebooks → {out_path} with {len(merged.cells)} cells. "
    f"{'Outputs kept.' if not clear_outputs else 'Outputs cleared.'}"
)
