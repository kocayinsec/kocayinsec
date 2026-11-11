#!/usr/bin/env python3
"""Build the profile banner (assets/hero*.svg) from this one file.

    python3 scripts/build_hero.py

Writes eight files: dark and light, wide and compact, moving and still,
plus the profile picture (assets/avatar.svg, drawn from the same owl).
README.md chooses among them with <picture>; it shows the light print in
both colour schemes, and the dark plate is kept as an option.

Standard library only. The copy, both palettes, the owl's strokes, the order
they are drawn in and how the owl behaves once awake all live here.

v2: the owl sits in front of a faint moon ring with a few stars around it,
the branch reaches out toward the name, the owl breathes, leans toward the
name when it looks at it, and the dot of the "i" warms to copper under its
gaze.

GitHub shows a README image through <img>. An SVG loaded that way runs CSS
animations, but no scripts, no web fonts and no pointer events. So the
wordmark and the line under it are stored as outlines, and all motion is
CSS that starts when the image loads. Every animation only describes how a stroke *arrives*: with
animations off, the file is the finished drawing.
"""
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Copy ─────────────────────────────────────────────────────────────────
EYEBROW = "WARSAW, POLAND"
SAY = ["Builds web & mobile products.", "Studies how they break."]
TITLE = "kocayinsec. Builds web and mobile products, studies how they break."
DESC = ("A line drawing of an owl on a branch, in ivory and copper, in front of a "
        "faint moon ring, beside the name kocayinsec. The owl is drawn stroke by "
        "stroke, opens its eyes, breathes, and now and then leans over to look "
        "at the name, whose i-dot warms to copper while it looks.")

# ── Palettes: the plate (dark), and the print pulled from it (light) ─────
# Each palette is its own file and README.md picks one with <picture>. A
# prefers-color-scheme query inside the SVG is not dependable: loaded through
# <img>, WebKit answered "light" under a dark page when this was tested.
DARK = dict(bg="#151A19", edge="#DED5BC", edge_o=".09", ink="#DED5BC",
            cu="#B89362", word="#EDE5D4", say="#C4CCC6", tag="#9EA89F", moon_o=".2")
LIGHT = dict(bg="#F1EBDD", edge="#2B2924", edge_o=".14", ink="#2B2924",
             cu="#A5633A", word="#1F1E1A", say="#4A4840", tag="#7C786B", moon_o=".22")

# ── Two sizes. GitHub scales the wide card to about 830 px, and the compact
#    one to about 290 px on a phone, so the compact card says less, larger. ─
LAYOUTS = {
    "": dict(w=1280, h=400, word=(66, 216, 112), tag=(70, 97, 17, 3.4),
             say=(70, (279, 315), 26), owl=(840, 3, 1.04), weight=1.0, reach=True,
             stars=[(742, 64, .9), (812, 116, .6), (706, 158, .5), (1152, 96, .45), (1218, 82, .7)]),
    "-compact": dict(w=720, h=340, word=(28, 158, 80), tag=None,
                     say=(31, (212, 250), 29), owl=(392, 0, .9), weight=1.25, reach=False,
                     stars=[(452, 58, .75), (690, 62, .6)]),
}

# ── Motion ───────────────────────────────────────────────────────────────
ARRIVE = "cubic-bezier(.25,1,.5,1)"   # easeOutQuart: words settle
BURIN = "cubic-bezier(.6,0,.3,1)"     # a cut speeds up, then slows
BURIN_SPEED = 430     # owl units per second: one hand, one speed
MIN_CUT = .2          # seconds; the shortest stroke still reads as a stroke
TRACK = -1.2          # wordmark tracking, in hundredths of an em
T_WAKE = 2.55         # the eyes open once the drawing is done

# ── YOUR CALL: the owl at rest ───────────────────────────────────────────
# One loop lasts REST_PERIOD seconds and starts just after the eyes open, so
# its first seconds are also the end of the entrance. Times are % of the loop.
# REST_LOOK moves the pupils: negative x looks left, across at the name; the
# eye is 42 units wide, so about ±9 is the most a pupil can travel.
REST_PERIOD = 16
REST_BLINKS = [4, 47, 49.2, 90]          # the pair at 47/49.2 is a double blink
REST_LOOK = [(9, 0), (11.2, -6), (24, -6), (27, 0),        # across at the name
             (66, 0), (68, 3.5), (76, 3.5), (78.5, 0)]     # a glance out, past the edge
# The body follows the eyes a beat later and leans about the feet (degrees).
REST_LEAN = [(10, 0), (13.5, -1.5), (24.5, -1.5), (28.5, 0),
             (67, 0), (70, .8), (76.5, .8), (80, 0)]
# While the gaze rests on the name, the dot of the i warms to copper.
REST_GLINT = (13.5, 15.5, 22.5, 25.5)    # start warming, warm, start cooling, cool
BREATH = (5.6, 1.005, 1.012)             # seconds per breath, then scale x, y
# ─────────────────────────────────────────────────────────────────────────

# Lora Regular (SIL OFL 1.1), shaped with HarfBuzz; em = 100, y down.
# (advance, outline) per glyph. Regenerate with: build_hero.py --outline Lora-Regular.ttf
WORDMARK = [
    (53.0, "M3.5 0V-3Q6.6 -3 7.8 -4.6Q8.9 -6.1 9.1 -8.9Q9.3 -11.6 9.3 -15.2L9.4 -62.5Q9.4 -64.1 9.4 -65.6Q9.5 -67 9.7 -69Q7.9 -68.9 6.2 -68.8Q4.4 -68.7 2.6 -68.6V-72.8Q7 -72.8 9.4 -73.2Q11.8 -73.6 13.1 -74.2Q14.3 -74.8 15 -75.5H17.9V-28.2H21.9L34.1 -41Q35.8 -42.7 37.2 -44.1Q38.6 -45.4 40 -46.3L33.2 -46V-50H51.4V-47Q48 -46.7 45 -44.9Q42.1 -43 39.7 -40.7Q37.2 -38.4 35.4 -36.5L27.6 -28.3Q29.6 -27.4 31 -26Q32.4 -24.6 33.8 -22.9L40.9 -13.8Q41.4 -13.2 42.7 -11.5Q43.9 -9.8 45.7 -7.8Q47.4 -5.8 49.4 -4.4Q51.3 -3 53 -3V0H43.9Q41.1 0 38.6 -2.9Q36.1 -5.8 33.3 -9.4Q30.7 -13 28.7 -16Q26.6 -18.9 25 -21.1Q23.3 -23.3 22 -24.5L17.9 -24.3V-10.6Q17.9 -8.6 17.9 -7Q17.8 -5.5 17.5 -3.8Q19.1 -3.9 20.7 -4Q22.3 -4 23.9 -4.1V0Z"),
    (58.5, "M29.2 1.6Q22.2 1.6 16.5 -1.7Q10.8 -4.9 7.5 -10.7Q4.1 -16.4 4.1 -23.8Q4.1 -31.7 7.4 -38Q10.7 -44.3 16.4 -48Q22.1 -51.6 29.2 -51.6Q36.2 -51.6 41.9 -48.2Q47.6 -44.9 51 -39.2Q54.4 -33.5 54.4 -26.2Q54.4 -18.5 51.1 -12.2Q47.7 -5.8 42 -2.1Q36.3 1.6 29.2 1.6ZM30 -2.4Q35.3 -2.4 38.4 -5.4Q41.5 -8.4 42.9 -13.2Q44.2 -18 44.2 -23.3Q44.2 -27.8 43.4 -32.1Q42.5 -36.5 40.7 -40Q38.9 -43.6 36.1 -45.7Q33.2 -47.8 29.2 -47.8Q24 -47.8 20.7 -44.8Q17.4 -41.8 15.9 -37Q14.3 -32.2 14.3 -26.7Q14.3 -20.5 16 -14.9Q17.7 -9.4 21.2 -5.9Q24.7 -2.4 30 -2.4Z"),
    (53.0, "M28.8 1.6Q22.1 1.6 16.5 -1.4Q10.8 -4.5 7.5 -10.2Q4.1 -16 4.1 -24.1Q4.1 -29.3 6 -34.2Q7.9 -39.1 11.4 -43Q14.8 -47 19.6 -49.3Q24.4 -51.6 30.2 -51.6Q35.8 -51.6 40 -49.9Q44.1 -48.2 46.4 -45.4Q48.7 -42.6 48.7 -39.3Q48.7 -37.1 47.5 -35.5Q46.3 -34 44 -34Q41.5 -33.9 40.5 -35.5Q39.4 -37.2 39.4 -38.5Q39.4 -39.5 39.7 -40.5Q40 -41.6 40.9 -42.5Q40.1 -44.9 38.1 -46.1Q36.1 -47.2 34 -47.6Q31.8 -47.9 30.4 -47.9Q23.6 -47.9 19 -42.5Q14.3 -37 14.3 -26.6Q14.3 -19.9 16.5 -14.7Q18.6 -9.5 22.5 -6.5Q26.4 -3.6 31.5 -3.6Q36.2 -3.6 40.5 -6.1Q44.8 -8.6 47.2 -12.2L49.8 -10.2Q47.2 -6 43.6 -3.4Q39.9 -0.8 36.1 0.4Q32.2 1.6 28.8 1.6Z"),
    (50.6, "M34.8 0Q34.5 -1.7 34.4 -3Q34.3 -4.3 34.1 -5.7Q30.7 -2.3 26.8 -0.4Q22.8 1.6 18.4 1.6Q10.8 1.6 7.1 -1.9Q3.4 -5.3 3.4 -10.3Q3.4 -14.9 6.2 -18.2Q9.1 -21.6 13.6 -23.8Q18.2 -25.9 23.6 -27Q28.9 -28 33.9 -27.9V-34.1Q33.9 -37.6 33.3 -40.7Q32.7 -43.8 30.7 -45.8Q28.7 -47.8 24.3 -47.9Q21.4 -48 18.4 -46.8Q15.3 -45.6 13.9 -42.7Q14.7 -41.9 15 -40.9Q15.2 -39.8 15.2 -38.9Q15.2 -37.7 14.2 -36.2Q13.2 -34.6 10.7 -34.7Q8.6 -34.7 7.5 -36.2Q6.4 -37.6 6.4 -39.6Q6.4 -43 8.9 -45.7Q11.5 -48.4 16 -50Q20.5 -51.6 26.2 -51.6Q34.6 -51.6 38.6 -47.2Q42.6 -42.7 42.5 -33.1Q42.5 -29.4 42.5 -25.7Q42.5 -21.9 42.5 -18.2Q42.4 -14.4 42.4 -10.6Q42.4 -9 42.3 -7.4Q42.2 -5.8 42 -3.8Q43.8 -3.9 45.6 -4Q47.3 -4.1 49.1 -4.2V0ZM33.9 -24.5Q30.5 -24.4 26.8 -23.7Q23 -22.9 19.9 -21.4Q16.7 -19.9 14.8 -17.5Q12.8 -15 12.9 -11.5Q13.1 -7.8 15.4 -6Q17.6 -4.1 20.7 -4.1Q24.8 -4.1 27.9 -5.7Q30.9 -7.2 33.9 -10Q33.8 -11.1 33.8 -12.4Q33.8 -13.7 33.8 -15.1Q33.8 -15.6 33.9 -18.3Q33.9 -21 33.9 -24.5Z"),
    (52.8, "M12.1 27.1Q9 27.1 6.8 25.6Q4.6 24.1 4.6 21Q4.6 19.2 5.8 17.7Q7 16.2 8.9 16.2Q11.3 16.1 12.2 17.7Q13 19.3 13 20.5Q13 20.8 13 21.1Q13 21.5 12.9 21.9Q13.2 22.1 14 22.1Q15.2 22.1 16.6 21.1Q18 20.1 19.1 18.2Q20.4 16 22.2 11.6Q23.9 7.2 26.1 1.1L10.5 -32.3Q7.9 -37.9 6.8 -41.2Q5.6 -44.5 5.2 -46.1L0.4 -45.9V-50H21.1V-47H20.7Q16.5 -46.7 16.1 -43.9Q15.7 -41 18.4 -35.2L30.1 -10.1Q32.4 -16.5 34.5 -22.8Q36.6 -29 38.7 -35.2Q39.5 -37.4 40.4 -39.8Q41.2 -42.1 42.1 -44Q42.9 -45.8 43.6 -46.3L36.7 -45.9V-50H52.4V-47Q48.7 -45.6 46.9 -42.4Q45 -39.1 43.1 -34L30.6 0.9Q27.6 9.3 25.1 15.2Q22.6 21 19.6 24.1Q16.6 27.1 12.1 27.1Z"),
    (28.1, "M4.4 -3Q7.5 -3 8.7 -4.6Q9.9 -6.1 10.1 -8.9Q10.3 -11.6 10.3 -15.2V-38Q10.3 -39.6 10.4 -41Q10.5 -42.5 10.7 -44.5Q8.9 -44.4 7.2 -44.3Q5.4 -44.2 3.6 -44.1V-48.3Q8 -48.3 10.4 -48.7Q12.8 -49.1 14.1 -49.7Q15.3 -50.3 16 -51H18.9V-10.6Q18.9 -8.6 18.9 -7Q18.8 -5.5 18.5 -3.8Q20.1 -3.9 21.7 -4Q23.2 -4 24.8 -4.1V0H4.4ZM14 -60.9Q11.9 -60.9 10.3 -62.6Q8.7 -64.3 8.7 -66.8Q8.7 -69.3 10.4 -71Q12 -72.8 14.1 -72.8Q16.4 -72.8 18 -71Q19.5 -69.3 19.5 -66.8Q19.5 -64.3 17.9 -62.6Q16.2 -60.9 14 -60.9Z"),
    (60.7, "M4.4 0V-3Q7.5 -3 8.7 -4.6Q9.9 -6.1 10.1 -8.9Q10.3 -11.6 10.3 -15.2L10.4 -38Q10.4 -39.6 10.4 -41.2Q10.5 -42.8 10.8 -44.5Q9 -44.4 7.2 -44.3Q5.5 -44.2 3.7 -44.1V-48.3Q8.1 -48.3 10.4 -48.7Q12.6 -49.1 13.7 -49.7Q14.8 -50.3 15.5 -51H18.4Q18.5 -50.3 18.6 -49.4Q18.6 -48.5 18.7 -47.4Q18.8 -46.3 18.8 -44.9Q21 -46.8 23.6 -48.3Q26.3 -49.8 29.2 -50.7Q32.2 -51.6 35.1 -51.6Q43.8 -51.6 47.8 -46.2Q51.8 -40.7 51.8 -29.2V-10.6Q51.8 -8.6 51.8 -7Q51.7 -5.5 51.4 -3.8Q53 -3.9 54.5 -4Q56.1 -4 57.7 -4.1V0H37.3V-3Q40.4 -3 41.6 -4.6Q42.8 -6.1 43 -8.9Q43.2 -11.6 43.2 -15.2V-29.2Q43.1 -37.8 40.4 -42.2Q37.6 -46.6 31.7 -46.5Q28.1 -46.4 24.7 -44.6Q21.2 -42.8 18.9 -40Q19 -39.2 19 -38.2Q19 -37.2 19 -36.1L18.9 -10.6Q18.9 -8.6 18.9 -7Q18.8 -5.5 18.5 -3.8Q20.1 -3.9 21.7 -4Q23.2 -4 24.8 -4.1V0Z"),
    (46.3, "M24.9 1.6Q19.9 1.6 16 0.2Q12.1 -1.1 9.6 -2.8L10 0.7H5.8L5.2 -16.5H8.3Q8.5 -12.4 10.6 -9.2Q12.7 -5.9 16 -4.1Q19.3 -2.3 23.1 -2.3Q25.7 -2.3 28.2 -3.2Q30.7 -4 32.4 -5.8Q34.1 -7.5 34.1 -10.2Q34.1 -13 32.5 -14.8Q30.8 -16.7 28.1 -18.1Q25.4 -19.5 22.3 -20.7Q19.3 -21.9 16.3 -23.2Q13.3 -24.5 10.8 -26.3Q8.2 -28.1 6.7 -30.7Q5.2 -33.3 5.2 -37.1Q5.2 -39.2 6 -41.7Q6.8 -44.2 8.7 -46.5Q10.6 -48.7 13.9 -50.2Q17.2 -51.6 22.3 -51.6Q25 -51.6 28.3 -50.7Q31.6 -49.8 34.7 -47.3L34.5 -51.1H38.7V-33.6H35.5Q35.3 -37.1 33.9 -40.4Q32.5 -43.6 29.8 -45.8Q27.1 -47.9 22.8 -47.9Q18.2 -47.9 15.6 -45.6Q13 -43.3 13 -40.3Q13 -37.2 15 -35.2Q16.9 -33.1 20 -31.6Q23.1 -30.1 26.6 -28.7Q30.4 -27.1 34 -25.2Q37.6 -23.3 39.9 -20.5Q42.2 -17.6 42.2 -13.1Q42.2 -8.1 39.7 -4.8Q37.1 -1.5 33.2 0.1Q29.2 1.6 24.9 1.6Z"),
    (53.7, "M28.6 1.6Q21.7 1.6 16.2 -1.7Q10.6 -4.9 7.4 -10.9Q4.2 -16.8 4.2 -24.9Q4.2 -31.9 7.3 -38Q10.5 -44.1 16.2 -47.9Q21.9 -51.6 29.4 -51.6Q33.6 -51.6 37.2 -50.2Q40.9 -48.9 43.7 -46.2Q46.5 -43.4 48.1 -39.2Q49.7 -35.1 49.7 -29.5L14.5 -28.9Q14.5 -21.3 16.1 -15.6Q17.8 -9.8 21.5 -6.7Q25.2 -3.5 31 -3.5Q34.1 -3.5 37.4 -4.6Q40.6 -5.7 43.4 -7.6Q46.2 -9.5 47.9 -11.8L50.3 -9.8Q47.6 -5.6 43.8 -3.1Q40 -0.6 36 0.5Q32 1.6 28.6 1.6ZM14.8 -33.1H40.3Q40.3 -36.7 39.2 -40.1Q38.2 -43.4 35.8 -45.6Q33.4 -47.7 29.5 -47.7Q23.7 -47.7 19.9 -44.2Q16 -40.8 14.8 -33.1Z"),
    (53.2, "M28.8 1.6Q22.1 1.6 16.5 -1.4Q10.8 -4.5 7.5 -10.2Q4.1 -16 4.1 -24.1Q4.1 -29.3 6 -34.2Q7.9 -39.1 11.4 -43Q14.8 -47 19.6 -49.3Q24.4 -51.6 30.2 -51.6Q35.8 -51.6 40 -49.9Q44.1 -48.2 46.4 -45.4Q48.7 -42.6 48.7 -39.3Q48.7 -37.1 47.5 -35.5Q46.3 -34 44 -34Q41.5 -33.9 40.5 -35.5Q39.4 -37.2 39.4 -38.5Q39.4 -39.5 39.7 -40.5Q40 -41.6 40.9 -42.5Q40.1 -44.9 38.1 -46.1Q36.1 -47.2 34 -47.6Q31.8 -47.9 30.4 -47.9Q23.6 -47.9 19 -42.5Q14.3 -37 14.3 -26.6Q14.3 -19.9 16.5 -14.7Q18.6 -9.5 22.5 -6.5Q26.4 -3.6 31.5 -3.6Q36.2 -3.6 40.5 -6.1Q44.8 -8.6 47.2 -12.2L49.8 -10.2Q47.2 -6 43.6 -3.4Q39.9 -0.8 36.1 0.4Q32.2 1.6 28.8 1.6Z"),
]

# The line under the name: Lora Italic (SIL OFL 1.1), shaped with HarfBuzz;
# em = 100, y down. Regenerate with: build_hero.py --outline-say Lora-Italic.ttf
SAY_GLYPHS = {
    "B": "M30 -70Q42 -70 48 -66Q54 -62 53 -53Q53 -50 51 -47Q49 -44 46 -41Q42 -39 36 -38V-37Q47 -37 52 -32Q58 -27 57 -20Q57 -14 54 -9Q50 -5 45 -2Q40 0 33 0H4L4 -3Q8 -3 10 -5Q11 -7 11 -10Q12 -12 12 -16L14 -58Q14 -61 14 -63Q14 -65 15 -66Q13 -66 11 -66Q9 -66 7 -66L8 -70Q13 -70 19 -70Q24 -70 30 -70ZM31 -35Q28 -35 26 -35Q24 -35 21 -34L20 -12Q20 -9 20 -7Q19 -5 19 -4Q21 -4 23 -4Q25 -4 27 -4Q29 -4 30 -4Q38 -4 42 -8Q47 -12 48 -19Q48 -25 46 -28Q44 -32 40 -33Q36 -35 31 -35ZM30 -67Q27 -67 25 -66Q24 -65 23 -63Q22 -61 22 -57L21 -38Q23 -38 25 -38Q27 -38 29 -38Q34 -39 38 -41Q41 -43 43 -47Q44 -50 44 -54Q45 -59 42 -62Q40 -65 37 -66Q34 -67 30 -67Z",
    "S": "M27 2Q23 2 18 1Q13 0 10 -3L10 1H5L5 -20H9Q9 -14 12 -10Q14 -6 18 -4Q22 -3 28 -3Q32 -3 35 -4Q38 -5 41 -8Q43 -11 43 -15Q43 -20 41 -23Q38 -26 34 -29Q30 -31 25 -33Q20 -36 16 -38Q12 -41 9 -44Q7 -48 7 -54Q7 -56 8 -60Q10 -62 12 -65Q14 -68 18 -70Q22 -72 28 -72Q32 -72 37 -71Q42 -70 46 -66L45 -71H50L49 -49H46Q46 -54 44 -58Q42 -62 38 -65Q35 -68 29 -68Q23 -68 19 -64Q15 -60 15 -56Q15 -52 17 -49Q19 -46 22 -44Q26 -42 29 -40Q33 -39 37 -37Q41 -35 45 -32Q48 -30 50 -26Q52 -22 52 -17Q51 -12 48 -8Q45 -3 40 -1Q35 2 27 2Z",
    "a": "M33 -51Q36 -51 40 -51Q43 -50 46 -49Q46 -43 45 -37Q44 -32 43 -26Q43 -21 42 -17Q42 -12 42 -10Q42 -8 42 -6Q42 -4 45 -4Q46 -4 48 -6Q50 -8 52 -14L55 -13Q54 -11 54 -9Q53 -6 51 -4Q49 -2 47 0Q45 1 42 1Q38 1 36 -1Q34 -4 34 -8Q34 -11 35 -14Q36 -18 36 -21H36Q34 -14 31 -9Q28 -5 26 -3Q23 0 21 0Q18 1 16 1Q11 1 7 -3Q4 -7 4 -16Q4 -23 6 -30Q7 -36 11 -41Q15 -46 20 -48Q26 -51 33 -51ZM30 -48Q25 -48 22 -45Q19 -42 16 -38Q14 -34 13 -29Q12 -24 12 -18Q12 -12 14 -7Q15 -3 19 -3Q21 -3 24 -6Q27 -9 29 -13Q32 -18 34 -23Q35 -29 36 -35Q38 -41 38 -46Q36 -47 34 -47Q32 -48 30 -48Z",
    "ampersand": "M29 2Q21 2 15 -1Q10 -3 6 -7Q3 -12 3 -18Q4 -23 6 -27Q8 -32 12 -35Q16 -38 22 -38Q14 -40 11 -44Q8 -48 9 -54Q9 -59 12 -63Q15 -67 20 -69Q25 -72 31 -72Q36 -72 40 -70Q44 -68 46 -66Q48 -63 48 -60Q48 -59 47 -57Q46 -56 44 -56Q42 -56 41 -57Q40 -58 40 -59Q40 -60 40 -61Q40 -62 40 -63Q40 -65 37 -66Q35 -68 31 -68Q27 -68 24 -66Q21 -64 19 -61Q18 -58 17 -54Q17 -53 18 -50Q18 -48 19 -46Q20 -43 23 -42Q26 -40 30 -40Q32 -40 32 -40Q33 -40 34 -40L34 -36L30 -36Q25 -36 22 -34Q19 -33 17 -30Q15 -28 14 -25Q13 -22 13 -20Q13 -14 15 -11Q18 -7 22 -5Q26 -3 30 -3Q38 -3 42 -6Q47 -9 50 -14Q52 -19 52 -24Q49 -24 47 -24Q45 -24 43 -24Q41 -23 38 -21L36 -23Q38 -26 41 -28Q43 -30 46 -30Q49 -31 53 -31Q57 -31 60 -31Q64 -32 67 -35L69 -33Q68 -31 66 -29Q64 -27 62 -26Q60 -25 56 -24Q56 -20 55 -16Q54 -11 50 -7Q47 -3 42 -1Q37 2 29 2Z",
    "b": "M20 -76Q19 -73 19 -70Q18 -67 18 -64Q18 -61 17 -59Q17 -54 16 -50Q16 -45 15 -40Q15 -35 14 -30H15Q17 -37 19 -41Q22 -46 24 -48Q27 -50 29 -50Q32 -51 34 -51Q39 -51 41 -48Q44 -46 45 -42Q46 -38 46 -33Q46 -26 45 -20Q43 -14 40 -9Q37 -4 32 -2Q26 1 19 1Q17 1 15 1Q13 1 10 0Q8 0 6 -1Q6 -11 7 -19Q7 -26 8 -34Q8 -41 9 -48Q9 -55 10 -64Q10 -66 10 -67Q10 -68 11 -69Q9 -69 7 -69Q5 -69 4 -69L4 -73Q8 -73 11 -73Q13 -74 15 -74Q16 -75 17 -76ZM31 -46Q28 -46 26 -44Q23 -41 21 -36Q19 -32 17 -26Q15 -21 14 -15Q13 -10 13 -5Q14 -4 16 -3Q19 -2 20 -2Q25 -2 28 -4Q31 -6 33 -9Q35 -12 36 -16Q37 -20 38 -24Q38 -28 38 -32Q38 -39 36 -43Q35 -47 31 -46Z",
    "c": "M28 -51Q32 -51 36 -50Q39 -48 41 -45Q43 -43 43 -39Q43 -37 42 -36Q41 -34 39 -34Q36 -34 35 -36Q34 -37 34 -38Q34 -39 35 -40Q35 -41 36 -42Q35 -45 33 -46Q31 -48 28 -48Q23 -48 20 -45Q18 -43 16 -39Q14 -36 13 -31Q13 -27 13 -23Q13 -16 14 -12Q16 -8 19 -6Q21 -4 25 -4Q28 -4 30 -5Q33 -6 36 -9Q38 -12 40 -16L44 -15Q41 -9 38 -5Q35 -2 31 0Q27 1 23 1Q14 1 9 -4Q4 -10 4 -21Q4 -26 5 -31Q7 -36 10 -41Q12 -45 17 -48Q22 -51 28 -51Z",
    "d": "M17 1Q13 1 10 -1Q7 -4 5 -8Q4 -13 4 -18Q4 -28 7 -35Q10 -43 17 -47Q23 -51 33 -51Q34 -51 36 -51Q37 -51 38 -51Q39 -54 39 -58Q40 -62 40 -65Q41 -68 41 -69Q39 -69 37 -69Q36 -69 34 -69L34 -73Q39 -73 41 -73Q44 -74 45 -74Q46 -75 47 -76H50Q49 -70 48 -62Q47 -55 46 -43Q45 -36 44 -30Q44 -24 43 -18Q43 -13 43 -9Q43 -7 43 -6Q44 -4 45 -4Q47 -4 49 -6Q51 -8 53 -14L56 -13Q55 -11 54 -9Q53 -6 52 -4Q50 -2 48 0Q46 1 42 1Q38 1 37 -1Q35 -4 35 -8Q35 -11 35 -14Q36 -17 36 -21H36Q33 -12 30 -7Q27 -2 24 -1Q20 1 17 1ZM19 -4Q23 -4 26 -7Q29 -11 32 -17Q34 -22 36 -29Q36 -32 37 -37Q37 -41 38 -46Q36 -47 35 -47Q33 -48 31 -48Q27 -48 24 -46Q21 -44 18 -41Q16 -38 15 -35Q14 -31 13 -27Q12 -23 12 -20Q12 -13 14 -8Q16 -4 19 -4Z",
    "e": "M28 -51Q32 -51 35 -50Q38 -49 40 -46Q42 -44 42 -40Q42 -36 39 -32Q37 -30 32 -28Q28 -26 22 -24Q17 -23 13 -23Q13 -16 14 -12Q15 -8 18 -6Q20 -4 24 -4Q27 -4 30 -5Q33 -6 36 -9Q38 -12 40 -16L44 -14Q41 -9 38 -6Q35 -2 31 0Q27 1 22 1Q13 1 8 -5Q4 -11 4 -20Q4 -26 5 -32Q7 -37 10 -42Q13 -46 18 -49Q22 -51 28 -51ZM27 -48Q22 -48 19 -45Q16 -42 15 -37Q13 -32 13 -26Q18 -27 23 -29Q28 -31 31 -33Q34 -36 34 -40Q34 -43 32 -46Q30 -48 27 -48Z",
    "h": "M43 1Q38 1 37 -1Q35 -4 35 -8Q35 -11 36 -15Q36 -19 37 -23Q37 -28 38 -32Q38 -36 38 -40Q38 -42 38 -43Q37 -44 36 -45Q35 -46 33 -46Q30 -46 28 -44Q25 -42 23 -37Q20 -33 18 -28Q16 -22 15 -17Q14 -11 14 -5Q14 -4 14 -3Q14 -1 14 0H6Q6 -1 6 -1Q6 -2 6 -3Q6 -5 6 -11Q7 -16 7 -24Q8 -31 8 -38Q9 -46 10 -53Q10 -59 11 -64Q11 -66 12 -67Q12 -68 12 -69L5 -69L5 -73Q10 -73 12 -73Q15 -74 16 -74Q17 -75 18 -76H21Q20 -73 20 -70Q20 -67 19 -64Q18 -61 18 -58Q18 -56 17 -52Q17 -48 17 -44Q16 -39 16 -35Q15 -31 15 -29H16Q19 -38 22 -43Q26 -48 29 -49Q32 -51 35 -51Q41 -51 44 -47Q46 -43 46 -38Q46 -33 46 -27Q45 -21 44 -16Q43 -11 43 -8Q43 -7 44 -5Q44 -4 46 -4Q48 -4 50 -6Q52 -8 53 -14L56 -13Q56 -11 55 -9Q54 -6 52 -4Q51 -2 48 0Q46 1 43 1Z",
    "i": "M13 -51Q18 -51 20 -48Q22 -45 22 -41Q22 -38 21 -34Q21 -30 20 -26Q19 -21 18 -17Q18 -12 18 -8Q18 -6 19 -5Q19 -4 21 -4Q23 -4 25 -6Q27 -8 28 -14L31 -13Q31 -11 30 -8Q29 -6 27 -4Q26 -2 24 0Q22 1 19 1Q14 1 12 -1Q10 -4 10 -8Q10 -13 10 -17Q11 -21 12 -25Q12 -29 13 -33Q14 -37 14 -42Q14 -43 13 -44Q12 -46 11 -46Q9 -46 7 -44Q5 -42 4 -36L1 -37Q1 -39 2 -41Q3 -44 4 -46Q6 -48 8 -50Q10 -51 13 -51ZM19 -73Q21 -73 23 -71Q24 -70 24 -67Q24 -64 23 -63Q21 -61 19 -61Q17 -61 15 -63Q14 -64 14 -67Q14 -70 15 -71Q17 -73 19 -73Z",
    "k": "M38 1Q35 1 32 -2Q30 -5 27 -12Q25 -17 24 -19Q22 -21 19 -22Q18 -22 18 -21Q17 -21 16 -21Q15 -17 15 -13Q14 -9 14 -5Q14 -4 14 -3Q14 -1 14 0H6Q6 -1 6 -1Q6 -2 6 -3Q6 -5 6 -11Q7 -16 7 -24Q8 -31 8 -38Q9 -46 10 -52Q10 -59 11 -64Q11 -66 12 -67Q12 -68 12 -69Q10 -69 8 -69Q7 -69 5 -69L5 -73Q10 -73 12 -73Q15 -74 16 -74Q17 -75 18 -76H21Q20 -73 20 -70Q19 -67 19 -64Q18 -61 18 -58Q17 -52 17 -44Q16 -36 15 -29H16Q19 -38 22 -42Q25 -47 28 -49Q32 -51 35 -51Q39 -51 41 -50Q43 -48 44 -46Q45 -43 45 -40Q45 -37 43 -33Q41 -29 36 -26Q32 -23 26 -22V-22Q29 -22 31 -20Q33 -19 34 -15Q36 -13 37 -10Q38 -8 39 -6Q40 -5 41 -4Q43 -4 44 -6Q46 -7 46 -11L49 -10Q49 -7 47 -5Q46 -2 44 -1Q42 1 38 1ZM17 -24Q27 -24 32 -28Q37 -32 37 -40Q37 -41 36 -43Q36 -44 35 -46Q34 -47 32 -46Q29 -46 27 -43Q24 -40 22 -35Q19 -30 17 -24Z",
    "l": "M21 -76Q21 -73 21 -70Q20 -67 20 -64Q19 -61 19 -58Q18 -54 18 -49Q17 -44 16 -38Q16 -32 15 -27Q15 -21 15 -17Q14 -12 14 -9Q14 -7 15 -6Q15 -4 17 -4Q19 -4 21 -6Q23 -8 24 -14L27 -13Q27 -11 26 -9Q25 -6 23 -4Q22 -2 19 0Q17 1 14 1Q10 1 8 -1Q6 -3 6 -7Q6 -10 6 -14Q7 -19 7 -26Q8 -32 9 -39Q9 -46 10 -52Q11 -58 12 -64Q12 -66 12 -67Q12 -68 12 -69Q11 -69 9 -69Q7 -69 5 -69L6 -73Q10 -73 13 -73Q15 -74 16 -74Q18 -75 19 -76Z",
    "m": "M73 1Q69 1 67 -1Q65 -4 65 -8Q65 -11 66 -15Q66 -19 67 -23Q68 -28 68 -32Q69 -36 69 -40Q69 -42 68 -43Q68 -44 67 -45Q66 -46 64 -46Q61 -46 59 -44Q56 -41 54 -37Q51 -32 50 -27Q48 -22 47 -16Q46 -10 46 -5Q46 -4 46 -3Q46 -1 46 0H38Q38 -1 38 -1Q38 -2 38 -3Q38 -6 38 -12Q39 -17 39 -22Q40 -28 41 -33Q41 -38 41 -41Q41 -42 40 -44Q39 -46 36 -46Q34 -46 31 -44Q28 -41 26 -37Q24 -32 22 -27Q20 -22 19 -16Q18 -10 18 -5Q18 -4 18 -3Q18 -1 18 0H10Q10 -1 10 -1Q10 -2 10 -3Q10 -4 10 -7Q10 -9 10 -13Q11 -16 12 -23Q12 -28 13 -32Q13 -35 13 -37Q14 -39 14 -40Q14 -40 14 -42Q14 -43 13 -45Q13 -46 11 -46Q9 -46 7 -44Q5 -42 4 -36L1 -37Q1 -39 2 -41Q3 -44 5 -46Q6 -48 8 -50Q11 -51 14 -51Q17 -51 19 -49Q20 -48 21 -45Q21 -42 21 -39Q21 -37 21 -34Q20 -31 20 -29H20Q23 -38 26 -43Q30 -48 33 -49Q36 -51 38 -51Q42 -51 45 -49Q47 -47 48 -45Q49 -42 49 -40Q49 -37 49 -35Q48 -33 47 -29H48Q51 -38 54 -43Q57 -48 60 -49Q64 -51 66 -51Q70 -51 73 -49Q75 -48 76 -45Q77 -42 77 -38Q77 -33 76 -27Q75 -21 74 -16Q74 -11 74 -8Q74 -7 74 -5Q74 -4 76 -4Q78 -4 80 -6Q82 -8 84 -14L86 -13Q86 -11 85 -9Q84 -6 82 -4Q81 -2 79 0Q76 1 73 1Z",
    "o": "M29 -51Q34 -51 38 -49Q43 -46 45 -41Q48 -36 48 -29Q48 -21 45 -14Q42 -7 36 -3Q31 1 23 1Q16 1 12 -2Q8 -5 6 -10Q4 -15 4 -21Q4 -29 7 -36Q10 -43 15 -47Q21 -51 29 -51ZM27 -47Q23 -48 20 -44Q16 -41 15 -36Q13 -31 13 -25Q13 -21 13 -17Q14 -14 15 -10Q16 -7 18 -5Q21 -3 24 -3Q28 -3 31 -5Q34 -7 35 -11Q37 -14 38 -18Q39 -22 39 -26Q39 -30 38 -33Q38 -37 37 -40Q35 -43 33 -45Q31 -47 27 -47Z",
    "p": "M4 26V22Q7 22 8 21Q9 19 10 16Q10 12 10 8Q11 0 12 -8Q12 -16 13 -23Q14 -30 14 -34Q15 -39 15 -41Q15 -43 14 -44Q14 -46 12 -46Q10 -46 8 -44Q6 -42 5 -36L2 -37Q2 -39 3 -41Q4 -44 6 -46Q7 -48 10 -50Q12 -51 15 -51Q19 -51 21 -48Q22 -45 22 -41Q22 -38 22 -35Q22 -32 21 -29H21Q24 -38 27 -43Q30 -48 33 -49Q36 -51 39 -51Q44 -51 47 -48Q50 -46 51 -41Q53 -37 53 -32Q53 -22 49 -15Q46 -7 39 -3Q33 1 23 1Q22 1 21 1Q20 1 18 1Q18 8 18 13Q17 17 17 19Q17 21 17 22Q18 22 20 22Q22 22 23 21V26ZM25 -2Q29 -2 32 -4Q35 -6 38 -9Q40 -11 41 -15Q43 -19 43 -22Q44 -26 44 -30Q44 -34 43 -38Q43 -42 41 -44Q40 -46 37 -46Q34 -46 32 -44Q29 -41 27 -36Q24 -31 22 -25Q21 -19 20 -13Q19 -11 19 -8Q19 -6 19 -4Q20 -3 22 -3Q23 -2 25 -2Z",
    "period": "M10 -11Q13 -11 14 -9Q16 -7 16 -5Q16 -2 14 0Q12 2 10 2Q7 2 6 0Q4 -2 4 -5Q4 -7 6 -9Q8 -11 10 -11Z",
    "r": "M10 0Q10 -1 10 -1Q10 -2 10 -3Q10 -4 10 -7Q10 -9 11 -13Q11 -17 12 -23Q12 -30 13 -33Q13 -36 13 -38Q14 -39 14 -40Q14 -42 13 -44Q13 -46 11 -46Q9 -46 7 -44Q5 -42 4 -36L1 -37Q1 -39 2 -41Q3 -44 4 -46Q6 -48 8 -50Q11 -51 14 -51Q18 -51 20 -48Q21 -45 21 -40Q21 -38 20 -35Q20 -32 20 -29H20Q23 -38 26 -43Q29 -47 32 -49Q36 -51 39 -51Q42 -51 44 -50Q46 -48 46 -45Q46 -44 44 -42Q43 -40 41 -40Q39 -40 38 -42Q37 -43 36 -45Q34 -45 31 -43Q28 -40 26 -36Q24 -32 22 -26Q20 -21 19 -15Q18 -9 18 -4Q18 -3 18 -2Q18 -1 18 0Z",
    "s": "M19 1Q15 1 11 0Q8 -1 5 -4Q3 -6 3 -10Q3 -12 4 -13Q6 -14 7 -14Q9 -14 10 -13Q11 -12 11 -10Q11 -10 11 -9Q11 -8 10 -7Q11 -5 14 -4Q16 -3 19 -3Q24 -3 27 -5Q30 -8 30 -12Q30 -15 28 -17Q26 -19 23 -21Q20 -23 17 -24Q14 -26 11 -28Q9 -30 7 -32Q5 -35 5 -38Q5 -41 8 -44Q10 -47 14 -49Q18 -51 23 -51Q26 -51 30 -50Q33 -49 35 -46Q38 -44 38 -41Q38 -39 36 -38Q35 -37 33 -37Q32 -37 30 -38Q29 -39 29 -41Q29 -42 30 -42Q30 -43 30 -44Q30 -46 28 -47Q26 -48 22 -48Q20 -48 18 -47Q16 -46 15 -44Q13 -42 13 -40Q13 -38 14 -36Q16 -35 17 -33Q19 -32 22 -31Q25 -28 29 -26Q33 -24 35 -21Q38 -18 38 -14Q38 -9 35 -6Q33 -3 29 -1Q25 1 19 1Z",
    "t": "M22 -64 20 -50H36L36 -46L20 -46Q19 -42 19 -37Q18 -33 18 -28Q17 -24 17 -20Q17 -16 17 -13Q17 -11 17 -9Q17 -7 18 -5Q19 -4 21 -4Q22 -4 24 -4Q25 -5 27 -6Q29 -8 31 -11L33 -9Q30 -4 27 -2Q24 1 19 1Q15 1 13 -1Q10 -2 10 -5Q8 -8 8 -11Q8 -14 9 -20Q9 -25 10 -32Q10 -39 11 -46L2 -46L2 -50Q9 -50 13 -54Q16 -57 18 -64Z",
    "u": "M21 1Q17 1 14 -1Q12 -2 11 -6Q10 -8 10 -12Q10 -18 11 -23Q12 -29 12 -34Q13 -39 13 -41Q13 -43 13 -45Q12 -46 10 -46Q9 -46 7 -44Q5 -42 3 -36L1 -37Q1 -39 2 -41Q3 -44 4 -46Q6 -48 8 -50Q10 -51 13 -51Q17 -51 19 -49Q21 -46 21 -41Q21 -39 21 -34Q20 -30 20 -26Q19 -22 19 -17Q18 -13 18 -10Q18 -9 18 -7Q19 -6 20 -5Q21 -4 23 -4Q26 -4 28 -6Q31 -9 33 -13Q36 -18 38 -23Q40 -28 41 -34Q42 -40 42 -45Q42 -46 42 -47Q42 -49 42 -50H50Q50 -49 50 -49Q50 -48 50 -47Q50 -46 50 -43Q50 -41 49 -37Q49 -33 48 -27Q47 -21 47 -18Q47 -15 46 -13Q46 -11 46 -10Q46 -10 46 -8Q46 -7 47 -5Q47 -4 49 -4Q50 -4 53 -6Q55 -8 56 -14L59 -13Q59 -11 58 -9Q57 -6 55 -4Q54 -2 51 0Q49 1 46 1Q42 1 40 -1Q38 -4 38 -8Q38 -11 39 -14Q39 -18 40 -21H40Q36 -12 33 -7Q30 -2 27 -1Q24 1 21 1Z",
    "w": "M64 -51Q68 -51 71 -48Q74 -45 75 -41Q76 -36 76 -31Q75 -25 74 -20Q72 -16 69 -12Q67 -8 64 -5Q60 -2 56 0Q52 1 48 1Q46 1 43 0Q41 -1 39 -5Q38 -8 38 -14Q37 -10 34 -6Q31 -3 28 -1Q24 1 21 1Q15 1 13 -3Q10 -7 10 -12Q10 -16 11 -20Q11 -24 12 -28Q12 -32 13 -36Q13 -39 13 -41Q13 -43 13 -45Q12 -46 10 -46Q9 -46 7 -44Q5 -42 3 -36L0 -37Q1 -39 2 -41Q3 -44 4 -46Q6 -48 8 -50Q10 -51 13 -51Q16 -51 18 -50Q20 -49 20 -47Q21 -44 21 -41Q21 -38 21 -34Q20 -29 20 -25Q19 -20 19 -16Q19 -12 19 -10Q19 -9 19 -7Q19 -6 20 -5Q21 -4 23 -4Q25 -4 28 -6Q30 -7 33 -10Q35 -13 37 -17Q38 -21 39 -27Q40 -32 40 -39Q40 -41 40 -44Q40 -47 40 -50H48Q48 -49 48 -48Q49 -46 49 -46Q49 -40 48 -36Q48 -31 47 -27Q46 -23 46 -19Q45 -15 45 -12Q45 -9 46 -7Q47 -4 51 -4Q54 -4 56 -5Q59 -7 62 -9Q64 -12 66 -15Q68 -18 70 -22Q70 -24 71 -28Q71 -31 71 -34Q71 -38 70 -41Q69 -43 66 -44Q66 -43 65 -42Q64 -42 62 -42Q61 -42 59 -43Q58 -44 58 -46Q58 -47 59 -48Q59 -50 60 -50Q62 -51 64 -51Z",
    "y": "M6 27Q3 27 1 25Q-1 23 -1 21Q-1 18 0 17Q2 16 3 16Q7 16 7 21Q8 22 8 22Q9 22 9 22Q12 22 14 20Q16 19 18 16Q21 14 22 11Q24 9 25 8Q24 2 23 -4Q21 -11 20 -17Q18 -23 16 -29Q15 -34 12 -40Q12 -41 11 -43Q10 -45 8 -45Q6 -44 5 -42Q4 -39 4 -34L1 -34Q1 -36 1 -40Q1 -42 2 -45Q3 -48 5 -49Q7 -51 10 -51Q14 -51 16 -49Q18 -48 19 -45Q20 -42 21 -40Q23 -35 25 -28Q27 -22 28 -15Q30 -8 30 -2H30Q33 -7 36 -13Q38 -19 40 -25Q42 -31 42 -36Q42 -39 41 -41Q41 -43 40 -43Q40 -43 39 -43Q39 -43 38 -43Q36 -43 35 -44Q34 -45 34 -47Q34 -49 35 -50Q37 -51 39 -51Q42 -51 43 -49Q45 -47 46 -44Q47 -42 47 -38Q47 -32 45 -25Q43 -18 40 -11Q37 -4 33 2Q28 11 24 16Q19 22 15 25Q11 27 6 27Z",
}
SAY_RUNS = [
    [('B', 0.0), ('u', 61.9), ('i', 121.2), ('l', 153.6), ('d', 181.9), ('s', 237.4), ('w', 306.5), ('e', 386.6), ('b', 434.3), ('ampersand', 511.7), ('m', 606.3), ('o', 693.9), ('b', 746.0), ('i', 797.1), ('l', 829.5), ('e', 857.8), ('p', 931.8), ('r', 988.9), ('o', 1033.4), ('d', 1085.5), ('u', 1141.0), ('c', 1200.3), ('t', 1247.6), ('s', 1284.0), ('period', 1326.8)],
    [('S', 0.0), ('t', 56.6), ('u', 93.0), ('d', 152.3), ('i', 207.8), ('e', 240.2), ('s', 287.9), ('h', 357.0), ('o', 414.2), ('w', 466.3), ('t', 572.7), ('h', 609.1), ('e', 666.3), ('y', 714.0), ('b', 791.7), ('r', 842.8), ('e', 887.3), ('a', 935.0), ('k', 989.8), ('period', 1041.8)],
]

# ── The owl, in the order a hand would cut it ────────────────────────────
# (kind, start, path[, step])   kind: ink | cu are drawn, soft fades up.
# A path with several sub-paths is split; `step` staggers them (seconds), and
# without it each one starts as the one before is nearly done.
OWL = [
    # Outline: crown and ears, then both sides down to the branch.
    ("ink", .45, "M111 112c-3-22 5-47 10-65 9 14 21 21 35 23 23-9 50-10 72-2 13-4 23-13 31-24 4 16 12 34 10 53"),
    ("ink", .74, "M108 122c-7 29-2 49 9 64-9 21-13 46-9 69 4 28 16 47 39 56"),
    ("ink", .80, "M275 111c10 26 7 51-5 71 10 29 11 59 3 83-5 17-14 30-26 40"),
    ("soft", 1.15, "M128 74c8 8 16 12 27 12m78-3c8-5 16-10 20-17", .1),
    # Facial discs: the only warm metal on the face.
    ("cu", 1.02, "M192 111c-16-27-48-33-66-15-21 20-16 57 7 77 14 13 35 19 56 21"),
    ("cu", 1.12, "M198 110c16-27 46-31 63-14 21 21 16 55-6 76-14 13-32 19-51 22"),
    ("soft", 1.45, "M180 106c-15-16-36-19-48-6-15 15-13 43 2 59m77-54c13-16 33-17 44-5 13 14 11 36-2 52", .08),
    ("soft", 1.3, "M148 90l8 6m73-8-8 7m-28-17 1 13m-13-10 3 8m22-10-3 9", .2),
    ("soft", 1.7, "m147 171 9 7m8-4 8 6m54-8-8 7m23-10-8 7m-53 11 10 3m17-1 9-3", .22),
    # Wings and body.
    ("ink", 1.5, "M127 195c-6 29-1 62 17 89 6 9 13 14 18 15-13-29-16-54-12-78"),
    ("ink", 1.58, "M257 195c9 29 4 62-12 88-5 8-11 14-17 17 12-29 15-52 11-78"),
    ("soft", 1.8, "M126 225c3 20 10 38 20 52m-17-67 8 5m-7 11 8 5m-4 12 8 6m112-24c-3 20-10 38-20 52m18-68-8 6m5 10-8 6m4 11-8 7", .3),
    ("soft", 1.85, "m171 212 5 9 7-8m21-3 5 10 6-7m-32 18 6 10 6-9m-27 18 6 9 7-8m23-3 6 10 6-9m-33 17 6 10 7-9m-24 19 6 8m22-8-5 8", .36),
    ("ink", 1.95, "M166 299c6 6 13 9 20 9m18 0c7 0 14-3 20-8", .06),
    ("soft", 2.15, "m180 313 8 18 9-3 9 1 7-18m-16 6v11", .08),
]
# The branch, then the feet that hold it. Drawn over the body, and never
# leans: the owl moves, the branch stays.
PERCH = [
    ("cu", 1.8, "M79 319c43-8 73-9 103-8 47 2 91-3 136-19m-32 10 16-15m-193 28-16-9"),
    ("soft", 2.25, "M88 324c35-7 54-8 72-8m59 2c31-1 63-8 89-17", .1),
    ("ink", 2.05, "M164 306c-5 1-7 6-6 12m12-10c-4 2-5 6-4 11m11-11c-3 2-4 5-3 9m43-11c-4 1-6 5-5 11m12-10c-4 2-5 5-4 10m11-13c-3 1-5 5-4 10", .035),
]
# On the wide card the branch reaches back toward the name and fades out,
# cut left to right so it runs straight on into the branch.
REACH = [("reach", 1.4, "M-150 336C-70 335 10 328 79 319")]
# The face turns with the eyes, so it is kept apart from the rest.
FACE = [
    ("ink", 1.27, "M125 119c18-11 36-10 54 2m33-1c16-12 33-13 49-4", .06),
    ("ink", 1.52, "M190 135c0 11-1 23 7 35 6-11 8-24 7-35"),
    ("cu", 1.74, "m194 151 3 12 4-13"),
]
# (id, almond, closed lid = the almond's lower edge, pupil centre, lid start)
EYES = [
    ("L", "M132 131c12-12 30-12 42 1-11 14-29 14-42-1Z", "M132 131C145 146 163 146 174 132", (153, 132), 1.40),
    ("R", "M217 131c11-13 29-15 42-3-10 15-29 16-42 3Z", "M217 131C230 144 249 143 259 128", (238, 130), 1.46),
]
TURN = .35            # how far the face follows the pupils
TURN_LAG = .6         # % of the loop the face trails the pupils by
LEAN_PIVOT = (194, 312)   # the feet, in owl units

# Behind the owl: a moon ring (owl units: centre x, y, radius, start angle),
# and a closed outline of the owl in the background colour that hides the
# ring where the owl stands in front of it.
MOON = (198, 152, 126, 160)
SILHOUETTE = ("M111 112C108 90 116 65 121 47C130 61 142 68 156 70C179 61 206 60 228 68"
              "C241 64 251 55 259 44C263 60 271 78 269 97L275 111C285 137 282 162 270 182"
              "C280 211 281 241 273 265C268 282 259 295 247 305L214 316L180 316L147 311"
              "C124 302 112 283 108 255C104 232 108 207 117 186C106 171 101 151 108 122Z")
STAR = ("M0 -6C.5 -1.4 1.4 -.5 6 0C1.4 .5 .5 1.4 0 6C-.5 1.4 -1.4 .5 -6 0"
        "C-1.4 -.5 -.5 -1.4 0 -6Z")
IDOT = 5              # the i in kocayinsec


def n(v, places=2):
    s = f"{v:.{places}f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        return "0"
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


def subpaths(d):
    """Split a path into sub-paths with absolute coordinates.

    Returns [(d, length, start_y)]. Handles M m L l V v C c Z, which is all
    the owl uses.
    """
    toks = re.findall(r"[MmLlVvCcZz]|-?(?:\d+\.?\d*|\.\d+)", d)
    out, segs, cur, start, cmd, i = [], None, (0.0, 0.0), (0.0, 0.0), None, 0

    def flush():
        if not segs:
            return
        length, parts = 0.0, [f"M{n(segs[0][1][0], 1)} {n(segs[0][1][1], 1)}"]
        for kind, *pts in segs:
            if kind == "Z":
                parts.append("Z")
                length += math.dist(pts[0], pts[1])
            elif kind == "L":
                parts.append(f"L{n(pts[1][0], 1)} {n(pts[1][1], 1)}")
                length += math.dist(pts[0], pts[1])
            else:
                p0, c1, c2, p1 = pts
                parts.append("C" + " ".join(n(v, 1) for p in (c1, c2, p1) for v in p))
                prev = p0
                for k in range(1, 25):
                    t = k / 24
                    u = 1 - t
                    q = tuple(u**3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t**3 * e
                              for a, b, c, e in zip(p0, c1, c2, p1))
                    length += math.dist(prev, q)
                    prev = q
        out.append(("".join(parts), length, segs[0][1][1]))

    def num():
        nonlocal i
        i += 1
        return float(toks[i - 1])

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                segs.append(("Z", cur, start))
                cur = start
            continue
        rel = cmd.islower()
        ox, oy = cur if rel else (0.0, 0.0)
        if cmd in "Mm":
            flush()
            cur = start = (ox + num(), oy + num())
            segs = []
            cmd = "l" if rel else "L"
            continue
        if cmd in "Ll":
            p = (ox + num(), oy + num())
            segs.append(("L", cur, p))
        elif cmd in "Vv":
            p = (cur[0], oy + num())
            segs.append(("L", cur, p))
        else:
            c1, c2, p = ((ox + num(), oy + num()) for _ in range(3))
            segs.append(("C", cur, c1, c2, p))
        cur = p
    flush()
    return out


def blink_css(name, period, at):
    """Eye and lid keyframes for blinks at `at` (% of `period` seconds)."""
    pct = lambda ms: ms / (period * 10)
    shut, hold, back = pct(80), pct(70), pct(130)
    eye_open, eye_shut, lid_off, lid_on = ["0%", "100%"], [], ["0%", "100%"], []
    for b in at:
        eye_open += [n(b - shut) + "%", n(b + hold + back) + "%"]
        eye_shut += [n(b) + "%", n(b + hold) + "%"]
        lid_off += [n(b - shut / 2) + "%", n(b + hold + back / 3) + "%"]
        lid_on += [n(b) + "%", n(b + hold) + "%"]
    return (f"@keyframes {name}{{{','.join(eye_open)}{{transform:scaleY(1);opacity:1}}"
            f"{','.join(eye_shut)}{{transform:scaleY(.06);opacity:0}}}}"
            f"@keyframes {name}-lid{{{','.join(lid_off)}{{opacity:0}}{','.join(lid_on)}{{opacity:1}}}}")


def look_css(name, scale, lag=0.0):
    stops = [(0, 0)] + [(min(99.9, p + lag), x) for p, x in REST_LOOK] + [(100, 0)]
    return (f"@keyframes {name}{{" +
            "".join(f"{n(p)}%{{transform:translateX({n(x * scale)}px)}}" for p, x in stops) + "}")


def lean_css(name):
    """Rotate about the feet. Every stop has the same function list, so the
    browser interpolates the angle alone and the pivot never drifts."""
    px, py = LEAN_PIVOT
    stops = [(0, 0)] + REST_LEAN + [(100, 0)]
    return (f"@keyframes {name}{{" + "".join(
        f"{n(p)}%{{transform:translate({px}px,{py}px) rotate({n(a)}deg) translate({-px}px,{-py}px)}}"
        for p, a in stops) + "}")


def glint_css(name, D):
    a, b, c, e = REST_GLINT
    return (f"@keyframes {name}{{0%,{n(a)}%,{n(e)}%,100%{{fill:{D['word']}}}"
            f"{n(b)}%,{n(c)}%{{fill:{D['cu']}}}}}")


def style(L, D, animated):
    k = L["weight"]
    css = [
        f".bg{{fill:{D['bg']};stroke:{D['edge']};stroke-opacity:{D['edge_o']}}}",
        f".ink,.soft,.cu{{fill:none;stroke:{D['ink']};stroke-linecap:round;stroke-linejoin:round}}",
        f".ink{{stroke-width:{n(2.15 * k)}}}.soft{{stroke-width:{n(1.55 * k)};opacity:.49}}",
        f".cu{{stroke:{D['cu']};stroke-width:{n(1.85 * k)}}}",
        f".reach{{fill:none;stroke:url(#reach);stroke-width:{n(1.85 * k)};stroke-linecap:round}}",
        f".moon{{fill:none;stroke:{D['ink']};stroke-width:{n(1.3 * k)};stroke-opacity:{D['moon_o']}}}",
        f".knock{{fill:{D['bg']}}}.star{{fill:{D['ink']};opacity:.55}}",
        f".word,.pupil{{fill:{D['word']}}}.glint{{fill:{D['bg']}}}",
        f".say{{fill:{D['say']}}}",
    ]
    if L["tag"]:
        css.append(f".tag{{fill:{D['tag']};font:{L['tag'][2]}px ui-monospace,SFMono-Regular,Menlo,Consolas,"
                   f"'Liberation Mono',monospace;letter-spacing:{L['tag'][3]}px}}")
    if animated:
        rest = f"{REST_PERIOD}s {n(T_WAKE + .45)}s infinite"
        css += [
            f".d{{animation:draw 1s {BURIN} backwards}}.f{{animation:fade .5s ease-out backwards}}",
            f".r{{animation:rise .7s {ARRIVE} backwards}}",
            ".eye{transform-box:fill-box;transform-origin:50% 100%;"
            f"animation:wake .36s {ARRIVE} {n(T_WAKE)}s backwards,rest-blink {rest}}}",
            f".look{{animation:rest-look cubic-bezier(.5,0,.2,1) {rest}}}",
            f".turn{{animation:rest-turn cubic-bezier(.5,0,.2,1) {rest}}}",
            f".lean{{animation:rest-lean cubic-bezier(.45,0,.25,1) {rest}}}",
            ".breathe{transform-box:fill-box;transform-origin:50% 100%;"
            f"animation:breathe {n(BREATH[0])}s ease-in-out {n(T_WAKE)}s infinite alternate}}",
            ".star{transform-box:fill-box;transform-origin:50% 50%}",
            ".lid{opacity:0}",
            f"@keyframes breathe{{to{{transform:scale({n(BREATH[1], 3)},{n(BREATH[2], 3)})}}}}",
            "@keyframes twinkle{from{opacity:.18;transform:scale(.62)}to{opacity:.8;transform:scale(1)}}",
            lean_css("rest-lean"), glint_css("glint", D),
            "@keyframes draw{from{stroke-dasharray:1 1;stroke-dashoffset:1;opacity:0}8%{opacity:1}"
            "to{stroke-dasharray:1 1;stroke-dashoffset:0}}",
            "@keyframes fade{from{opacity:0}}",
            "@keyframes rise{from{opacity:0;transform:translateY(12px)}}",
            "@keyframes wake{from{transform:scaleY(.06);opacity:0}30%{opacity:1}}",
            "@keyframes lid{0%{opacity:1;stroke-dasharray:1 1;stroke-dashoffset:1}"
            "22%{stroke-dasharray:1 1;stroke-dashoffset:0}94%{opacity:1}to{opacity:0}}",
            blink_css("rest-blink", REST_PERIOD, REST_BLINKS),
            look_css("rest-look", 1), look_css("rest-turn", TURN, TURN_LAG),
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}",
        ]
    return "".join(css)


def strokes(entries, animated):
    out = []
    for kind, at, d, *rest in entries:
        subs = subpaths(d)
        step = rest[0] if rest else None
        if kind == "soft":
            order = sorted(range(len(subs)), key=lambda j: subs[j][2])
            for rank, j in enumerate(order):
                t = at + (step or 0) * rank / max(1, len(subs) - 1)
                a = f' class="soft f" style="animation-delay:{n(t)}s"' if animated else ' class="soft"'
                out.append(f"<path{a} d=\"{subs[j][0]}\"/>")
            continue
        t = at
        for j, (sd, length, _) in enumerate(subs):
            dur = max(MIN_CUT, length / BURIN_SPEED)
            if j:
                t = at + step * j if step else t
            a = (f' class="{kind} d" pathLength="1" style="animation-delay:{n(t)}s;animation-duration:{n(dur)}s"'
                 if animated else f' class="{kind}"')
            out.append(f"<path{a} d=\"{sd if len(subs) > 1 else d}\"/>")
            if not step:
                t += dur * .85
    return out


def render(L, P, animated):
    w, h = L["w"], L["h"]
    A = lambda cls, t: f' class="{cls} r" style="animation-delay:{n(t)}s"' if animated else f' class="{cls}"'
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
         'role="img" aria-labelledby="t d">',
         f'<title id="t">{TITLE}</title>', f'<desc id="d">{DESC}</desc>',
         f"<style>{style(L, P, animated)}</style>",
         "<defs>" + "".join(f'<clipPath id="e{i}"><path d="{almond}"/></clipPath>' for i, almond, *_ in EYES)
         + f'<linearGradient id="reach" gradientUnits="userSpaceOnUse" x1="-150" y1="0" x2="79" y2="0">'
           f'<stop offset="0" stop-color="{P["cu"]}" stop-opacity="0"/>'
           f'<stop offset=".75" stop-color="{P["cu"]}"/></linearGradient>'
         + "".join(f'<path id="s-{g}" d="{d}"/>' for g, d in SAY_GLYPHS.items()) + "</defs>",
         f'<rect class="bg" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"/>']
    # Stars: placed by an outer <g>, so the twinkle's CSS transform on the
    # inner path does not replace their position.
    for j, (sx, sy, k) in enumerate(L["stars"]):
        a = (f' class="star" style="animation:fade .8s ease-out {n(T_WAKE + .2 + j * .18)}s backwards,'
             f'twinkle {n(4.6 + j * 1.3)}s ease-in-out {n(T_WAKE + 1.1 + j * .9)}s infinite alternate"'
             if animated else ' class="star"')
        o.append(f'<g transform="translate({sx} {sy}) scale({n(k)})"><path{a} d="{STAR}"/></g>')
    if L["tag"]:
        x, y, *_ = L["tag"]
        o.append(f'<text{A("tag", .05)} x="{x}" y="{y}">{EYEBROW}</text>')
    x, y, size = L["word"]
    o.append(f'<g transform="translate({x} {y}) scale({n(size / 100)})">')
    dx = 0.0
    for i, (adv, d) in enumerate(WORDMARK):
        t = .12 + i * .045
        if i == IDOT:
            # The i's dot is its own path, so it can warm up on its own.
            stem, dot = d.split("ZM", 1)
            dot_a = (f' class="word" style="animation:rise .7s {ARRIVE} {n(t)}s backwards,'
                     f'glint {REST_PERIOD}s linear {n(T_WAKE + .45)}s infinite"' if animated else ' class="word"')
            o.append(f'<g transform="translate({n(dx, 1)})"><path{A("word", t)} d="{stem}Z"/>'
                     f'<path{dot_a} d="M{dot}"/></g>')
        else:
            o.append(f'<g transform="translate({n(dx, 1)})"><path{A("word", t)} d="{d}"/></g>')
        dx += adv + TRACK
    o.append("</g>")
    x, ys, size = L["say"]
    for i, (y, run) in enumerate(zip(ys, SAY_RUNS)):
        # The rise is on the outer group, so it moves in card pixels.
        uses = "".join(f'<use href="#s-{g}" x="{n(gx, 1)}"/>' for g, gx in run)
        o.append(f'<g{A("say", .55 + i * .1)}><g transform="translate({x} {y}) scale({n(size / 100, 3)})">'
                 f'{uses}</g></g>')
    ox, oy, s = L["owl"]
    o.append(f'<g transform="translate({ox} {oy}) scale({n(s)})">')
    mx, my, mr, ma = MOON
    moon_a = (' class="moon d" style="animation-delay:.3s;animation-duration:2.6s"' if animated
              else ' class="moon"')
    o.append(f'<circle{moon_a} pathLength="1" cx="{mx}" cy="{my}" r="{mr}" transform="rotate({ma} {mx} {my})"/>')
    # lean > breathe > (knockout, body, face). The knockout moves with the
    # body, so the moon never shows through the owl while it leans.
    o.append('<g class="lean"><g class="breathe">' if animated else "<g><g>")
    o.append(f'<path class="knock" d="{SILHOUETTE}"/>')
    o += strokes(OWL, animated)
    o.append('<g class="turn">' if animated else "<g>")
    o += strokes(FACE, animated)
    for i, almond, lid, (cx, cy), t in EYES:
        if animated:
            o.append(f'<path class="ink lid" pathLength="1" style="animation:lid {n(T_WAKE - t + .08)}s linear {n(t)}s,'
                     f'rest-blink-lid {REST_PERIOD}s linear {n(T_WAKE + .45)}s infinite" d="{lid}"/>')
        o.append(f'<g class="eye"><path class="ink" d="{almond}"/><g clip-path="url(#e{i})"><g class="look">'
                 f'<ellipse class="pupil" cx="{cx}" cy="{cy}" rx="6.6" ry="10.2"/>'
                 f'<circle class="glint" cx="{cx + 2.2}" cy="{cy - 3}" r="1.7"/></g></g></g>')
    o.append("</g></g></g>")          # turn, breathe, lean
    if L["reach"]:
        o += strokes(REACH, animated)
    o += strokes(PERCH, animated)
    o.append("</g></svg>")
    return "\n".join(o) + "\n"


# ── The profile picture: the same owl, head and chest, heavier lines so it
#    still reads at 40 px. GitHub crops it to a circle. ─────────────────
AVATAR = dict(size=460, owl=(-77, -4, 1.6), weight=1.9, ring=212)


def render_avatar(P):
    S, (ox, oy, s), k = AVATAR["size"], AVATAR["owl"], AVATAR["weight"]
    css = (f".ink,.soft,.cu{{fill:none;stroke:{P['ink']};stroke-linecap:round;stroke-linejoin:round}}"
           f".ink{{stroke-width:{n(2.15 * k)}}}.soft{{stroke-width:{n(1.55 * k)};opacity:.49}}"
           f".cu{{stroke:{P['cu']};stroke-width:{n(1.85 * k)}}}"
           f".moon{{fill:none;stroke:{P['ink']};stroke-width:{n(1.6 / s * k * 1.4)};stroke-opacity:{P['moon_o']}}}"
           f".knock{{fill:{P['bg']}}}.pupil{{fill:{P['word']}}}.glint{{fill:{P['bg']}}}")
    c, r = S / 2, AVATAR["ring"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}" '
         'role="img" aria-labelledby="t"><title id="t">kocayinsec: a line drawing of an owl</title>',
         f"<style>{css}</style>",
         "<defs>" + "".join(f'<clipPath id="e{i}"><path d="{almond}"/></clipPath>' for i, almond, *_ in EYES) + "</defs>",
         f'<rect width="{S}" height="{S}" fill="{P["bg"]}"/>',
         f'<g transform="translate({ox} {oy}) scale({n(s)})">',
         f'<circle class="moon" cx="{n((c - ox) / s, 1)}" cy="{n((c - oy) / s, 1)}" r="{n(r / s, 1)}"/>',
         f'<path class="knock" d="{SILHOUETTE}"/>']
    o += strokes(OWL, False) + strokes(FACE, False)
    for i, almond, lid, (cx, cy), t in EYES:
        o.append(f'<path class="ink" d="{almond}"/><g clip-path="url(#e{i})">'
                 f'<ellipse class="pupil" cx="{cx}" cy="{cy}" rx="6.6" ry="10.2"/>'
                 f'<circle class="glint" cx="{cx + 2.2}" cy="{cy - 3}" r="1.7"/></g>')
    o.append("</g></svg>")
    return "\n".join(o) + "\n"


def outline_say(font_path, lines=SAY):
    """Print SAY_GLYPHS and SAY_RUNS for a font file (em = 100). Coordinates
    are whole units: at 26 px one unit is a quarter of a pixel."""
    import uharfbuzz as hb
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont

    font = TTFont(font_path)
    glyphs, names, k = font.getGlyphSet(), font.getGlyphOrder(), 100 / font["head"].unitsPerEm
    hb_font = hb.Font(hb.Face(hb.Blob.from_file_path(font_path)))
    shapes, runs = {}, []
    for line in lines:
        buf = hb.Buffer()
        buf.add_str(line)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf, {"kern": True, "liga": False})
        x, run = 0.0, []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = names[info.codepoint]
            pen = SVGPathPen(glyphs, ntos=lambda v: str(round(v)))
            glyphs[name].draw(TransformPen(pen, (k, 0, 0, -k, 0, 0)))
            if pen.getCommands():
                shapes[name] = pen.getCommands()
                run.append((name, round(x + pos.x_offset * k, 1)))
            x += pos.x_advance * k
        runs.append(run)
    print("SAY_GLYPHS = {")
    for name, d in sorted(shapes.items()):
        print(f'    "{name}": "{d}",')
    print("}")
    print("SAY_RUNS = [")
    for run in runs:
        print(f"    {run!r},")
    print("]")


def outline(font_path, text="kocayinsec"):
    """Print WORDMARK for a font file. Needs: pip install fonttools uharfbuzz"""
    import uharfbuzz as hb
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont

    font = TTFont(font_path)
    glyphs, names, k = font.getGlyphSet(), font.getGlyphOrder(), 100 / font["head"].unitsPerEm
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb.Font(hb.Face(hb.Blob.from_file_path(font_path))), buf, {"kern": True, "liga": False})
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip(".") or "0")
        glyphs[names[info.codepoint]].draw(TransformPen(pen, (k, 0, 0, -k, pos.x_offset * k, 0)))
        print(f'    ({round(pos.x_advance * k, 1)}, "{pen.getCommands()}"),')


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--outline":
        return outline(sys.argv[2])
    if len(sys.argv) == 3 and sys.argv[1] == "--outline-say":
        return outline_say(sys.argv[2])
    for theme, P in (("", DARK), ("-light", LIGHT)):
        for size, L in LAYOUTS.items():
            for still, animated in (("", True), ("-static", False)):
                path = ROOT / "assets" / f"hero{theme}{size}{still}.svg"
                path.write_text(render(L, P, animated), encoding="utf-8")
                print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f} KB")
    path = ROOT / "assets" / "avatar.svg"
    path.write_text(render_avatar(LIGHT), encoding="utf-8")
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
