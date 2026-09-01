import re
import streamlit as st
from datetime import date

st.set_page_config(page_title="KDPEasy Storybook Prompt Kit", page_icon="📖", layout="centered")

# ----------------------------------------------------------------------------
# Access. One password per product - it unlocks ONLY that product's mode.
# The cart delivers each product's password automatically. A buyer logs in
# with one password per session; the green banner shows what it unlocked.
#   FE ....................... KDPSTORY2026   (access, no extra modes)
#   OTO1 (Coloring book) ..... KDPSTORYPAGES2026   -> "pages"
#   OTO2 (Full color) ........ KDPSTORYPRO2026     -> "pro"
# Flags: "pages" = coloring-book mode + 3 extra B&W styles;
#        "pro"   = full-color storybook mode + 6 color styles.
# Book size (real KDP trims) is available to everyone.
# "expires": None = permanent, or a datetime.date (trial).
# ----------------------------------------------------------------------------
PASSWORDS = {
    "KDPSTORY2026":       {"pages": False, "pro": False, "expires": None},
    "KDPSTORYPAGES2026":  {"pages": True,  "pro": False, "expires": None},
    "KDPSTORYPRO2026":    {"pages": False, "pro": True,  "expires": None},

    # 3-day trial. Works UP TO AND INCLUDING the date below, then stops.
    # For a new trial: change the password string AND the date.
    "KDPSTORYTRIAL2026": {"pages": False, "pro": False, "expires": date(2026, 9, 1)},
}

CUSTOM_CSS = """
<style>
:root { color-scheme: light; }
.stApp { background: linear-gradient(135deg, #eef2ff 0%, #ffffff 60%); }
.kdp-card {
    background: white; border-radius: 16px; padding: 2rem 2rem 1.5rem;
    box-shadow: 0 4px 24px rgba(79, 70, 229, 0.08); margin-bottom: 1.5rem;
}
h1, h2, h3 { color: #4f46e5; }
.stButton>button, .stDownloadButton>button {
    background-color: #10b981; color: white; border-radius: 10px; border: none;
    padding: 0.6rem 1.4rem; font-weight: 600;
}
.stButton>button:hover, .stDownloadButton>button:hover { background-color: #059669; color: white; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def check_password() -> bool:
    if st.session_state.get("authed"):
        return True
    st.markdown('<div class="kdp-card">', unsafe_allow_html=True)
    st.title("📖 KDPEasy Storybook Prompt Kit")
    pw = st.text_input("Enter access password", type="password")
    if st.button("Unlock"):
        tier = PASSWORDS.get(pw)
        if tier is None:
            st.error("Incorrect password.")
        elif tier["expires"] is not None and date.today() > tier["expires"]:
            st.error("This trial password has expired. Please reach out to get full access.")
        else:
            st.session_state["authed"] = True
            st.session_state["tier"] = {"pages": tier["pages"], "pro": tier["pro"]}
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    return False


def has(feature: str) -> bool:
    """feature is 'pages' (OTO1) or 'pro' (OTO2)."""
    return bool(st.session_state.get("tier", {}).get(feature))


# Streamlit reruns the whole script on every click (including the download
# buttons), which wipes anything rendered inside an `if st.button(...)` block -
# trial users kept losing their built prompts. These stash the result keyed by
# the inputs that produced it, so it keeps showing until an input actually
# changes, and disappears cleanly when it does.
def _stash(key, sig, value):
    st.session_state[key] = (sig, value)


def _recall(key, sig):
    got = st.session_state.get(key)
    return got[1] if got and got[0] == sig else None


# ----------------------------------------------------------------------------
# Shared building blocks. All text that ends up in a customer prompt is plain
# ASCII on purpose - it gets pasted into ChatGPT, so no smart quotes / dashes.
# ----------------------------------------------------------------------------

# INTERIOR line-art styles. The kit targets ages 4-8 - clean, simple, thick-line.
# FE = 2 presets. OTO1 adds 3 more.
STYLE_BW_FE = {
    "Bold & simple": ("thick, smooth, even black outlines; large chunky shapes; almost no small "
                      "interior detail; wide open areas to color; the cleanest, simplest look"),
    "Bold & rounded": ("thick, smooth, even black outlines with every shape gently rounded and "
                       "cuddly; large chunky shapes; almost no small interior detail; wide open "
                       "areas to color"),
}
STYLE_BW_PRO = {
    "A little more detail": ("clean, even, medium-weight outlines; a little more detail and a few "
                             "more elements per scene, still simple and fully closed"),
    "Chunky marker": ("very thick, rounded marker-style outlines; huge simple shapes; almost no "
                      "small detail; for the youngest hands"),
    "Storybook classic": ("even, calm pen linework with a traditional storybook feel and gently "
                          "balanced detail; still clean and fully closed"),
}
# INTERIOR full-color styles - only in the full-color mode (OTO2).
STYLE_COLOR = {
    "Bold & simple": "bright, bold, cheerful color: thick clean outlines, simple punchy shapes, flat lively color",
    "Soft watercolor": "gentle watercolor with soft edges and a warm, light palette",
    "Colored pencil": "colored-pencil look with visible strokes, cozy and handmade",
    "Flat vector": "clean flat vector shapes in a bright, limited palette",
    "Papercut collage": "layered papercut and collage shapes with a soft paper texture",
    "Kawaii chibi": "cute kawaii chibi style: rounded shapes, big friendly eyes, soft pastel color",
}

# Book size. One list for everyone - real KDP trims. First tuple item goes into
# the prompts and leads with the trim in inches (ChatGPT can't hit an arbitrary
# ratio - only 1:1, 2:3, 3:2 - so ratio numbers appear only where a trim IS one
# of those). Second tuple item is a UI caption: layout doc size + any crop note.
SAFE_AREA = ("Keep faces, the main character, and every key object inside a centered safe area with "
             "open, even margin on all four sides - nothing important near an edge - so nothing is "
             "cropped when the image is placed on the printed page.")
BOOK_SHAPE = {
    "KDP 8.5 x 8.5 in - square (most popular)": (
        "Printed at 8.5 x 8.5 inches - a square page. Make it a 1:1 square image. " + SAFE_AREA,
        "Layout / Canva document: 8.75 x 8.75 in (with bleed). The easiest size to lay out - a good default if you are new.",
    ),
    "KDP 8 x 8 in - square": (
        "Printed at 8 x 8 inches - a square page. Make it a 1:1 square image. " + SAFE_AREA,
        "Layout / Canva document: 8.25 x 8.25 in (with bleed).",
    ),
    "KDP 6 x 9 in - portrait": (
        "Printed at 6 x 9 inches - a tall portrait page, exactly a 2:3 shape. Make it a 2:3 portrait image. " + SAFE_AREA,
        "Layout / Canva document: 6.25 x 9.25 in (with bleed). This trim matches ChatGPT's 2:3 image exactly - no trimming needed.",
    ),
    "KDP 8 x 10 in - portrait": (
        "Printed at 8 x 10 inches - a tall portrait page. Make it a tall portrait image. " + SAFE_AREA +
        " Keep the top and bottom especially open - background only - so it can be trimmed to the 8 x 10 page with nothing important lost.",
        "Layout / Canva document: 8.25 x 10.25 in (with bleed). ChatGPT's portrait image comes out a little taller than this page - crop the top and bottom to fit; do not stretch it.",
    ),
    "KDP 8.5 x 11 in - portrait (US Letter)": (
        "Printed at 8.5 x 11 inches - a tall portrait page. Make it a tall portrait image. " + SAFE_AREA +
        " Keep the top and bottom especially open - background only - so it can be trimmed to the 8.5 x 11 page with nothing important lost.",
        "Layout / Canva document: 8.75 x 11.25 in (with bleed). ChatGPT's portrait image comes out a little taller than this page - crop the top and bottom to fit; do not stretch it.",
    ),
    "Landscape 11 x 8.5 in - wide": (
        "Printed at 11 x 8.5 inches - a wide landscape page. Make it a wide landscape image. " + SAFE_AREA,
        "Layout / Canva document: 11.25 x 8.75 in (with bleed).",
    ),
}

# Story text placement: an edge margin (fixes text creeping into the edge) without shrinking
# the type (a tester said the earlier "make it smaller" wording went too far).
TEXT_SAFE = ("Keep a clear empty margin around the story text - at least 10 percent of the page in "
             "from every edge - and never let it touch or run off an edge. Center the text block in "
             "its area with a little breathing room above and below.")

# One clean line-art spec, used in the Step 1 ART STYLE block and every Step 2 page prompt.
# Bans the detail creep (fur / wood-grain / fabric texture, hatching, scribbled ground lines,
# sparkle marks, busy backgrounds) alongside the older grey / shading problem.
LINE_ART_LOCK = (
    "Clean black-and-white coloring-book line art. Bold, smooth black outlines of one even weight "
    "on a pure white background. Big, simple shapes with generous open white space inside every "
    "one. Keep it uncluttered: no color, no gray, no shading or shadows, no hatching or "
    "crosshatching, no stippling or dot texture, no solid black fills, no fur, hair, wood-grain, "
    "or fabric texture, no scribbled ground lines, no sparkle or motion marks, no busy background. "
    "Every shape fully closed. No frame, border, or panel around the drawing."
)

COLOR_INTERIOR_LOCK = (
    "Clean full-color children's storybook illustration. Bright, warm, and friendly, with flat or "
    "lightly shaded color and clear, simple shapes. Keep it uncluttered - a few large elements, "
    "not a busy scene. No frame, border, or panel around the drawing."
)

COLOR_COVER_LOCK = (
    "Full-color, professionally finished children's book cover art - bright, warm, and appealing, "
    "with good contrast and a clean, uncluttered composition. Not black and white, not a coloring "
    "page. Keep important elements clear of the edges. No frame or border."
)

COMPOSITION = {
    "AUTO (text top, illustration bottom)": ("top third of the page", "lower two thirds of the page"),
    "TOP (text top, illustration bottom)": ("top third of the page", "lower two thirds of the page"),
    "BOTTOM (text bottom, illustration top)": ("bottom third of the page", "upper two thirds of the page"),
    "LEFT (text left, illustration right)": ("left third of the page", "right two thirds of the page"),
    "RIGHT (text right, illustration left)": ("right third of the page", "left two thirds of the page"),
}

FIELD_LABELS = ["STORY TEXT", "STORY SCENE", "ILLUSTRATION TYPE", "ILLUSTRATION DIRECTION"]

COVER_TYPES = {
    "AUTO": "Choose the cover composition that best fits this story.",
    "FULL SCENE": "Show the hero character inside a newly arranged story setting, not a copy of any interior page.",
    "CHARACTER FOCUS": "Make the main character the single dominant element on a simple, open background.",
    "GROUP SCENE": "Feature the main characters together in a fresh arrangement, resized and repositioned as needed.",
    "MINIMAL": "A very simple composition: one hero element and lots of open space.",
}

TITLE_POS = {
    "AUTO": "wherever it leaves the cleanest, most readable layout",
    "TOP": "across the top of the cover",
    "BOTTOM": "across the bottom of the cover",
}

# Book type modes: (label, required_flag, color_mode, no_text, upgrade_name)
MODES = [
    ("Storybook - black & white, with text", None, False, False, ""),
    ("Coloring book - has a story, NO text on the pages", "pages", False, True, "OTO 1"),
    ("Storybook - full color, with text", "pro", True, False, "OTO 2"),
]


# ----------------------------------------------------------------------------
# Step 1 - Story Engine prompt
# ----------------------------------------------------------------------------

def build_story_prompt(idea, page_count_raw, style_desc, shape_label, color_mode=False,
                       no_text=False, extra_art=""):
    pc = page_count_raw.strip()
    if pc.isdigit():
        n = max(20, min(40, int(pc)))
        pc_line = "Aim for exactly %d story pages (the book must have between 20 and 40)." % n
    else:
        pc_line = "Choose a length between 24 and 32 story pages (never fewer than 20, never more than 40)."

    medium = ("Each page will become a full-color storybook illustration." if color_mode
              else "Each page will become a black-and-white line-art coloring page.")
    dir_note = ("a plain description of what happens in the scene - the character's pose and action, "
                "the setting, and a few key objects")

    lines = [
        "You are a children's storybook author and illustration director. Turn the idea below into "
        "a complete, ready-to-illustrate picture book for children ages 4-8. " + medium,
        "",
        "IDEA: " + idea.strip(),
        "",
        "STORY",
        "Write warm, simple English in short sentences. Tell one clear story with a beginning, a "
        "middle turn, and a satisfying ending. Stay close to the idea above - keep its characters, "
        "setting, events, and ending; if the idea is only a line, invent the rest in the same "
        "spirit. Every page belongs to this one story.",
        pc_line + " Reach the length with real beats - one action, discovery, or feeling per page - "
        "not by repeating scenes or padding. If the idea is too small for the target, get as close "
        "as you can and say so in one line.",
        "If the reply would be cut off before the last page, stop at a clean page boundary and write "
        "exactly: (continue)",
    ]
    if no_text:
        lines += [
            "",
            "The story text will not be printed on the pages (the pictures carry the story), but "
            "still write a STORY TEXT line for every page.",
        ]
    lines += [
        "",
        "CHARACTER",
        "Give the main character one fixed identity and keep it identical on every page: species or "
        "type, body shape and proportions, face, hair or fur, colors, and the complete outfit and "
        "accessories - nothing added, dropped, or restyled between pages. Only the pose, gesture, "
        "expression, camera angle, action, and background change from page to page. If the idea "
        "names a character, use it and fill in the rest; otherwise create one that fits.",
        "",
        "ART & SCENES",
        ("Planned look: " + style_desc.strip().rstrip(".") + "."
         + (" Also apply on every page: " + extra_art.strip().rstrip(".") + "." if extra_art.strip() else "")
         + " The full style spec goes in the ART STYLE block below."),
        "Keep every scene simple - one main action and a few large elements over an open, "
        "uncluttered background. The finished art is " + shape_label + "; compose each scene for "
        "that shape with room to spare on every side.",
        "",
        "OUTPUT - exactly this, in this order, with nothing else added:",
        "1) STORY CONCEPT - 2 to 3 sentences.",
        "2) The character sheet, wrapped exactly:",
        "=== CHARACTER BIBLE START ===",
        "<every fixed character detail, spelled out in full>",
        "=== CHARACTER BIBLE END ===",
        "3) The art style, wrapped exactly:",
        "=== ART STYLE START ===",
        (COLOR_INTERIOR_LOCK if color_mode else LINE_ART_LOCK),
        "=== ART STYLE END ===",
        "4) TOTAL PAGE COUNT - a single number.",
        "5) STORY ARC - 3 to 5 short lines.",
        "6) The page-by-page plan. Every page in exactly this format, nothing between pages:",
        "",
        "=== PAGE 01 ===",
        "STORY TEXT: <the 1-2 short sentences for this page>",
        "STORY SCENE: <the single central story moment on this page>",
        "ILLUSTRATION TYPE: <DEFAULT for a calm page, or THEME for a key event>",
        "ILLUSTRATION DIRECTION: <" + dir_note + ">",
        "=== PAGE 02 ===",
        "...",
        "(page numbers always two digits: 01, 02, 03 ...)",
        "",
        "Keep every ILLUSTRATION DIRECTION true to the story - never add objects, places, or "
        "characters the story does not mention.",
    ]
    if not color_mode:
        lines.append("Keep each ILLUSTRATION DIRECTION a plain scene description with no words about "
                     "rendering, medium, shading, lighting, or mood - the ART STYLE block controls "
                     "the look.")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Step 2 - parse the pasted story, build one image prompt per page
# ----------------------------------------------------------------------------

PAGE_SPLIT_RE = re.compile(
    r'^[ \t]*[=#*_\-]*[ \t]*PAGE[ \t]+0*(\d+)[ \t]*[=#*_\-]*[ \t]*:?[ \t]*$',
    re.IGNORECASE | re.MULTILINE,
)
_NEXT_FIELD = r'(?=\n\s*(?:' + '|'.join(l.replace(' ', r'\s+') for l in FIELD_LABELS) + r')\s*:|\Z)'


def parse_character_bible(text):
    m = re.search(r'CHARACTER BIBLE START\s*=*\s*(.*?)\s*=*\s*CHARACTER BIBLE END',
                  text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'CHARACTER BIBLE\s*:?\s*\n(.*?)(?:\n\s*\n|\nTOTAL PAGE|\nSTORY ARC|\n=* ?PAGE)',
                  text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def split_pages(text):
    matches = list(PAGE_SPLIT_RE.finditer(text))
    by_num = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        by_num[num] = text[start:end].strip()
    return [(n, by_num[n]) for n in sorted(by_num)]


def extract_field(block, name):
    pat = re.compile(name.replace(' ', r'\s+') + r'\s*:?\s*(.*?)' + _NEXT_FIELD,
                     re.IGNORECASE | re.DOTALL)
    m = pat.search(block)
    return m.group(1).strip() if m else ""


def build_page_prompt(page_num, fields, char_bible, comp_label, shape_desc, style_desc,
                      color_mode=False, no_text=False, extra_art=""):
    text_area, illo_area = COMPOSITION[comp_label]
    story_text = fields.get("STORY TEXT") or "(use the story text for this page from your pasted story)"
    story_scene = fields.get("STORY SCENE") or ""
    illo_type = (fields.get("ILLUSTRATION TYPE") or "").upper()
    illo_dir = fields.get("ILLUSTRATION DIRECTION") or story_scene or "(see the story scene for this page)"

    beat = ("This is a key moment - a little more action and energy, still simple and uncluttered."
            if "THEME" in illo_type else
            "This is a calm page - keep it especially simple and open.")

    bible = char_bible.strip() or ("(no character sheet found - match the character exactly to your "
                                   "other pages: same species, body, face, colors, and outfit)")

    if color_mode:
        opening = "Create a clean full-color illustration for one interior page of a children's storybook, ages 4-8."
        style_lock, ink = COLOR_INTERIOR_LOCK, "dark"
    else:
        opening = "Create a clean black-and-white line-art coloring page for a children's storybook, ages 4-8."
        style_lock, ink = LINE_ART_LOCK, "solid black"

    preset_line = "Preset: " + style_desc.strip().rstrip(".") + "."
    if extra_art.strip():
        preset_line += " Also apply: " + extra_art.strip().rstrip(".") + "."

    lines = [
        opening,
        shape_desc,
        "Work only from the text in this brief - no uploaded reference picture is needed.",
        "",
        "STYLE",
        style_lock,
        preset_line,
        "",
        "CHARACTER - keep every fixed detail identical to this description:",
        bible,
        "On this page, give the character a fresh pose, gesture, expression, and camera angle that "
        "suit the moment below. Do not copy or reuse an earlier page's pose. Nothing else about the "
        "character changes.",
        "",
        "SCENE",
        illo_dir,
    ]
    if story_scene:
        lines.append("Central moment: " + story_scene.rstrip(".") + ".")
    lines += [
        "Keep the scene simple: one clear main action and only a few large elements over an open, "
        "uncluttered background. " + beat,
        "",
        "PAGE LAYOUT",
    ]
    if no_text:
        lines.append("Illustration only - no printed story text and no page number anywhere. The "
                     "picture fills the page.")
    else:
        lines += [
            "Print this exact line in a clean, child-friendly serif, " + ink + ", at a comfortable "
            "read-aloud size (filling most of its area over 2 to 4 well-spaced lines, never crowding "
            "the edges): '" + story_text + "'",
            "Put the text across the " + text_area + " and the illustration in the " + illo_area +
            ", the art fading softly into the open white - no dividing line, no panel or box around it.",
            TEXT_SAFE,
        ]
    lines.append("")
    if no_text:
        lines.append("Do not add any text, letters, numbers, title, caption, speech bubble, label, "
                     "page number, or signature anywhere. Do not add characters or objects not named "
                     "in the scene above.")
    else:
        lines.append("Do not add a page number, title, caption, speech bubble, label, or signature - "
                     "only the line above. Do not add characters or objects not named in the scene above.")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Step 3 - cover prompts (always FULL COLOR) + KDP listing helper
# ----------------------------------------------------------------------------

def cover_style_desc_for(label):
    return (STYLE_COLOR.get(label)
            or "bright, appealing, professionally finished full-color children's book cover illustration")


def build_front_cover_prompt(title, subtitle, extra_lines, badge, ctype_label, tpos_label,
                             summary, char_colors, shape_desc, cover_style_desc):
    title = title.strip()
    if title:
        title_line = ("TITLE: draw the exact text '" + title + "' as the large, dominant title in clean, "
                      "friendly lettering, in a color that stands out clearly against the background. "
                      "Place it " + TITLE_POS[tpos_label] + ".")
    else:
        title_line = ("TITLE: create a short, fitting title for this story (based on the summary below) and "
                      "draw it as the large, dominant title in clean, friendly lettering, in a color that "
                      "stands out clearly against the background. Place it " + TITLE_POS[tpos_label] + ".")

    lines = [
        "Full color FRONT COVER for a children's storybook. " + shape_desc,
        "",
        ("HOW TO USE THIS PROMPT: paste it in the SAME ChatGPT chat where you made the interior pages, so "
         "the character carries over. If you are starting a fresh chat, first upload one finished interior "
         "page so ChatGPT has the character."),
        "",
        ("Keep the exact same character from the interior pages - same identity, shapes, proportions, and "
         "outfit. Do NOT copy any page's layout or scene. Draw the character in full, rich color for a "
         "brand-new cover."),
        "",
        "COMPOSITION: " + COVER_TYPES[ctype_label],
        "HERO: the story's main character, drawn large and clearly recognizable in a fresh pose.",
        ("BACKGROUND: a new, colorful cover background suggested by the story's world, with clear space "
         "kept open for the title."),
    ]
    if char_colors.strip():
        lines.append("CHARACTER COLORS (keep these exact): " + char_colors.strip() + ".")
    lines += ["", title_line]
    if subtitle.strip():
        lines.append("SUBTITLE: smaller, placed just under the title: '" + subtitle.strip() + "'.")
    if extra_lines:
        lines.append("ALSO INCLUDE (small and neat, never competing with the title): " + extra_lines + ".")
    if badge.strip():
        lines.append("BADGE: a small, simple badge shape in one corner containing the text '" + badge.strip() + "'.")
    if summary.strip():
        lines += ["", "STORY SUMMARY (for context and the title only, do not print it on the cover): " + summary.strip()]
    lines += [
        "",
        "STYLE: " + cover_style_desc + ".",
        COLOR_COVER_LOCK,
        "Do not add any text other than what is listed above. Do not add extra characters or unrelated objects.",
    ]
    return "\n".join(lines)


def build_back_cover_prompt(summary, char_colors, cover_style_desc, shape_desc):
    lines = [
        "Full color BACK COVER for the same children's storybook. " + shape_desc,
        "",
        ("HOW TO USE THIS PROMPT: paste it in the SAME ChatGPT chat as the front cover, so it carries "
         "over. If you are starting a fresh chat, first upload the finished front cover."),
        "",
        ("Match the front cover's colors, palette, character, and style exactly. Build a NEW, simple "
         "layout - do not mirror or copy the front cover."),
        "",
        ("KEEP IT SIMPLE: a calm, mostly open background in the same color tone as the front cover, with "
         "just one small supporting element (or the character drawn small) in an upper or left area. "
         "Lots of open space."),
        "",
    ]
    if summary.strip():
        lines += [
            ("BLURB: write a short, warm back-cover blurb of 2 to 3 sentences for children and parents, "
             "based ONLY on the story summary below. Place it as clean, readable text in the upper-center "
             "area. Do not invent anything beyond the summary."),
            "Story summary: " + summary.strip(),
        ]
    else:
        lines.append("Do not add a blurb. Keep the cover clean and mostly empty.")
    if char_colors.strip():
        lines.append("CHARACTER COLORS (keep these exact): " + char_colors.strip() + ".")
    lines += [
        "",
        ("BARCODE AREA (important): keep the bottom-right corner (about 2 x 1.2 inches) clear of text and "
         "of any important artwork or focal detail, so a barcode printed there would not cover anything "
         "that matters. Let the background color and any light texture continue naturally through that "
         "corner - do NOT carve out a white box or a blank panel."),
        "",
        "STYLE: " + cover_style_desc + ".",
        COLOR_COVER_LOCK,
        ("Keep the blurb the most prominent text. Do not repeat the full title lettering from the front "
         "cover. Do not add extra characters or unrelated text. Do not draw a barcode yourself."),
    ]
    return "\n".join(lines)


def build_kdp_listing_prompt(summary, title, age, extra):
    title_line = ("Book title: '" + title.strip() + "'.") if title.strip() else \
        "The book has no fixed title yet - suggest one, then write the rest."
    age_line = ("Target age range: " + age.strip() + ".") if age.strip() else \
        "Target age range: pick a sensible one for a young children's coloring storybook."
    extra_line = ("Niche / angle words to lean on: " + extra.strip() + ".") if extra.strip() else ""
    lines = [
        "You are an Amazon KDP listing copywriter for children's coloring storybooks.",
        "Using ONLY the story summary below, write a complete Amazon listing.",
        "",
        "STORY SUMMARY: " + summary.strip(),
        title_line,
        age_line,
    ]
    if extra_line:
        lines.append(extra_line)
    lines += [
        "",
        "OUTPUT THESE THREE PARTS, clearly labelled:",
        "",
        "1) BOOK DESCRIPTION (max 4000 characters). Plain text only - no HTML tags, no "
        "markdown. Seven short sections in this order, each starting with a short standalone "
        "lead line on its own, then the rest of the section:",
        "   a. Hook - one or two lines, an emotional question or a vivid moment.",
        "   b. Tease - introduce the character and the situation without spoiling the ending.",
        "   c. What's inside - 4 to 5 bullet points of real book features (page count feel, "
        "read-aloud story on every page, clean line art, single-sided pages, etc.).",
        "   d. Perfect for - specific occasions (quiet time, gifts, road trips, classrooms).",
        "   e. Why grown-ups love it - the calm-time / fine-motor / together-time benefits.",
        "   f. Call to action - a plain 'Scroll up and add it to your cart today' style line.",
        "   g. More to come - one line hinting at other books with this character.",
        "",
        "2) SEVEN BACKEND KEYWORDS. Search phrases a parent would actually type, up to 50 "
        "characters each, no repeats of words already in the title. Mix 1-2 broader phrases "
        "with 5-6 specific long-tail phrases. One per line.",
        "",
        "3) THREE CATEGORIES from the Amazon 'Books > Children's Books' tree that best fit "
        "this story (for example: Children's Books > Animals; Children's Books > Bedtime & "
        "Dreams; Children's Books > Activity Books > Coloring Books). Give the full path for "
        "each.",
        "",
        "Keep the writing warm, clear, and honest. Do not invent characters, events, awards, "
        "or claims that are not in the summary.",
    ]
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------

if check_password():
    st.markdown('<div class="kdp-card">', unsafe_allow_html=True)
    st.title("📖 KDPEasy Storybook Prompt Kit")
    st.caption("Build ready-to-paste ChatGPT prompts for a full storybook - interior pages plus covers. "
               "This kit writes prompts only; you generate the images in ChatGPT.")

    badges = []
    if has("pages"):
        badges.append("Coloring-book mode unlocked")
    if has("pro"):
        badges.append("Full color unlocked")
    if badges:
        st.success("  |  ".join(badges))

    st.warning("**This tool does not save your work.** As you go, save ChatGPT's full story "
               "reply and each prompt (.txt) to your own computer. If the page reloads, paste "
               "your saved story back into Step 2 to carry on - it takes seconds. Your images "
               "live in ChatGPT, so save those too.")

    with st.expander("How this kit works (read first)"):
        st.markdown(
            "**What this kit does.** It writes the ChatGPT prompts for a whole storybook - the story, "
            "one illustration prompt per page, and both covers. You run those prompts in ChatGPT to "
            "make the pictures. The kit does not create images itself.\n\n"
            "**Book type** (top of the page): black-and-white storybook with text (default), a "
            "coloring book that has a full story but no text printed on the pages (OTO 1), or a "
            "full-color storybook with text (OTO 2). The three steps below work the same for all "
            "three.\n\n"
            "**Step by step**\n\n"
            "1. **Step 1 - Story.** Type your idea, copy the prompt, paste it into ChatGPT. ChatGPT "
            "writes the full story and splits it into pages. Keep this as your **story chat**.\n"
            "2. **Step 2 - Page prompts.** Paste ChatGPT's whole reply back in. You get one image "
            "prompt per page.\n"
            "3. **Make the pages.** Open a **new, separate ChatGPT chat** - your **image chat**. Paste "
            "Page 1, let it draw, then Page 2, and so on, all in this one chat.\n"
            "4. **Step 3 - Covers.** Fill the title and options, then paste the cover prompts into that "
            "same image chat.\n"
            "5. **Build the book.** Combine the images into a print-ready PDF in a separate layout "
            "tool - that is also where page numbers get added.\n\n"
            "**Good to know**\n\n"
            "- Keep the story chat and the image chat separate, or the linework fades page to page.\n"
            "- Covers are always full color.\n"
            "- If an image chat gets very long, start a fresh one and upload a finished page first.\n"
            "- ChatGPT's text-in-image is good but not perfect - expect to regenerate a few pages.\n\n"
            "**If something goes sideways**\n\n"
            "- **ChatGPT asks you to upload an image, or says it needs one to edit:** reply "
            "\"Create a brand-new image from the brief, not an edit.\" If it keeps asking, start a "
            "fresh chat and paste the page prompt again. (This is a ChatGPT quirk, not the kit.)\n"
            "- **ChatGPT offers two images for page 1:** pick your favorite, then tell it \"match "
            "every following page to this one\" so the rest of the book stays consistent.\n"
            "- **Want a different look?** Change the **Illustration style**, or type a note in "
            "**Extra art direction**, then rebuild Step 1 and Step 2 - the change flows into every "
            "page prompt. To tweak the character, edit the Character Bible in your pasted story and "
            "rebuild Step 2.\n"
            "- **Doing covers in a later session:** re-select the same **Book size** at the top "
            "first - it resets to the default each time you log in."
        )

    # ---- book type (mode) ----
    # The radio holds only the modes this buyer owns. Locked modes show below
    # it as greyed, non-clickable caption lines (Streamlit radio has no
    # per-option disable).
    _unlocked = [m for m in MODES if m[1] is None or has(m[1])]
    _locked = [m for m in MODES if m[1] is not None and not has(m[1])]
    if len(_unlocked) == 1:
        _m = _unlocked[0]
        st.markdown("**Book type:** " + _m[0])
    else:
        _pick = st.radio("Book type", [m[0] for m in _unlocked])
        _m = _unlocked[[m[0] for m in _unlocked].index(_pick)]
    _label, _flag, color_mode, no_text, _oto = _m
    for _lm in _locked:
        st.caption("🔒 " + _lm[0] + "  -  unlocks with " + _lm[4])

    # ---- style + book size ----
    if color_mode:
        style_menu = dict(STYLE_COLOR)
    else:
        style_menu = dict(STYLE_BW_FE)
        if has("pages"):
            style_menu.update(STYLE_BW_PRO)

    shape_lookup = dict(BOOK_SHAPE)

    m1, m2 = st.columns(2)
    with m1:
        if len(style_menu) > 1:
            style_label = st.selectbox("Illustration style", list(style_menu))
        else:
            style_label = list(style_menu)[0]
            st.caption("Illustration style: " + style_label)
    with m2:
        shape_label_full = st.selectbox("Book size", list(shape_lookup))
    style_desc = style_menu[style_label]
    shape_desc, shape_note = shape_lookup[shape_label_full]
    if shape_note:
        st.caption(shape_note)
    cover_style = cover_style_desc_for(style_label)

    extra_art = st.text_input(
        "Extra art direction (optional) - applied to every page",
        placeholder="e.g. even thicker outlines, fewer background objects, more white space",
    )
    st.caption("Whatever you type here is added to the STYLE section of every page prompt (and the "
               "story prompt), so one change updates the whole book. Rebuild Step 1 / Step 2 after "
               "you edit it.")

    # ---- FE preview of the upgrades ----
    if not (has("pages") and has("pro")):
        try:
            _box = st.container(border=True)
        except Exception:
            _box = st.container()
        with _box:
            st.markdown("**Unlock more with the upgrades:**")
            if not has("pages"):
                st.markdown(":lock: **OTO 1 - Coloring book.** The full story, told through the "
                            "pictures with no text printed on the pages, plus 3 more art styles. "
                            "Also includes the Upscaler and the PDF Builder.")
            if not has("pro"):
                st.markdown(":lock: **OTO 2 - Full-color storybooks.** Finished color illustrations "
                            "instead of line art, plus 6 color art styles (watercolor, colored "
                            "pencil, flat vector, papercut collage, kawaii chibi, and bold & simple).")

    tab1, tab2, tab3 = st.tabs(["Step 1 - Story", "Step 2 - Page prompts", "Step 3 - Covers"])

    # ---------------- Step 1 ----------------
    with tab1:
        idea = st.text_area(
            "Story idea", height=150,
            placeholder=("One line works, but the more you describe the closer the story stays to what "
                         "you pictured. Example:\n\n"
                         "A shy little fox named Finn loves the forest choir but is too afraid to sing. "
                         "He practices alone by the pond at night. When the choir needs a new voice, "
                         "his friends encourage him and he finally sings with them."),
        )
        st.caption("A short idea is fine. A detailed paragraph gives you a story much closer to what "
                   "you had in mind.")
        page_count = st.text_input("Page count (optional)",
                                   placeholder="blank = AI picks ~24-32; any number from 20 to 40")
        st.caption("Books are always 20 to 40 pages. On longer books ChatGPT may stop partway and end "
                   "with \"(continue)\" - just reply \"continue\" in the chat.")
        st.caption("Name or describe your character right in the story idea (like \"Pip, a small "
                   "round hedgehog in a flour-dusted apron\") and the prompt will keep it. If the "
                   "idea has no character, the AI invents one.")

        sig_story = (idea, page_count, style_label, shape_label_full, color_mode, no_text, extra_art)
        if st.button("Build Story prompt", key="btn_story"):
            if not idea.strip():
                st.warning("Enter a story idea first.")
            else:
                pcs = page_count.strip()
                if pcs.isdigit() and not (20 <= int(pcs) <= 40):
                    st.info("Page count is kept between 20 and 40 - using %d." % max(20, min(40, int(pcs))))
                _stash("out_story", sig_story,
                       build_story_prompt(idea, page_count, style_desc, shape_label_full,
                                          color_mode, no_text, extra_art))
        _sp = _recall("out_story", sig_story)
        if _sp:
            st.success("Paste this into ChatGPT. When it finishes, copy the WHOLE reply into Step 2 "
                       "AND save it in a text file on your computer.")
            st.code(_sp, language=None)
            st.download_button("Download story prompt (.txt)", data=_sp.encode("utf-8"),
                               file_name="storybook_story_prompt.txt", mime="text/plain")
            st.caption("Changed the idea or a setting above? Click **Build Story prompt** again to refresh this.")

    # ---------------- Step 2 ----------------
    with tab2:
        pasted = st.text_area("Paste ChatGPT's full story reply here", height=260, key="story_paste")
        if no_text:
            comp_label = list(COMPOSITION)[0]
            st.caption("Coloring-book mode: no text is placed on the page, so there is no text position "
                       "to set.")
        else:
            comp_label = st.selectbox("Story text position on the page", list(COMPOSITION))

        sig_pages = (pasted, comp_label, style_label, shape_label_full, color_mode, no_text, extra_art)
        if st.button("Build page prompts", key="btn_pages"):
            if not pasted.strip():
                st.warning("Paste the story from Step 1 first.")
            else:
                bible = parse_character_bible(pasted)
                pages = split_pages(pasted)
                if not pages:
                    st.error("Could not find any pages. Make sure you pasted the whole reply, including "
                             "the lines that look like '=== PAGE 01 ==='. If ChatGPT used a different "
                             "format, re-run the Step 1 prompt.")
                else:
                    out = []
                    for num, block in pages:
                        fields = {lbl: extract_field(block, lbl) for lbl in FIELD_LABELS}
                        p = build_page_prompt(num, fields, bible, comp_label, shape_desc, style_desc,
                                              color_mode, no_text, extra_art)
                        out.append((num, p))
                    _stash("out_pages", sig_pages, {"pages": out, "has_bible": bool(bible)})
        _pg = _recall("out_pages", sig_pages)
        if _pg:
            if not _pg["has_bible"]:
                st.warning("No Character Bible block found in the paste - prompts will still work, but "
                           "double-check character consistency.")
            all_text = "\n\n\n".join("PAGE %02d\n%s" % (n, p) for n, p in _pg["pages"])
            st.success("Built %d page prompt(s)." % len(_pg["pages"]))
            st.download_button("Download all page prompts (.txt)", data=all_text.encode("utf-8"),
                               file_name="storybook_page_prompts.txt", mime="text/plain", key="dl_pages_top")
            st.caption("Use this Download button - copying every box by hand is slow, and printing the "
                       "page to PDF cuts off the long lines. The same button is repeated below.")
            for num, p in _pg["pages"]:
                st.markdown("**Page %02d**" % num)
                st.code(p, language=None)
            st.download_button("Download all page prompts (.txt)", data=all_text.encode("utf-8"),
                               file_name="storybook_page_prompts.txt", mime="text/plain", key="dl_pages_bottom")
            st.caption("Changed a setting or the pasted story above? Click **Build page prompts** again to refresh.")

    # ---------------- Step 3 ----------------
    with tab3:
        st.caption("This tab makes your front cover, back cover, and Amazon listing. Start by "
                   "pasting your story summary just below.")
        summary = st.text_area("Story summary", height=90, key="cover_summary")
        st.caption("Go back to your Step 1 reply in ChatGPT. The very first part is labelled "
                   "STORY CONCEPT - copy those 2 to 3 sentences and paste them in the box above. "
                   "Everything else on this tab is optional.")
        title = st.text_input("Book title (leave blank to let ChatGPT name it from the summary)")
        subtitle = st.text_input("Subtitle (optional)")
        char_colors = st.text_input("Character colors (optional)",
                                    placeholder="russet-red fur, cream belly, forest-green scarf")
        st.caption("Character colors: the covers are always full color even for a black-and-white "
                   "book. Type the colors you want the character to be so the front and back "
                   "match. Leave blank and ChatGPT picks.")
        c4, c5 = st.columns(2)
        with c4:
            author = st.text_input("Author line (optional)", placeholder="Written by Jane Doe")
        with c5:
            pub = st.text_input("Website / brand line (optional)")
        badge = st.text_input("Badge text (optional)", placeholder="Ages 4-8  |  24 Pages to Color")
        c6, c7 = st.columns(2)
        with c6:
            ctype_label = st.selectbox("Cover type", list(COVER_TYPES))
        with c7:
            tpos_label = st.selectbox("Title position", list(TITLE_POS))
        st.caption("Cover type - AUTO: let ChatGPT choose. FULL SCENE: character inside a scene "
                   "from the story's world. CHARACTER FOCUS: the character big and front-and-"
                   "center on a simple background. GROUP SCENE: the main characters together. "
                   "MINIMAL: one hero element and lots of empty space. If unsure, use AUTO or "
                   "CHARACTER FOCUS.")

        sig_cov = (summary, title, subtitle, char_colors, author, pub, badge, ctype_label, tpos_label,
                   style_label, shape_label_full)
        if st.button("Build cover prompts", key="btn_covers"):
            extras = []
            if author.strip():
                extras.append("'" + author.strip() + "'")
            if pub.strip():
                extras.append("'" + pub.strip() + "'")
            extra_lines = ", ".join(extras)
            front = build_front_cover_prompt(title, subtitle, extra_lines, badge, ctype_label, tpos_label,
                                             summary, char_colors, shape_desc, cover_style)
            back = build_back_cover_prompt(summary, char_colors, cover_style, shape_desc)
            _stash("out_covers", sig_cov, (front, back))
        _cov = _recall("out_covers", sig_cov)
        if _cov:
            front, back = _cov
            st.success("Run these two prompts in your IMAGE chat (the same ChatGPT chat where "
                       "you made the pages). If you start a fresh chat, upload one finished "
                       "interior page first so the character matches. Front cover first, then "
                       "back cover.")
            st.markdown("**FRONT COVER prompt**")
            st.code(front, language=None)
            st.markdown("**BACK COVER prompt**")
            st.code(back, language=None)
            both = "FRONT COVER\n" + front + "\n\n\nBACK COVER\n" + back
            st.download_button("Download both cover prompts (.txt)", data=both.encode("utf-8"),
                               file_name="storybook_cover_prompts.txt", mime="text/plain")
            st.caption("Changed a field above? Click **Build cover prompts** again to refresh.")

        st.divider()
        st.markdown("### KDP listing helper")
        st.caption("Builds a prompt that makes ChatGPT write your whole Amazon listing at once: "
                   "a book description, 7 backend keywords, and 3 category suggestions. Uses the "
                   "story summary from the top of this tab.")
        kl_age = st.text_input("Age range for the listing", key="kl_age", placeholder="4-8")
        st.caption("Age range: type it like \"4-8\" or \"3-7\".")
        kl_extra = st.text_input("Niche / angle words (optional)", key="kl_extra",
                                 placeholder="bedtime, animals, kindness")
        sig_kl = (summary, title, kl_age, kl_extra)
        if st.button("Build KDP listing prompt", key="btn_kl"):
            if not summary.strip():
                st.warning("Paste the story summary at the top of this tab first.")
            else:
                _stash("out_listing", sig_kl, build_kdp_listing_prompt(summary, title, kl_age, kl_extra))
        _kl = _recall("out_listing", sig_kl)
        if _kl:
            st.success("Run this prompt in ChatGPT. Then, on your KDP 'Paperback Details' "
                       "page: paste the DESCRIPTION into the Description box, put each of "
                       "the 7 KEYWORDS in its own keyword slot, and use the 3 CATEGORIES "
                       "when KDP asks you to choose categories.")
            st.code(_kl, language=None)

    st.markdown('</div>', unsafe_allow_html=True)
