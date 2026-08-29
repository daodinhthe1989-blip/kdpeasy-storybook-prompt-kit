import re
import streamlit as st
from datetime import date

st.set_page_config(page_title="KDPEasy Storybook Prompt Kit", page_icon="📖", layout="centered")

# ----------------------------------------------------------------------------
# Access. Each password = "everything up to and including this OTO":
#   FE only .......................... KDPSTORY2026
#   FE + OTO1 (Coloring Pages) ....... KDPSTORYPAGES2026
#   FE + OTO1 + OTO2 (Pro / Color) ... KDPSTORYPRO2026
#   FE + OTO1 + OTO2 + OTO3 (Series) . KDPSTORYMAX2026
# Flags: "pages" = OTO1 no-text coloring-pages mode; "pro" = OTO2 (color +
# styles + KDP trims + character sheet + matter pages); "series" = OTO3
# (series next-book + batch). "expires": None = permanent, or a datetime.date.
# If a buyer DECLINED an earlier OTO, hand them a password matching exactly
# what they own (add a custom entry here).
# ----------------------------------------------------------------------------
PASSWORDS = {
    "KDPSTORY2026":       {"pages": False, "pro": False, "series": False, "expires": None},
    "KDPSTORYPAGES2026":  {"pages": True,  "pro": False, "series": False, "expires": None},
    "KDPSTORYPRO2026":    {"pages": True,  "pro": True,  "series": False, "expires": None},
    "KDPSTORYMAX2026":    {"pages": True,  "pro": True,  "series": True,  "expires": None},
    "KDPSTORYSERIES2026": {"pages": True,  "pro": True,  "series": True,  "expires": None},  # alias of MAX

    # 3-day trial. Works UP TO AND INCLUDING the date below, then stops.
    # Today is 2026-08-29, so this gives 2026-08-29, 30, 31 and 09-01.
    # For a new trial: change the password string AND the date.
    "KDPSTORYTRIAL2026": {"pages": False, "pro": False, "series": False, "expires": date(2026, 9, 1)},
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
            st.session_state["tier"] = {"pages": tier["pages"], "pro": tier["pro"],
                                        "series": tier["series"]}
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    return False


def has(feature: str) -> bool:
    """feature is 'pages' (OTO1), 'pro' (OTO2), or 'series' (OTO3)."""
    return bool(st.session_state.get("tier", {}).get(feature))


# ----------------------------------------------------------------------------
# Shared building blocks. All text that ends up in a customer prompt is plain
# ASCII on purpose - it gets pasted into ChatGPT, so no smart quotes / dashes.
# ----------------------------------------------------------------------------

# INTERIOR line-art styles. FE = 2 presets. Pro adds 3 more B&W presets.
STYLE_BW_FE = {
    "Kids - bold & simple": "bold, thick outlines of a single even weight, large simple shapes, very little fine detail, and big open areas to color; made for young children",
    "Adults - clean & detailed": "clean outlines of an even, medium weight, with more detail and more elements per scene and smaller areas to color, staying crisp and fully closed throughout; made for older kids and adults",
}
STYLE_BW_PRO = {
    "Fine ink detail": "fine, even ink linework with rich detail, delicate elements, and small areas to color; for confident colorists",
    "Chunky marker": "very chunky, rounded marker-style outlines, huge simple shapes, almost no small detail; for the youngest hands",
    "Storybook classic": "even classic pen linework with a calm, traditional storybook feel and balanced detail",
}
# INTERIOR full-color styles (Pro only - reached by switching Interior mode to color).
STYLE_COLOR = {
    "Kids - bold & simple": "bright, bold, cheerful full-color art: thick clean outlines, simple punchy shapes, flat lively color",
    "Adults - clean & detailed": "refined full-color illustration: clean linework, richer detail and depth, harmonious color",
    "Soft watercolor": "gentle watercolor storybook illustration with soft edges and a warm, light palette",
    "Colored pencil": "colored-pencil illustration with visible strokes, cozy and handmade",
    "Flat vector": "clean flat vector illustration with bold shapes and a bright, limited palette",
    "Papercut collage": "layered papercut and collage look with simple shapes and a soft paper texture",
    "Vintage midcentury": "vintage mid-century picture-book style with textured flat color and a muted retro palette",
    "Kawaii chibi": "cute kawaii chibi style with rounded shapes, big friendly eyes, and soft pastel color",
}

# Book size. FE = 3 generic shapes. Pro adds exact KDP trims (with the Canva doc size).
BOOK_SHAPE_FE = {
    "Portrait (tall)": ("Portrait orientation, clearly taller than wide (about 2:3). Keep extra open "
                        "white margin at the top and bottom - the final printed page may be a different height.", ""),
    "Square (1:1)": ("Square 1:1 composition, equal width and height.", ""),
    "Landscape (wide)": ("Landscape orientation, clearly wider than tall (about 3:2).", ""),
}
BOOK_SHAPE_PRO = {
    "KDP 8.5 x 8.5 in (square)": ("Square 1:1 composition, equal width and height.", "Canva document: 8.75 x 8.75 in"),
    "KDP 8 x 8 in (square)": ("Square 1:1 composition, equal width and height.", "Canva document: 8.25 x 8.25 in"),
    "KDP 6 x 9 in (portrait)": ("Portrait orientation, taller than wide, about 2:3.", "Canva document: 6.25 x 9.25 in"),
    "KDP 8 x 10 in (portrait)": ("Portrait orientation, taller than wide, about 4:5.", "Canva document: 8.25 x 10.25 in"),
    "KDP 8.5 x 11 in (portrait)": ("Portrait orientation, taller than wide, about 3:4.", "Canva document: 8.75 x 11.25 in"),
}

LINE_ART_LOCK = (
    "Pure black and white line art only. Every line the same solid, even black weight - no "
    "thick-and-thin variation, no faint or gray lines, no sketchy, broken, or doubled lines. "
    "All shapes fully closed. No shading, no hatching, no stippling, no grayscale, no gray fill, "
    "no color anywhere. Solid white background. Lines clean and heavy enough to print sharply "
    "and to color inside. Do not crop the main subject. Keep clear white margins on all four "
    "sides, nothing touching the edges. No frame, no border, no rectangle around the artwork."
)

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

MATTER_PAGES = {
    "Title page": "Center the book title '{title}' large, and beneath it in smaller text 'Written and illustrated by {author}'. One small, simple motif from the story is fine. No other text.",
    "Copyright page": "Small, plain, centered text with lots of white space: 'Text and illustrations copyright (c) {year} {author}. All rights reserved. No part of this book may be reproduced without written permission.' No artwork.",
    "Dedication page": "Center a short dedication in gentle text: '{dedication}'. Lots of white space, at most one tiny motif.",
    "This book belongs to": "Center the words 'This book belongs to' with a wide open line beneath it for a child to write their name. One small, simple decorative motif is fine. No other text.",
    "About the author": "A simple page headed 'About the Author' with the short text: '{about}'. Leave a clear space for a small round author portrait. Keep it plain.",
}


# ----------------------------------------------------------------------------
# Step 1 - Story Engine prompt
# ----------------------------------------------------------------------------

def build_story_prompt(idea, page_count_raw, ctype, cage, coutfit, style_desc, shape_label,
                       color_mode=False, series_bible=""):
    pc = page_count_raw.strip()
    if pc.isdigit():
        n = max(20, min(40, int(pc)))
        pc_line = "Aim for exactly %d story pages. Hit this number as closely as you can." % n
    else:
        pc_line = ("Choose a good length, normally 24 to 32 story pages. Never fewer than 20 and "
                   "never more than 40.")

    if color_mode:
        medium = "Every page will be drawn as a full-color storybook illustration."
        dir_note = ("what to draw, including colors, light, and mood")
        style_word = "art"
    else:
        medium = "Every page will be drawn as black-and-white line art for kids to color."
        dir_note = ("what to draw, described so it works as open black-and-white coloring line art - "
                    "no color words, no shading words")
        style_word = "drawing"

    lines = [
        "You are a children's storybook author and illustration director.",
        "Turn the story idea below into a complete, production-ready children's storybook. " + medium,
        "",
    ]
    if series_bible.strip():
        lines += [
            "THIS IS THE NEXT BOOK IN AN EXISTING SERIES.",
            "Reuse the EXACT character and world in the Character Bible below, completely unchanged.",
            "Tell a brand-new, complete, standalone story - do not retell or continue the previous plot.",
            "",
            "=== CHARACTER BIBLE START ===",
            series_bible.strip(),
            "=== CHARACTER BIBLE END ===",
            "",
        ]

    char_bits = []
    if ctype.strip():
        char_bits.append("type/species: " + ctype.strip())
    if cage.strip():
        char_bits.append("age: " + cage.strip())
    if coutfit.strip():
        char_bits.append("outfit: " + coutfit.strip())
    if series_bible.strip():
        char_line = "Use the character from the Character Bible above, unchanged."
    elif char_bits:
        char_line = "Use this main character and fill in the rest yourself: " + "; ".join(char_bits) + "."
    else:
        char_line = "Create a fitting main character yourself."

    lines += [
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
        ("<repeat the Character Bible provided above, unchanged>" if series_bible.strip()
         else "<all the fixed character details>"),
        "=== CHARACTER BIBLE END ===",
        "3) TOTAL PAGE COUNT - a single number.",
        "4) STORY ARC - 3 to 5 short lines.",
        "5) The page-by-page plan. Output EVERY page in EXACTLY this format and nothing else between pages:",
        "",
        "=== PAGE 01 ===",
        "STORY TEXT: <the 1-2 short sentences that will be printed on this page>",
        "STORY SCENE: <the single central story moment on this page>",
        "ILLUSTRATION TYPE: <DEFAULT for a quiet establishing page, or THEME for a key event page>",
        "ILLUSTRATION DIRECTION: <" + dir_note + ">",
        "=== PAGE 02 ===",
        "STORY TEXT: ...",
        "(continue for every page, page numbers always two digits: 01, 02, 03 ...)",
        "",
        "Keep ILLUSTRATION DIRECTION consistent with the story - never introduce objects, places, or "
        "characters the story does not mention.",
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


def build_page_prompt(page_num, fields, char_bible, comp_label, shape_desc, style_desc, color_mode=False):
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
        text_line = ("Print this exact story text on the page in a clean, simple, child-friendly serif, "
                     "dark and easy to read, generously spaced: '" + story_text + "'")
        lock = COLOR_INTERIOR_LOCK
    else:
        head = "Black and white line art for a single interior page of a children's coloring storybook. " + shape_desc
        text_line = ("Print this exact story text on the page in a clean, simple, child-friendly serif, "
                     "solid black, generously spaced and easy to read: '" + story_text + "'")
        lock = LINE_ART_LOCK

    lines = [
        head,
        "",
        "CHARACTER (must look identical on every page):",
        bible,
        "",
        "PAGE LAYOUT:",
        text_line,
        ("Place the story text across the " + text_area + ". Place the illustration in the " + illo_area +
         ". Let the illustration fade softly into the open page - no dividing line, no box or rectangle "
         "around the illustration, no full-bleed."),
        "",
        "ILLUSTRATION FOR THIS PAGE:",
        illo_dir,
        ("Central moment: " + story_scene) if story_scene else None,
        type_note,
        "",
        "STYLE: " + style_desc + ".",
        lock,
        ("Do not add a page number. Do not add any words, title, caption, speech bubble, label, or "
         "signature other than the story text above. Do not add characters or objects that are not part "
         "of this page's story."),
    ]
    return "\n".join(l for l in lines if l is not None)


# ----------------------------------------------------------------------------
# Step 3 - cover prompts (always FULL COLOR)
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


# ----------------------------------------------------------------------------
# Pro & Series tools (OTO 2 / OTO 3)
# ----------------------------------------------------------------------------

def build_char_sheet_prompt(bible, style_desc, color_mode):
    lock = COLOR_INTERIOR_LOCK if color_mode else LINE_ART_LOCK
    kind = "full color" if color_mode else "black and white line art"
    return "\n".join([
        "Create a single CHARACTER REFERENCE SHEET (%s) for the character described below." % kind,
        "On one page, plain white background, evenly spaced, no scene or background:",
        "- a front view, a three-quarter view, a side view, and a back view, standing",
        "- a row of five head expressions: happy, sad, surprised, scared, sleepy",
        "Keep the identity, proportions, clothing, and features identical in every view.",
        "Do not add labels, text, arrows, or a border.",
        "",
        "STYLE: " + style_desc + ".",
        lock,
        "",
        "CHARACTER:",
        bible.strip() or "(paste your Character Bible here)",
    ])


def build_matter_prompt(page_name, ctx, style_desc, color_mode):
    lock = COLOR_INTERIOR_LOCK if color_mode else LINE_ART_LOCK
    kind = "full color" if color_mode else "black and white line art"
    body = MATTER_PAGES[page_name].format(**ctx)
    return "\n".join([
        "Design a %s %s for a children's storybook, matching the book's shape." % (kind, page_name.upper()),
        body,
        "",
        "STYLE: " + style_desc + ".",
        lock,
    ])


# ----------------------------------------------------------------------------
# OTO 1 - plain coloring pages (no story, no text)
# ----------------------------------------------------------------------------

def build_scene_ideas_prompt(char, theme, n):
    t = (" around the theme of " + theme.strip()) if theme.strip() else ""
    return ("Give me %d different coloring-page scene ideas for the character below%s. "
            "Each one a short, concrete, child-friendly scene on its own line, with no "
            "numbering. Vary the action, place, and objects so the pages feel different, "
            "and give each scene plenty of things to color.\n\n"
            "CHARACTER:\n%s" % (n, t, char.strip() or "(describe your character here)"))


def build_coloring_page_prompt(scene, char, shape_desc, style_desc):
    ch = char.strip() or "(keep the exact same character on every page)"
    return "\n".join([
        "Black and white line art for a single coloring book page. " + shape_desc,
        "",
        "CHARACTER (must look identical on every page):",
        ch,
        "",
        "SCENE: " + scene.strip(),
        "",
        "STYLE: " + style_desc + ".",
        LINE_ART_LOCK,
        ("Do NOT add any text, letters, numbers, title, caption, speech bubble, or page "
         "number anywhere. Just the character in the scene, as clean, open line art to "
         "color."),
    ])


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------

if check_password():
    st.markdown('<div class="kdp-card">', unsafe_allow_html=True)
    st.title("📖 KDPEasy Storybook Prompt Kit")
    st.caption("Build ready-to-paste ChatGPT prompts for a full storybook - interior pages plus covers. "
               "This kit writes prompts only; you generate the images in ChatGPT.")

    badges = []
    if has("pro"):
        badges.append("Pro / Color unlocked")
    if has("series"):
        badges.append("Series unlocked")
    if badges:
        st.success("  |  ".join(badges))

    with st.expander("How this kit works (read first)"):
        st.markdown(
            "**What this kit does.** It writes the ChatGPT prompts for a whole storybook - the story, "
            "one illustration prompt per page, and both covers. You run those prompts in ChatGPT to "
            "make the pictures. The kit does not create images itself.\n\n"
            "**Step by step**\n\n"
            "1. **Step 1 - Story.** Type your idea, press the button, paste the prompt into ChatGPT. "
            "ChatGPT writes the full story and splits it into pages. Keep this as your **story chat**.\n"
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
            "- Black-and-white interiors have the story text drawn in. Covers are always full color.\n"
            "- If an image chat gets very long, start a fresh one and upload a finished page first.\n"
            "- ChatGPT's text-in-image is good but not perfect - expect to regenerate a few pages."
        )

    # ---- global choices ----
    # FE sees only the 2 base B&W styles and the 3 generic shapes. Pro adds
    # 3 more B&W styles + 8 full-color styles ("Color - ...") and the exact
    # KDP trims. Picking a "Color - " entry makes the interior color.
    style_menu = {}
    for _k, _v in STYLE_BW_FE.items():
        style_menu[_k] = (_v, False)
    if has("pro"):
        for _k, _v in STYLE_BW_PRO.items():
            style_menu[_k] = (_v, False)
        for _k, _v in STYLE_COLOR.items():
            style_menu["Color - " + _k] = (_v, True)

    shape_lookup = dict(BOOK_SHAPE_FE)
    if has("pro"):
        shape_lookup.update(BOOK_SHAPE_PRO)

    m1, m2 = st.columns(2)
    with m1:
        style_label = st.selectbox("Illustration style", list(style_menu))
    with m2:
        shape_label_full = st.selectbox("Book size", list(shape_lookup))

    style_desc, color_mode = style_menu[style_label]
    shape_desc, shape_note = shape_lookup[shape_label_full]
    if shape_note:
        st.caption(shape_note)

    # FE preview of the upgrades - so buyers can see what unlocking gets them.
    if not (has("pages") and has("pro")):
        try:
            _box = st.container(border=True)
        except Exception:
            _box = st.container()
        with _box:
            st.markdown("**Unlock more with the upgrades:**")
            if not has("pages"):
                st.markdown(":lock: **OTO 1 - Plain coloring pages.** One consistent "
                            "character, a page per scene, no story and no text on the page "
                            "- a straight coloring book. (Also includes the Upscaler and "
                            "PDF Builder.)")
            if not has("pro"):
                st.markdown(":lock: **OTO 2 - Full-color storybooks.** Full color instead "
                            "of line art, 10+ more art styles, exact KDP trim sizes, a "
                            "character reference sheet, and title / copyright / dedication "
                            "pages.")

    _base_style = style_label[8:] if style_label.startswith("Color - ") else style_label
    cover_style = cover_style_desc_for(_base_style)

    tab1, tab2, tab3, tab_cp, tab4 = st.tabs(
        ["Step 1 - Story", "Step 2 - Page prompts", "Step 3 - Covers",
         "Coloring pages (no story)", "Pro & Series tools"])

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
        st.markdown("**Character (all optional - leave blank for AI to invent)**")
        c1, c2, c3 = st.columns(3)
        with c1:
            ctype = st.text_input("Type / species")
        with c2:
            cage = st.text_input("Age")
        with c3:
            coutfit = st.text_input("Outfit")

        if st.button("Build Story prompt", key="btn_story"):
            if not idea.strip():
                st.warning("Enter a story idea first.")
            else:
                pcs = page_count.strip()
                if pcs.isdigit() and not (20 <= int(pcs) <= 40):
                    st.info("Page count is kept between 20 and 40 - using %d." % max(20, min(40, int(pcs))))
                st.success("Paste this into ChatGPT. When it finishes, copy the WHOLE reply into Step 2.")
                st.code(build_story_prompt(idea, page_count, ctype, cage, coutfit, style_desc,
                                           shape_label_full, color_mode), language=None)

    # ---------------- Step 2 ----------------
    with tab2:
        pasted = st.text_area("Paste ChatGPT's full story reply here", height=260, key="story_paste")
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
                        p = build_page_prompt(num, fields, bible, comp_label, shape_desc, style_desc, color_mode)
                        out.append((num, p))
                        st.markdown("**Page %02d**" % num)
                        st.code(p, language=None)
                    all_text = "\n\n\n".join("PAGE %02d\n%s" % (n, p) for n, p in out)
                    st.download_button("Download all page prompts (.txt)",
                                       data=all_text.encode("utf-8"),
                                       file_name="storybook_page_prompts.txt", mime="text/plain")

    # ---------------- Step 3 ----------------
    with tab3:
        summary = st.text_area("Story summary (paste the STORY CONCEPT text from Step 1's output)",
                               height=90, key="cover_summary")
        title = st.text_input("Book title (leave blank to let ChatGPT name it from the summary)")
        subtitle = st.text_input("Subtitle (optional)")
        char_colors = st.text_input("Character colors (optional)",
                                    placeholder="russet-red fur, cream belly, forest-green scarf")
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
            st.markdown("**FRONT COVER prompt**")
            st.code(front, language=None)
            st.markdown("**BACK COVER prompt**")
            st.code(back, language=None)
            both = "FRONT COVER\n" + front + "\n\n\nBACK COVER\n" + back
            st.download_button("Download both cover prompts (.txt)", data=both.encode("utf-8"),
                               file_name="storybook_cover_prompts.txt", mime="text/plain")

    # ---------------- Coloring pages (no story) - OTO 1 ----------------
    with tab_cp:
        st.markdown("### Plain coloring pages - no story, no text")
        st.caption("For a straight coloring book: one consistent character, a page per "
                   "scene, nothing written on the page.")
        _cp = has("pages")
        if not _cp:
            st.info("🔒 Unlock with the Coloring Pages upgrade (OTO 1).")

        cp_char = st.text_area(
            "Character - paste a Character Bible from a storybook, or describe your character",
            height=120, key="cp_char", disabled=not _cp,
            placeholder="A round, cheerful hedgehog cub with a tiny flower behind one ear "
                        "and a striped scarf.")

        st.markdown("**Need scene ideas?** Build this prompt, run it in ChatGPT, paste the "
                    "list back into the box below.")
        ci1, ci2 = st.columns(2)
        with ci1:
            cp_theme = st.text_input("Theme (optional)", key="cp_theme",
                                     placeholder="a day at the seaside", disabled=not _cp)
        with ci2:
            cp_n = st.number_input("How many ideas", min_value=5, max_value=60, value=30,
                                   step=5, key="cp_n", disabled=not _cp)
        if st.button("Build 'scene ideas' prompt", key="btn_cp_ideas", disabled=not _cp):
            st.code(build_scene_ideas_prompt(cp_char, cp_theme, int(cp_n)), language=None)

        st.divider()
        cp_scenes = st.text_area("Scene ideas (one per line)", height=180, key="cp_scenes",
                                 disabled=not _cp,
                                 placeholder="building a sandcastle with a bucket and spade\n"
                                             "collecting shells along the shoreline\n"
                                             "flying a kite shaped like a fish")
        if st.button("Build coloring page prompts", key="btn_cp", disabled=not _cp):
            scenes = [x.strip() for x in cp_scenes.splitlines() if x.strip()]
            if not scenes:
                st.warning("Enter at least one scene idea.")
            else:
                st.success("Built %d coloring page prompt(s). Generate them in one ChatGPT "
                           "image chat, anchored by your first page." % len(scenes))
                chunks = []
                for i, sc in enumerate(scenes, 1):
                    p = build_coloring_page_prompt(sc, cp_char, shape_desc, style_desc)
                    chunks.append("PAGE %02d\n%s" % (i, p))
                    st.markdown("**Page %02d**" % i)
                    st.code(p, language=None)
                st.download_button("Download all coloring page prompts (.txt)",
                                   data=("\n\n\n".join(chunks)).encode("utf-8"),
                                   file_name="coloring_page_prompts.txt", mime="text/plain")

    # ---------------- Pro & Series tools ----------------
    with tab4:
        st.markdown("### Character reference sheet  ")
        st.caption("Generate one sheet of your character (front / side / back + expressions) to anchor "
                   "every page. Make this first, then upload it into your image chat.")
        if not has("pro"):
            st.info("🔒 Unlock with the Pro upgrade (OTO 2).")
        cs_bible = st.text_area("Paste your Character Bible", height=150, key="cs_bible",
                                disabled=not has("pro"))
        if st.button("Build character-sheet prompt", key="btn_cs", disabled=not has("pro")):
            if not cs_bible.strip():
                st.warning("Paste your Character Bible first.")
            else:
                st.code(build_char_sheet_prompt(cs_bible, style_desc, color_mode), language=None)

        st.divider()
        st.markdown("### Front & back matter pages")
        st.caption("Title page, copyright, dedication, 'This book belongs to', about the author.")
        if not has("pro"):
            st.info("🔒 Unlock with the Pro upgrade (OTO 2).")
        mm1, mm2, mm3 = st.columns(3)
        with mm1:
            mm_title = st.text_input("Book title", key="mm_title", disabled=not has("pro"))
        with mm2:
            mm_author = st.text_input("Author name", key="mm_author", disabled=not has("pro"))
        with mm3:
            mm_year = st.text_input("Year", key="mm_year", value=str(date.today().year), disabled=not has("pro"))
        mm_ded = st.text_input("Dedication text", key="mm_ded", placeholder="For every child who loves to color",
                               disabled=not has("pro"))
        mm_about = st.text_input("About-the-author text", key="mm_about", disabled=not has("pro"))
        mm_pick = st.multiselect("Pages to build", list(MATTER_PAGES), default=["Title page", "Copyright page"],
                                 disabled=not has("pro"))
        if st.button("Build matter prompts", key="btn_mm", disabled=not has("pro")):
            ctx = {
                "title": mm_title.strip() or "[Book Title]",
                "author": mm_author.strip() or "[Author Name]",
                "year": mm_year.strip() or str(date.today().year),
                "dedication": mm_ded.strip() or "[your dedication]",
                "about": mm_about.strip() or "[a sentence or two about you]",
            }
            if not mm_pick:
                st.warning("Pick at least one page.")
            else:
                chunks = []
                for name in mm_pick:
                    p = build_matter_prompt(name, ctx, style_desc, color_mode)
                    chunks.append(name.upper() + "\n" + p)
                    st.markdown("**" + name + "**")
                    st.code(p, language=None)
                st.download_button("Download matter prompts (.txt)",
                                   data=("\n\n\n".join(chunks)).encode("utf-8"),
                                   file_name="storybook_matter_prompts.txt", mime="text/plain")

        st.divider()
        st.markdown("### Series - next book (same character)")
        st.caption("Paste the Character Bible from an earlier book plus a new idea. You get a Step 1 "
                   "prompt that reuses the exact character for a brand-new story.")
        if not has("series"):
            st.info("🔒 Unlock with the Series upgrade (OTO 3).")
        sr_bible = st.text_area("Character Bible from the earlier book", height=140, key="sr_bible",
                                disabled=not has("series"))
        sr_idea = st.text_area("New story idea for this book", height=110, key="sr_idea",
                               disabled=not has("series"))
        sr_pc = st.text_input("Page count (optional)", key="sr_pc", disabled=not has("series"))
        if st.button("Build series Story prompt", key="btn_sr", disabled=not has("series")):
            if not sr_bible.strip() or not sr_idea.strip():
                st.warning("Paste the Character Bible and a new story idea.")
            else:
                st.code(build_story_prompt(sr_idea, sr_pc, "", "", "", style_desc, shape_label_full,
                                           color_mode, series_bible=sr_bible), language=None)

        st.divider()
        st.markdown("### Batch - many stories at once")
        st.caption("One idea per line. You get a Step 1 prompt for each, using the settings above.")
        if not has("series"):
            st.info("🔒 Unlock with the Series upgrade (OTO 3).")
        bt_ideas = st.text_area("Story ideas, one per line", height=140, key="bt_ideas",
                                disabled=not has("series"))
        bt_pc = st.text_input("Page count for all (optional)", key="bt_pc", disabled=not has("series"))
        if st.button("Build batch Story prompts", key="btn_bt", disabled=not has("series")):
            ideas = [x.strip() for x in bt_ideas.splitlines() if x.strip()]
            if not ideas:
                st.warning("Enter at least one idea.")
            else:
                chunks = []
                for i, one in enumerate(ideas, 1):
                    p = build_story_prompt(one, bt_pc, "", "", "", style_desc, shape_label_full, color_mode)
                    chunks.append("STORY %d\n%s" % (i, p))
                    st.markdown("**Story %d**" % i)
                    st.code(p, language=None)
                st.download_button("Download all batch prompts (.txt)",
                                   data=("\n\n\n".join(chunks)).encode("utf-8"),
                                   file_name="storybook_batch_prompts.txt", mime="text/plain")

    st.markdown('</div>', unsafe_allow_html=True)
