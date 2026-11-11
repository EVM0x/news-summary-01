import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# The gate reads exactly these bytes: UTF-8, 1 to 2000 code points, not only white space.
text = open(os.path.join(HERE, "summary.txt"), encoding="utf-8").read()
assert 1 <= len(text) <= 2000, "summary is %d code points" % len(text)
assert text.strip(), "summary is blank"

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "entry.txt"), "w", encoding="utf-8", newline="") as f:
    f.write(text)
