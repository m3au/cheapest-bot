import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import cheapest  # noqa: E402


class SelectionTest(unittest.TestCase):
    def test_short_small_is_haiku(self):
        r = cheapest.cheapest("short", 20)
        self.assertEqual(r["model"], "Claude Haiku 5.5")
        self.assertEqual(r["billing"], "credit")

    def test_haiku_boundary_100k(self):
        self.assertEqual(cheapest.cheapest("short", 100)["model"], "Claude Haiku 5.5")
        self.assertEqual(cheapest.cheapest("short", 101)["model"], "GLM 5.3 Flash")

    def test_long_defaults_to_glm_flash(self):
        self.assertEqual(cheapest.cheapest("long")["model"], "GLM 5.3 Flash")

    def test_long_with_small_input_uses_haiku(self):
        self.assertEqual(cheapest.cheapest("long", 50)["model"], "Claude Haiku 5.5")

    def test_code_small_and_big(self):
        self.assertEqual(cheapest.cheapest("code", 50)["model"], "Claude Haiku 5.5")
        self.assertEqual(cheapest.cheapest("code", 300)["model"], "DeepSeek V4.1 Flash 1017")

    def test_allowance_is_composer_with_fast_false(self):
        for task in cheapest.TASKS:
            r = cheapest.cheapest(task, 500, billing="allowance")
            self.assertEqual(r["launch"], {"model": "composer-2.5", "model_params": {"fast": False}})
            self.assertEqual(r["launch_sdk"]["params"], [{"id": "fast", "value": "false"}])

    def test_never_recommends_fast_variant(self):
        for task in cheapest.TASKS:
            for k in (0, 50, 100, 101, 1000):
                for b in ("any", "allowance"):
                    r = cheapest.cheapest(task, k, b)
                    self.assertNotIn("fast", r["launch"]["model"].lower().replace("flash", ""))
                    self.assertNotEqual(r["launch"]["model_params"].get("fast"), True)

    def test_bad_input(self):
        for args in (("huge", 1), ("short", -1), ("short", 10001), ("short", "5"), ("short", True)):
            with self.assertRaises(ValueError):
                cheapest.cheapest(*args)
        with self.assertRaises(ValueError):
            cheapest.cheapest("short", 1, "credit-card")

    def test_data_shape(self):
        d = cheapest.load_models()
        allowed = {"name", "id", "provider", "input_per_m", "cached_input_per_m", "output_per_m",
                   "billing", "fast_variant_note", "notes", "source", "checked"}
        self.assertGreaterEqual(len(d["models"]), 30)
        for m in d["models"]:
            self.assertEqual(set(m), allowed, m["name"])
            self.assertIn(m["billing"], ("allowance", "credit"))
            self.assertTrue(m["source"].startswith("https://"))
            self.assertRegex(m["checked"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
