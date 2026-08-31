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


# ----------------------------------------------------------------------------
# Shared building blocks. All text that ends up in a customer prompt is plain
# ASCII on purpose - it gets pasted into ChatGPT, so no smart quotes / dashes.
# ----------------------------------------------------------------------------

# INTERIOR line-art styles. The kit targets ages 4-8 - no "adult" detail level.
# FE = 2 thick-line presets. OTO1 adds 3 more B&W presets.
STYLE_BW_FE = {
    "Bold & simple": "bold, thick outlines of a single even weight, large simple shapes, very little fine detail, and big open areas to color; made for children ages 4-8",
    "Bold & rounded": "bold, thick outlines with every shape softly rounded and curved - friendly and cuddly, large simple shapes, very little fine detail, and big open areas to color; made for children ages 4-8",
}
STYLE_BW_PRO = {
    "A little more detail": "clean, even, medium-weight outlines with a bit more detail and a few more elements per scene, still fully closed and easy for a 7-8 year old to color",
    "Chunky marker": "very chunky, rounded marker-style outlines, huge simple shapes, almost no small detail; for the youngest hands",
    "Storybook classic": "even classic pen linework with a calm, traditional storybook feel and balanced detail",
}
# INTERIOR full-color styles - only reachable in the full-color mode (OTO2).
STYLE_COLOR = {
    "Bold & simple": "bright, bold, cheerful full-color art: thick clean outlines, simple punchy shapes, flat lively color",
    "Soft watercolor": "gentle watercolor storybook illustration with soft edges and a warm, light palette",
    "Colored pencil": "colored-pencil illustration with visible strokes, cozy and handmade",
    "Flat vector": "clean flat vector illustration with bold shapes and a bright, limited palette",
    "Papercut collage": "layered papercut and collage look with simple shapes and a soft paper texture",
    "Kawaii chibi": "cute kawaii chibi style with rounded shapes, big friendly eyes, and soft pastel color",
}

# Book size. One list for everyone - real KDP trims. First tuple item goes into
# the prompts; second is a UI caption telling the customer the layout doc size
# and which ratio to actually ask ChatGPT for (it only renders 1:1, 2:3, 3:2).
SAFE_AREA = ("Keep every important part of the picture - faces, the main character, key objects - "
             "inside a centered safe area with wide, even margins on all four sides. Nothing that "
             "matters near the edges, so the art still fits when it is placed on the printed page "
             "even if the page proportion is a little different.")
BOOK_SHAPE = {
    "KDP 8.5 x 8.5 in - square (most popular)": (
        "Square 1:1 composition, equal width and height. " + SAFE_AREA,
        "Layout / Canva document: 8.75 x 8.75 in (includes bleed). Ask ChatGPT for a 1:1 square image - exact match.",
    ),
    "KDP 8 x 8 in - square": (
        "Square 1:1 composition, equal width and height. " + SAFE_AREA,
        "Layout / Canva document: 8.25 x 8.25 in (includes bleed). Ask ChatGPT for a 1:1 square image - exact match.",
    ),
    "KDP 6 x 9 in - portrait": (
        "Portrait orientation, taller than wide, at a 2:3 width-to-height ratio. " + SAFE_AREA,
        "Layout / Canva document: 6.25 x 9.25 in (includes bleed). Ask ChatGPT for a 2:3 portrait image - this trim matches it exactly.",
    ),
    "KDP 8 x 10 in - portrait": (
        "Portrait orientation, taller than wide, near a 4:5 ratio. " + SAFE_AREA,
        "Layout / Canva document: 8.25 x 10.25 in (includes bleed). Ask ChatGPT for a 2:3 portrait image, then add thin side margins in layout - do not stretch it to fill.",
    ),
    "KDP 8.5 x 11 in - portrait (US Letter)": (
        "Portrait orientation, tall, near a 3:4 ratio. " + SAFE_AREA,
        "Layout / Canva document: 8.75 x 11.25 in (includes bleed). Ask ChatGPT for a 2:3 portrait image, then add side margins in layout - do not stretch it to fill.",
    ),
    "Landscape 11 x 8.5 in - wide": (
        "Landscape orientation, clearly wider than tall, near a 3:2 ratio. " + SAFE_AREA,
        "Layout / Canva document: 11.25 x 8.75 in (includes bleed). Ask ChatGPT for a 3:2 landscape image.",
    ),
}

LINE_ART_LOCK = (
    "Pure black-and-white COLORING PAGE line art only: solid black outlines on a pure white "
    "background. Every line the same solid, even black weight - no thick-and-thin variation, "
    "no faint or gray lines, no sketchy, broken, or doubled lines. All shapes fully closed, "
    "with open white areas inside every shape for coloring. "
    "ABSOLUTELY NO: color, grayscale, gray tones, shading, shadows, hatching, crosshatching, "
    "stippling, gradients, halftones, solid black fills, heavy ink areas, dark or black "
    "backgrounds, sketch or pencil or charcoal texture, painterly effects, or realistic "
    "lighting. "
    "Lines clean and heavy enough to print sharply and to color inside. Do not crop the main "
    "subject. Keep clear white margins on all four sides, nothing touching the edges. No "
    "frame, no border, no rectangle around the artwork."
)

COLORING_REMINDER = ("Remember: this is a clean black-and-white coloring page - black outlines "
                     "only, pure white background, no shading, no gray, no filled areas, open "
                     "white spaces to color.")

COLOR_INTERIOR_LOCK = (
    "Full color children's storybook illustration - bright, warm, and appealing, with a harmonious "
    "palette and gentle shading. Clean, solid shapes. Do not crop the main subject. Keep clear "
    "margins on all four sides, nothing touching the edges. No frame, no border, no rectangle "
    "around the artwork."
)

COLOR_COVER_LOCK = (
    "Full color, professionally finished children's book cover art - bright, appealing, and warm, "
    "with a harmonious palette and good contrast. This is NOT black and white and NOT a coloring page. "
    "Keep clear margins; no important element touching the edges; no frame or border."
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

def build_story_prompt(idea, page_count_raw, style_desc, shape_label, color_mode=False, no_text=False):
    pc = page_count_raw.strip()
    if pc.isdigit():
        n = max(20, min(40, int(pc)))
        pc_line = "Aim for exactly %d story pages. Hit this number as closely as you can." % n
    else:
        pc_line = ("Choose a good length, normally 24 to 32 story pages. Never fewer than 20 and "
                   "never more than 40.")

    if color_mode:
        medium = "Every page will be drawn as a full-color storybook illustration."
        dir_note = "what to draw, including colors, light, and mood"
        style_word = "art"
    else:
        medium = "Every page will be drawn as black-and-white line art for kids to color."
        dir_note = ("what to draw, described so it works as open black-and-white coloring line art - "
                    "no color words, no shading words")
        style_word = "drawing"
    if no_text:
        medium += (" The story text will NOT be printed on the pages - the story is told through the "
                   "pictures - but still write a STORY TEXT line for every page (the customer may read "
                   "it aloud or place it elsewhere).")

    char_line = ("If the story idea already names or describes a character, use exactly that "
                 "character and fill in the rest of its look yourself. Otherwise, create a "
                 "fitting main character.")

    lines = [
        "You are a children's storybook author and illustration director.",
        "Turn the story idea below into a complete, production-ready children's storybook. " + medium,
        "",
        "STORY IDEA: " + idea.strip(),
        "PAGES: " + pc_line,
        "CHARACTER: " + char_line,
        "",
        "Write in natural, simple, warm, child-friendly English with short sentences. "
        "Tell one clear story with a beginning, a middle event or discovery, and a satisfying ending. "
        "Follow the customer's story idea closely - keep the characters, setting, events, and ending "
        "they describe. If the idea is only a short line, invent the rest in the same spirit. Either "
        "way keep the story coherent and on-topic: every page belongs to this one story.",
        "",
        "The book must have at least 20 and at most 40 story pages.",
        "",
        "How to reach the page count: break the story into more, smaller beats - one action, "
        "discovery, feeling, or step of the journey per page - and let secondary characters and each "
        "stop along the way have their own page. Do NOT reach the count by repeating scenes, "
        "restating the same idea, or adding events the idea does not support. If the idea is genuinely "
        "too small for the target number, get as close as you can with real beats, then say so in one "
        "short line.",
        "",
        "If your reply would be cut off before the last page, stop at a clean page boundary and end "
        "with a line that says exactly: (continue) - the customer will then ask you to continue.",
        "",
        "Give the character a fixed visual identity (species, age look, body, face, distinctive features, "
        "clothing, accessories) and keep it identical on every page. Only pose, expression, action, and "
        "setting may change.",
        "",
        "OUTPUT IN THIS EXACT ORDER, with no commentary before or after:",
        "1) STORY CONCEPT - 2 to 3 sentences.",
        "2) The Character Bible, wrapped exactly like this:",
        "=== CHARACTER BIBLE START ===",
        "<all the fixed character details>",
        "=== CHARACTER BIBLE END ===",
        "3) The global art style, wrapped exactly like this:",
        "=== ART STYLE START ===",
        (COLOR_INTERIOR_LOCK if color_mode else LINE_ART_LOCK),
        "=== ART STYLE END ===",
        "4) TOTAL PAGE COUNT - a single number.",
        "5) STORY ARC - 3 to 5 short lines.",
        "6) The page-by-page plan. Output EVERY page in EXACTLY this format and nothing else between pages:",
        "",
        "=== PAGE 01 ===",
        "STORY TEXT: <the 1-2 short sentences for this page>",
        "STORY SCENE: <the single central story moment on this page>",
        "ILLUSTRATION TYPE: <DEFAULT for a quiet establishing page, or THEME for a key event page>",
        "ILLUSTRATION DIRECTION: <" + dir_note + ">",
        "=== PAGE 02 ===",
        "STORY TEXT: ...",
        "(continue for every page, page numbers always two digits: 01, 02, 03 ...)",
        "",
        "Keep ILLUSTRATION DIRECTION consistent with the story - never introduce objects, places, or "
        "characters the story does not mention.",
        ("Write each ILLUSTRATION DIRECTION as a plain description of WHAT is in the scene "
         "(character pose, action, setting, props). Do NOT put any words about rendering, "
         "medium, shading, shadows, lighting, mood, gray, or black areas in it - the global "
         "ART STYLE block above controls all of that."),
        "Planned " + style_word + " style for later, keep the directions compatible with it: " + style_desc + ".",
        "The finished art will be " + shape_label + " - keep each scene composable in that shape.",
    ]
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
                      color_mode=False, no_text=False):
    text_area, illo_area = COMPOSITION[comp_label]
    story_text = fields.get("STORY TEXT") or "(use the story text for this page from your pasted story)"
    story_scene = fields.get("STORY SCENE") or ""
    illo_type = (fields.get("ILLUSTRATION TYPE") or "").upper()
    illo_dir = fields.get("ILLUSTRATION DIRECTION") or story_scene or "(see the story scene for this page)"

    if "THEME" in illo_type:
        type_note = "This is a key story moment - give the illustration more detail, action, and energy."
    else:
        type_note = "This is a calmer establishing page - keep the illustration simple and open."

    bible = char_bible.strip() or ("(match the character exactly to your other pages: same species, age, "
                                   "face, clothing, and accessories)")

    if color_mode:
        head = "Full color illustration for a single interior page of a children's storybook. " + shape_desc
        lock = COLOR_INTERIOR_LOCK
    else:
        head = "Black and white line art for a single interior page of a children's coloring storybook. " + shape_desc
        lock = LINE_ART_LOCK

    lines = [head, ""]
    lines += ["CHARACTER (must look identical on every page):", bible, ""]

    if no_text:
        lines += [
            "PAGE LAYOUT:",
            ("Fill the page with just the illustration. There is NO story text and NO page number "
             "anywhere on this page - it is an illustration only."),
        ]
    else:
        text_line = ("Print this exact story text on the page in a clean, simple, child-friendly serif, "
                     + ("dark" if color_mode else "solid black") +
                     ", generously spaced and easy to read: '" + story_text + "'")
        lines += [
            "PAGE LAYOUT:",
            text_line,
            ("Place the story text across the " + text_area + ". Place the illustration in the " + illo_area +
             ". Let the illustration fade softly into the open page - no dividing line, no box or rectangle "
             "around the illustration, no full-bleed."),
        ]

    lines += [
        "",
        "ILLUSTRATION FOR THIS PAGE:",
        illo_dir,
        ("Central moment: " + story_scene) if story_scene else None,
        type_note,
        (None if color_mode else COLORING_REMINDER),
        "",
        "STYLE: " + style_desc + ".",
        lock,
    ]

    if no_text:
        lines.append("Do NOT add ANY text, letters, numbers, words, title, caption, speech bubble, "
                     "label, page number, or signature anywhere on the page. Do not add characters "
                     "or objects that are not part of this page's story.")
    else:
        lines.append("Do not add a page number. Do not add any words, title, caption, speech bubble, "
                     "label, or signature other than the story text above. Do not add characters or "
                     "objects that are not part of this page's story.")
    return "\n".join(l for l in lines if l is not None)


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
            "- ChatGPT's text-in-image is good but not perfect - expect to regenerate a few pages."
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

        if st.button("Build Story prompt", key="btn_story"):
            if not idea.strip():
                st.warning("Enter a story idea first.")
            else:
                pcs = page_count.strip()
                if pcs.isdigit() and not (20 <= int(pcs) <= 40):
                    st.info("Page count is kept between 20 and 40 - using %d." % max(20, min(40, int(pcs))))
                st.success("Paste this into ChatGPT. When it finishes, copy the WHOLE reply into Step 2 "
                           "AND save it in a text file on your computer.")
                _sp = build_story_prompt(idea, page_count, style_desc, shape_label_full, color_mode, no_text)
                st.code(_sp, language=None)
                st.download_button("Download story prompt (.txt)", data=_sp.encode("utf-8"),
                                   file_name="storybook_story_prompt.txt", mime="text/plain")

    # ---------------- Step 2 ----------------
    with tab2:
        pasted = st.text_area("Paste ChatGPT's full story reply here", height=260, key="story_paste")
        if no_text:
            comp_label = list(COMPOSITION)[0]
            st.caption("Coloring-book mode: no text is placed on the page, so there is no text position "
                       "to set.")
        else:
            comp_label = st.selectbox("Story text position on the page", list(COMPOSITION))

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
                    if not bible:
                        st.warning("No Character Bible block found in the paste - prompts will still "
                                   "work, but double-check character consistency.")
                    st.success("Built %d page prompt(s)." % len(pages))
                    out = []
                    for num, block in pages:
                        fields = {lbl: extract_field(block, lbl) for lbl in FIELD_LABELS}
                        p = build_page_prompt(num, fields, bible, comp_label, shape_desc, style_desc,
                                              color_mode, no_text)
                        out.append((num, p))
                        st.markdown("**Page %02d**" % num)
                        st.code(p, language=None)
                    all_text = "\n\n\n".join("PAGE %02d\n%s" % (n, p) for n, p in out)
                    st.download_button("Download all page prompts (.txt)",
                                       data=all_text.encode("utf-8"),
                                       file_name="storybook_page_prompts.txt", mime="text/plain")

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

        st.divider()
        st.markdown("### KDP listing helper")
        st.caption("Builds a prompt that makes ChatGPT write your whole Amazon listing at once: "
                   "a book description, 7 backend keywords, and 3 category suggestions. Uses the "
                   "story summary from the top of this tab.")
        kl_age = st.text_input("Age range for the listing", key="kl_age", placeholder="4-8")
        st.caption("Age range: type it like \"4-8\" or \"3-7\".")
        kl_extra = st.text_input("Niche / angle words (optional)", key="kl_extra",
                                 placeholder="bedtime, animals, kindness")
        if st.button("Build KDP listing prompt", key="btn_kl"):
            if not summary.strip():
                st.warning("Paste the story summary at the top of this tab first.")
            else:
                st.success("Run this prompt in ChatGPT. Then, on your KDP 'Paperback Details' "
                           "page: paste the DESCRIPTION into the Description box, put each of "
                           "the 7 KEYWORDS in its own keyword slot, and use the 3 CATEGORIES "
                           "when KDP asks you to choose categories.")
                st.code(build_kdp_listing_prompt(summary, title, kl_age, kl_extra), language=None)

    st.markdown('</div>', unsafe_allow_html=True)
