"""Write one summary of the day to $MAKEFUN_OUTPUT_DIR/entry.txt.

The text lives in summary.txt beside this file, so the bytes the judge reads are
exactly the bytes committed here. No network, no clock, no randomness: both of
the grader's runs write the same bytes.

The gate reads exactly these bytes: UTF-8, 1 to 2000 code points, not only white
space.
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = "/output"

MIN_POINTS = 1
MAX_POINTS = 2000


def out_dir():
    """$MAKEFUN_OUTPUT_DIR, or the default when it is unset *or empty*.

    `os.environ.get(key, default)` only returns the default when the key is
    missing, so a variable exported as empty used to hand back "" and makedirs
    raised FileNotFoundError on it.
    """
    return os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUT


def check(text):
    """The gate's rule, checked without `assert`.

    `assert` is compiled away under `python3 -O`, and then a blank or oversized
    summary was written and the run still exited 0 — a silently empty entry
    instead of a failure.
    """
    if len(text) < MIN_POINTS:
        raise ValueError("summary is %d code points, under the %d minimum" % (len(text), MIN_POINTS))
    if len(text) > MAX_POINTS:
        raise ValueError("summary is %d code points, over the %d maximum" % (len(text), MAX_POINTS))
    if not text.strip():
        raise ValueError("summary is blank")


def summary_path():
    return os.path.join(HERE, "summary.txt")


def read_summary():
    with open(summary_path(), encoding="utf-8") as fh:
        return fh.read()


def write_entry(text, directory):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return path


def main():
    text = read_summary()
    check(text)
    write_entry(text, out_dir())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
