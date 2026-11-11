#!/usr/bin/env python3
"""Build the profile banner (assets/hero*.svg) from this one file.

    python3 scripts/build_hero.py

Writes eight files: dark and light, wide and compact, moving and still.
README.md chooses among them with <picture>.

Standard library only. The copy, both palettes, the owl's strokes, the order
they are drawn in and how the owl behaves once awake all live here.

GitHub shows a README image through <img>. An SVG loaded that way runs CSS
animations, but no scripts, no web fonts and no pointer events. So the
wordmark is stored as outlines, and all motion is CSS that starts when the
image loads. Every animation only describes how a stroke *arrives*: with
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
DESC = ("A line drawing of an owl on a branch, in ivory and copper, beside the "
        "name kocayinsec. The owl is drawn stroke by stroke, opens its eyes "
        "and now and then looks across at the name.")

# ── Palettes: the plate (dark), and the print pulled from it (light) ─────
# Each palette is its own file and README.md picks one with <picture>. A
# prefers-color-scheme query inside the SVG is not dependable: loaded through
# <img>, WebKit answered "light" under a dark page when this was tested.
DARK = dict(bg="#151A19", edge="#DED5BC", edge_o=".09", ink="#DED5BC",
            cu="#B89362", word="#EDE5D4", say="#C4CCC6", tag="#9EA89F")
LIGHT = dict(bg="#F1EBDD", edge="#2B2924", edge_o=".14", ink="#2B2924",
             cu="#A5633A", word="#1F1E1A", say="#4A4840", tag="#7C786B")

# ── Two sizes. GitHub scales the wide card to about 830 px, and the compact
#    one to about 290 px on a phone, so the compact card says less, larger. ─
LAYOUTS = {
    "": dict(w=1280, h=400, word=(66, 216, 112), tag=(70, 97, 17, 3.4),
             say=(70, (279, 315), 26), owl=(823, -14, 1.16), weight=1.0),
    "-compact": dict(w=720, h=340, word=(28, 158, 80), tag=None,
                     say=(31, (212, 250), 29), owl=(388, -8, .95), weight=1.25),
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
REST_BLINKS = [4, 62]
REST_LOOK = [(9, 0), (11.2, -6), (24, -6), (27, 0)]
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
    # The branch, then the feet that hold it.
    ("cu", 1.8, "M79 319c43-8 73-9 103-8 47 2 91-3 136-19m-32 10 16-15m-193 28-16-9"),
    ("soft", 2.25, "M88 324c35-7 54-8 72-8m59 2c31-1 63-8 89-17", .1),
    ("ink", 2.05, "M164 306c-5 1-7 6-6 12m12-10c-4 2-5 6-4 11m11-11c-3 2-4 5-3 9m43-11c-4 1-6 5-5 11m12-10c-4 2-5 5-4 10m11-13c-3 1-5 5-4 10", .035),
]
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


def look_css(name, scale):
    stops = [(0, 0)] + REST_LOOK + [(100, 0)]
    return (f"@keyframes {name}{{" +
            "".join(f"{n(p)}%{{transform:translateX({n(x * scale)}px)}}" for p, x in stops) + "}")


def style(L, D, animated):
    k = L["weight"]
    css = [
        f".bg{{fill:{D['bg']};stroke:{D['edge']};stroke-opacity:{D['edge_o']}}}",
        f".ink,.soft,.cu{{fill:none;stroke:{D['ink']};stroke-linecap:round;stroke-linejoin:round}}",
        f".ink{{stroke-width:{n(2.15 * k)}}}.soft{{stroke-width:{n(1.55 * k)};opacity:.49}}",
        f".cu{{stroke:{D['cu']};stroke-width:{n(1.85 * k)}}}",
        f".word,.pupil{{fill:{D['word']}}}.glint{{fill:{D['bg']}}}",
        f".say{{fill:{D['say']};font:italic {L['say'][2]}px Georgia,'Iowan Old Style','Times New Roman',serif}}",
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
            ".lid{opacity:0}",
            "@keyframes draw{from{stroke-dasharray:1 1;stroke-dashoffset:1;opacity:0}8%{opacity:1}"
            "to{stroke-dasharray:1 1;stroke-dashoffset:0}}",
            "@keyframes fade{from{opacity:0}}",
            "@keyframes rise{from{opacity:0;transform:translateY(12px)}}",
            "@keyframes wake{from{transform:scaleY(.06);opacity:0}30%{opacity:1}}",
            "@keyframes lid{0%{opacity:1;stroke-dasharray:1 1;stroke-dashoffset:1}"
            "22%{stroke-dasharray:1 1;stroke-dashoffset:0}94%{opacity:1}to{opacity:0}}",
            blink_css("rest-blink", REST_PERIOD, REST_BLINKS),
            look_css("rest-look", 1), look_css("rest-turn", TURN),
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
         "<defs>" + "".join(f'<clipPath id="e{i}"><path d="{almond}"/></clipPath>' for i, almond, *_ in EYES) + "</defs>",
         f'<rect class="bg" x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12"/>']
    if L["tag"]:
        x, y, *_ = L["tag"]
        o.append(f'<text{A("tag", .05)} x="{x}" y="{y}">{EYEBROW}</text>')
    x, y, size = L["word"]
    o.append(f'<g transform="translate({x} {y}) scale({n(size / 100)})">')
    dx = 0.0
    for i, (adv, d) in enumerate(WORDMARK):
        o.append(f'<g transform="translate({n(dx, 1)})"><path{A("word", .12 + i * .045)} d="{d}"/></g>')
        dx += adv + TRACK
    o.append("</g>")
    x, ys, _ = L["say"]
    for i, (y, line) in enumerate(zip(ys, SAY)):
        o.append(f'<text{A("say", .55 + i * .1)} x="{x}" y="{y}">{line.replace("&", "&amp;")}</text>')
    ox, oy, s = L["owl"]
    o.append(f'<g transform="translate({ox} {oy}) scale({n(s)})">')
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
    o.append("</g></g></svg>")
    return "\n".join(o) + "\n"


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
    for theme, P in (("", DARK), ("-light", LIGHT)):
        for size, L in LAYOUTS.items():
            for still, animated in (("", True), ("-static", False)):
                path = ROOT / "assets" / f"hero{theme}{size}{still}.svg"
                path.write_text(render(L, P, animated), encoding="utf-8")
                print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
