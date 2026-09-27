"""Checks the text layouts in patches.py against glyph positions measured on the reel.

Run: python3 -m unittest -v test_patches.py   (needs numpy, pillow, opencv-python-headless)
"""
import importlib.util
import unittest

DEPS = all(importlib.util.find_spec(m) for m in ("numpy", "PIL", "cv2"))

if DEPS:
    import numpy as np

    import patches as P

# Ink column runs (x0, x1) measured at 1080x1920 on the original frames.
LOWER_THIRD_RUNS = [(131, 143), (151, 164), (174, 187), (196, 215), (225, 238), (247, 259), (267, 282),
                    (302, 315), (323, 338), (346, 360), (369, 384), (392, 411), (421, 425), (434, 447),
                    (455, 469), (489, 492), (512, 526), (534, 556), (564, 577), (586, 594), (603, 617),
                    (625, 639), (647, 660), (668, 682), (701, 713), (721, 725), (735, 746), (754, 768),
                    (775, 788)]  # "FORMULA DYNAMICS · TWO-POST LIFTS", frame at 1:50.0
CAPTION_RUNS = [(75, 101), (128, 135), (145, 171), (180, 206), (215, 242), (268, 297), (304, 312),
                (322, 345), (352, 378), (387, 413), (422, 449), (455, 485), (493, 530), (538, 564),
                (573, 580)]  # "3 ,500 KILOGRAMS.", frame at 2:12.3


def ink_runs(alpha, x0):
    cols = np.where((alpha > 0.5).any(axis=0))[0]
    runs, start, prev = [], cols[0], cols[0]
    for c in cols[1:]:
        if c != prev + 1:
            runs.append((start + x0, prev + x0))
            start = c
        prev = c
    runs.append((start + x0, prev + x0))
    return runs


@unittest.skipUnless(DEPS, "needs numpy, pillow and opencv-python-headless")
class LayoutTest(unittest.TestCase):
    def assertRunsClose(self, got, want, tol=2):
        self.assertEqual(len(got), len(want), got)
        for g, w in zip(got, want):
            self.assertLessEqual(abs(g[0] - w[0]), tol, (got, want))
            self.assertLessEqual(abs(g[1] - w[1]), tol, (got, want))

    def test_lower_third_layout_matches_the_original(self):
        lt = P.LowerThird()
        y0, y1, x0, x1 = P.A_BOX
        alpha = P.render_alpha(lt.chars, P.A_SIZE, lt.y, (y1 - y0, x1 - x0))
        self.assertRunsClose(ink_runs(alpha, x0), LOWER_THIRD_RUNS)

    def test_scissor_lifts_starts_where_two_post_did_and_stays_on_the_panel(self):
        lt = P.LowerThird()
        y0, y1, x0, x1 = P.A_BOX
        runs = ink_runs(P.render_alpha(lt.new_chars, P.A_SIZE, lt.y, (y1 - y0, x1 - x0)), x0)
        self.assertLessEqual(abs(runs[0][0] - 512), 2)
        self.assertLess(runs[-1][1], 795)
        self.assertEqual(lt.n_new, len("SCISSORLIFTS"))

    def test_caption_layout_matches_the_original(self):
        _, chars, y = P.layout(P.C_TEXT, P.C_SIZE, P.C_TRACK, P.C_X0, P.C_TOP)
        y0, y1, x0, x1 = P.C_BOX
        alpha = P.render_alpha([(c, x - x0) for c, x in chars], P.C_SIZE, y - y0, (y1 - y0, x1 - x0))
        self.assertRunsClose(ink_runs(alpha, x0), CAPTION_RUNS)

    def test_caption_shift_closes_the_gap_to_normal_spacing(self):
        y0, y1, x0, x1 = P.C_BOX

        def comma_start(text):
            _, chars, y = P.layout(text, P.C_SIZE, P.C_TRACK, P.C_X0, P.C_TOP)
            alpha = P.render_alpha([(c, x - x0) for c, x in chars], P.C_SIZE, y - y0, (y1 - y0, x1 - x0))
            return ink_runs(alpha, x0)[1][0]
        self.assertLessEqual(abs(comma_start("3 ,500") - P.C_SHIFT - comma_start("3,500")), 1)

    def test_pound_line_sits_under_the_number_inside_the_frame(self):
        co = P.Callout()
        self.assertGreater(P.B_TOP, 810)  # "3500" ink ends at y=810
        self.assertLess(co.unit[0][1] + 60, 1080)
        self.assertEqual(round(3500 * 2.2046226), 7716)


if __name__ == "__main__":
    unittest.main()
