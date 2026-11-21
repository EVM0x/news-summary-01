"""Tests for the entry gate.

The whole program is one contract — "UTF-8, 1 to 2000 code points, not only
white space" — and nothing checked it. Three defects fell out of writing these:

  1. `MAKEFUN_OUTPUT_DIR=` (exported but empty) crashed with FileNotFoundError on
     makedirs("") instead of falling back to /output, because
     `os.environ.get(key, default)` only defaults when the key is *missing*.
  2. The gate was `assert`, which `python3 -O` compiles away: the run then wrote
     a 0-byte entry.txt and exited 0 — a silently empty submission.
  3. The asserts ran at module scope, so importing main.py executed the program
     and wrote to /output. Nothing could be imported, let alone tested.

Run: python3 -m unittest discover -s tests -v
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import main  # noqa: E402


class OutDirTest(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.get("MAKEFUN_OUTPUT_DIR")
        self.addCleanup(self._restore)

    def _restore(self):
        if self._saved is None:
            os.environ.pop("MAKEFUN_OUTPUT_DIR", None)
        else:
            os.environ["MAKEFUN_OUTPUT_DIR"] = self._saved

    def test_an_unset_variable_means_the_default(self):
        os.environ.pop("MAKEFUN_OUTPUT_DIR", None)
        self.assertEqual(main.out_dir(), "/output")

    def test_an_empty_variable_also_means_the_default(self):
        # The regression: this used to be "" and makedirs("") raised.
        os.environ["MAKEFUN_OUTPUT_DIR"] = ""
        self.assertEqual(main.out_dir(), "/output")

    def test_a_set_variable_is_used_as_given(self):
        os.environ["MAKEFUN_OUTPUT_DIR"] = "/tmp/somewhere"
        self.assertEqual(main.out_dir(), "/tmp/somewhere")


class CheckTest(unittest.TestCase):
    def test_one_code_point_is_enough(self):
        self.assertIsNone(main.check("x"))

    def test_two_thousand_code_points_is_still_allowed(self):
        self.assertIsNone(main.check("x" * 2000))

    def test_zero_code_points_is_refused(self):
        with self.assertRaises(ValueError):
            main.check("")

    def test_two_thousand_and_one_is_refused(self):
        with self.assertRaises(ValueError):
            main.check("x" * 2001)

    def test_white_space_only_is_refused(self):
        for blank in (" ", "\n", "\t", "  \n\t  "):
            with self.assertRaises(ValueError):
                main.check(blank)

    def test_the_limit_counts_code_points_not_bytes(self):
        # 2000 "é" is 4000 UTF-8 bytes but 2000 code points, which is what the
        # gate says it measures.
        self.assertIsNone(main.check("\u00e9" * 2000))

    def test_an_astral_character_counts_as_one_code_point(self):
        self.assertIsNone(main.check("\U0001f600" * 2000))
        with self.assertRaises(ValueError):
            main.check("\U0001f600" * 2001)

    def test_the_error_says_which_way_it_failed(self):
        with self.assertRaises(ValueError) as low:
            main.check("")
        self.assertIn("minimum", str(low.exception))
        with self.assertRaises(ValueError) as high:
            main.check("x" * 2001)
        self.assertIn("maximum", str(high.exception))


class CommittedSummaryTest(unittest.TestCase):
    def test_the_committed_summary_passes_its_own_gate(self):
        main.check(main.read_summary())

    def test_the_committed_summary_is_utf8(self):
        with open(main.summary_path(), "rb") as fh:
            raw = fh.read()
        self.assertEqual(raw.decode("utf-8").encode("utf-8"), raw)


class WriteTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_the_entry_is_byte_identical_to_the_summary(self):
        text = main.read_summary()
        path = main.write_entry(text, self.dir)
        with open(path, "rb") as fh:
            written = fh.read()
        with open(main.summary_path(), "rb") as fh:
            committed = fh.read()
        self.assertEqual(written, committed)

    def test_a_missing_output_directory_is_created(self):
        nested = os.path.join(self.dir, "a", "b")
        path = main.write_entry("hello", nested)
        self.assertTrue(os.path.isfile(path))

    def test_the_file_is_called_entry_txt(self):
        path = main.write_entry("hello", self.dir)
        self.assertEqual(os.path.basename(path), "entry.txt")

    def test_newlines_are_written_through_untouched(self):
        path = main.write_entry("a\r\nb\nc", self.dir)
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), b"a\r\nb\nc")


class ProcessTest(unittest.TestCase):
    """Run the program the way the grader does: as a script."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.box = os.path.join(self.dir, "box")
        os.makedirs(self.box)
        shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(self.box, "main.py"))
        self.out = os.path.join(self.dir, "out")

    def write_summary(self, text):
        with open(os.path.join(self.box, "summary.txt"), "w", encoding="utf-8") as fh:
            fh.write(text)

    def run_script(self, *flags, env_extra=None):
        env = dict(os.environ)
        env["MAKEFUN_OUTPUT_DIR"] = self.out
        env.update(env_extra or {})
        return subprocess.run(
            [sys.executable, *flags, os.path.join(self.box, "main.py")],
            capture_output=True, text=True, env=env, timeout=60,
        )

    def test_a_valid_summary_is_written_and_the_run_succeeds(self):
        self.write_summary("A fine summary.\n")
        done = self.run_script()
        self.assertEqual(done.returncode, 0, done.stderr)
        with open(os.path.join(self.out, "entry.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "A fine summary.\n")

    def test_a_blank_summary_fails_loudly(self):
        self.write_summary("")
        done = self.run_script()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("minimum", done.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.out, "entry.txt")))

    def test_an_oversized_summary_fails_loudly(self):
        self.write_summary("x" * 2001)
        done = self.run_script()
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("maximum", done.stderr)

    def test_optimised_mode_still_enforces_the_gate(self):
        # `python3 -O` drops every assert, which is what let a blank summary be
        # written and reported as success.
        self.write_summary("")
        done = self.run_script("-O")
        self.assertNotEqual(done.returncode, 0, "the gate vanished under -O")
        self.assertFalse(
            os.path.exists(os.path.join(self.out, "entry.txt")),
            "a blank entry was written under -O",
        )

    def test_optimised_mode_still_writes_a_valid_summary(self):
        self.write_summary("Still fine.\n")
        done = self.run_script("-O")
        self.assertEqual(done.returncode, 0, done.stderr)
        with open(os.path.join(self.out, "entry.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "Still fine.\n")

    def test_an_empty_output_variable_falls_back_instead_of_crashing(self):
        self.write_summary("A fine summary.\n")
        done = self.run_script(env_extra={"MAKEFUN_OUTPUT_DIR": ""})
        # It may not be able to write /output as an unprivileged user, but it
        # must not die on makedirs("") with FileNotFoundError.
        self.assertNotIn("FileNotFoundError", done.stderr)
        self.assertNotIn("No such file or directory: ''", done.stderr)

    def test_importing_the_module_writes_nothing(self):
        # The asserts used to run at module scope, so an import executed the
        # program. Import it with an output directory pointed at a temp path and
        # prove the directory stays empty.
        env = dict(os.environ)
        env["MAKEFUN_OUTPUT_DIR"] = self.out
        env["PYTHONPATH"] = ROOT
        done = subprocess.run(
            [sys.executable, "-c", "import main; print('imported')"],
            capture_output=True, text=True, env=env, timeout=60,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("imported", done.stdout)
        self.assertEqual(os.listdir(self.out) if os.path.isdir(self.out) else [], [])


if __name__ == "__main__":
    unittest.main()
