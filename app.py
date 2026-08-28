import re
import streamlit as st
from datetime import date

st.set_page_config(page_title="KDPEasy Storybook Prompt Kit", page_icon="📖", layout="centered")

# Password -> expiry date, or None for permanent access (paying customers).
PASSWORD_EXPIRY = {
    "KDPSTORY2026": None,
}

CUSTOM_CSS = """
<style>
:root {
    color-scheme: light;
}
.stApp {
    background: linear-gradient(135deg, #eef2ff 0%, #ffffff 60%);
}
.kdp-card {
    background: white;
    border-radius: 16px;
    padding: 2rem 2rem 1.5rem;
    box-shadow: 0 4px 24px rgba(79, 70, 229, 0.08);
    margin-bottom: 1.5rem;
}
h1, h2, h3 { color: #4f46e5; }
.stButton>button, .stDownloadButton>button {
    background-color: #10b981;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.6rem 1.4rem;
    font-weight: 600;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    background-color: #059669;
    color: white;
}
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
        if pw in PASSWORD_EXPIRY:
            expiry = PASSWORD_EXPIRY[pw]
            if expiry is None or date.today() <= expiry:
                st.session_state["authed"] = True
                st.rerun()
            else:
                st.error("This trial password has expired. Please reach out to get full access.")
        else:
            st.error("Incorrect password.")
    st.markdown('</div>', unsafe_allow_html=True)
    return False


# ----------------------------------------------------------------------------
# Shared building blocks. All text that ends up in a customer prompt is plain
# ASCII on purpose - it gets pasted into ChatGPT, so no smart quotes / dashes.
# ----------------------------------------------------------------------------

# Line-art vocabulary - used for the INTERIOR pages. Two presets, split by audience.
# Both rely on LINE_ART_LOCK for the print-safe rules; the preset only sets line
# weight and detail density.
STYLE_PRESETS = {
    "Kids - bold & simple": "bold, thick outlines of a single even weight, large simple shapes, very little fine detail, and big open areas to color; made for young children",
    "Adults - clean & detailed": "clean outlines of an even, medium weight, with more detail and more elements per scene and smaller areas to color, staying crisp and fully closed throughout; made for older kids and adults",
}

# Full-color version of the same 2 presets - used for the COVERS.
COVER_STYLE = {
    "Kids - bold & simple": "bright, bold, cheerful full-color children's book cover: thick clean outlines, simple punchy shapes, flat lively color",
    "Adults - clean & detailed": "refined full-color illustrated cover: clean linework, richer detail and depth, harmonious polished color",
}

BOOK_SHAPE = {
    "Portrait (tall)": ("Portrait orientation, clearly taller than wide (about 2:3). Keep extra open "
                        "white margin at the top and bottom - the final printed page may be a different height."),
    "Square (1:1)": "Square 1:1 composition, equal width and height.",
    "Landscape (wide)": "Landscape orientation, clearly wider than tall (about 3:2).",
}

LINE_ART_LOCK = (
    "Pure black and white line art only. Every line the same solid, even black weight - no "
    "thick-and-thin variation, no faint or gray lines, no sketchy, broken, or doubled lines. "
    "All shapes fully closed. No shading, no hatching, no stippling, no grayscale, no gray fill, "
    "no color anywhere. Solid white background. Lines clean and heavy enough to print sharply "
    "and to color inside. Do not crop the main subject. Keep clear white margins on all four "
    "sides, nothing touching the edges. No frame, no border, no rectangle around the artwork."
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


# ----------------------------------------------------------------------------
# Step 1 - Story Engine prompt
# ----------------------------------------------------------------------------

def build_story_prompt(idea, page_count_raw, ctype, cage, coutfit, style_desc, shape_label):
    pc = page_count_raw.strip()
    if pc.isdigit():
        pc_line = "Make the book exactly %d pages." % int(pc)
    else:
        pc_line = ("Choose the best number of pages, normally 10 to 16, never fewer than 10. "
                   "No filler pages - every page must move the story forward.")

    char_bits = []
    if ctype.strip():
        char_bits.append("type/species: " + ctype.strip())
    if cage.strip():
        char_bits.append("age: " + cage.strip())
    if coutfit.strip():
        char_bits.append("outfit: " + coutfit.strip())
    if char_bits:
        char_line = "Use this main character and fill in the rest yourself: " + "; ".join(char_bits) + "."
    else:
        char_line = "Create a fitting main character yourself."

    lines = [
        "You are a children's coloring storybook author and illustration director.",
        "Turn the story idea below into a complete, production-ready children's COLORING storybook. "
        "Every page will be drawn as black-and-white line art for kids to color.",
        "",
        "STORY IDEA: " + idea.strip(),
        "PAGES: " + pc_line,
        "CHARACTER: " + char_line,
        "",
        "Write in natural, simple, warm, child-friendly English with short sentences. "
        "Tell one clear story with a beginning, a middle event or discovery, and a satisfying ending. "
        "Follow the customer's story idea closely - keep the characters, setting, events, and ending "
        "they describe. If the idea is only a short line, invent the rest in the same spirit. Either "
        "way keep the story focused: do not pad it with subplots, characters, or repetition the idea "
        "does not call for.",
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
        "3) TOTAL PAGE COUNT - a single number.",
        "4) STORY ARC - 3 to 5 short lines.",
        "5) The page-by-page plan. Output EVERY page in EXACTLY this format and nothing else between pages:",
        "",
        "=== PAGE 01 ===",
        "STORY TEXT: <the 1-2 short sentences that will be printed on this page>",
        "STORY SCENE: <the single central story moment on this page>",
        "ILLUSTRATION TYPE: <DEFAULT for a quiet establishing page, or THEME for a key event page>",
        "ILLUSTRATION DIRECTION: <what to draw, described so it works as open black-and-white coloring "
        "line art - no color words, no shading words>",
        "=== PAGE 02 ===",
        "STORY TEXT: ...",
        "(continue for every page, page numbers always two digits: 01, 02, 03 ...)",
        "",
        "Keep ILLUSTRATION DIRECTION consistent with the story - never introduce objects, places, or "
        "characters the story does not mention.",
        "Planned drawing style for later, keep the directions compatible with it: " + style_desc + ".",
        "The finished art will be " + shape_label + " - keep each scene composable in that shape.",
    ]
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Step 2 - parse the pasted story, build one image prompt per page
# ----------------------------------------------------------------------------

# Tolerant page-header match: "=== PAGE 01 ===", "Page 1:", "### PAGE 3 ###",
# "**PAGE 02**", "-- page 4 --", etc.
PAGE_SPLIT_RE = re.compile(
    r'^[ \t]*[=#*_\-]*[ \t]*PAGE[ \t]+0*(\d+)[ \t]*[=#*_\-]*[ \t]*:?[ \t]*$',
    re.IGNORECASE | re.MULTILINE,
)

_NEXT_FIELD = r'(?=\n\s*(?:' + '|'.join(l.replace(' ', r'\s+') for l in FIELD_LABELS) + r')\s*:|\Z)'


def parse_character_bible(text):
    m = re.search(
        r'CHARACTER BIBLE START\s*=*\s*(.*?)\s*=*\s*CHARACTER BIBLE END',
        text, re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    m = re.search(
        r'CHARACTER BIBLE\s*:?\s*\n(.*?)(?:\n\s*\n|\nTOTAL PAGE|\nSTORY ARC|\n=* ?PAGE)',
        text, re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    return ""


def split_pages(text):
    matches = list(PAGE_SPLIT_RE.finditer(text))
    pages = []
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        pages.append((num, text[start:end].strip()))
    return pages


def extract_field(block, name):
    pat = re.compile(
        name.replace(' ', r'\s+') + r'\s*:?\s*(.*?)' + _NEXT_FIELD,
        re.IGNORECASE | re.DOTALL,
    )
    m = pat.search(block)
    return m.group(1).strip() if m else ""


def build_page_prompt(page_num, fields, char_bible, comp_label, shape_desc, style_desc):
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

    lines = [
        "Black and white line art for a single interior page of a children's coloring storybook. " + shape_desc,
        "",
        "CHARACTER (must look identical on every page):",
        bible,
        "",
        "PAGE LAYOUT:",
        ("Print this exact story text on the page in a clean, simple, child-friendly serif, solid black, "
         "generously spaced and easy to read: '" + story_text + "'"),
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
        LINE_ART_LOCK,
        ("Do not add a page number. Do not add any words, title, caption, speech bubble, label, or "
         "signature other than the story text above. Do not add characters or objects that are not part "
         "of this page's story."),
    ]
    return "\n".join(l for l in lines if l is not None)


# ----------------------------------------------------------------------------
# Step 3 - cover prompts (FULL COLOR)
# ----------------------------------------------------------------------------

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
        "Full color FRONT COVER for a children's coloring storybook. " + shape_desc,
        "",
        ("HOW TO USE THIS PROMPT: upload one finished interior page (your black-and-white line art) into "
         "ChatGPT together with this prompt."),
        "",
        ("The uploaded page is BLACK AND WHITE line art. Use it ONLY as the reference for the character's "
         "identity, shapes, proportions, and outfit. Do NOT copy its layout or scene, and do NOT make the "
         "cover black and white. Redraw the same character in full, rich color for a brand-new cover."),
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
        "Full color BACK COVER for the same children's coloring storybook. " + shape_desc,
        "",
        ("HOW TO USE THIS PROMPT: upload your finished FRONT COVER into ChatGPT together with this prompt."),
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
        ("BARCODE SPACE (important): leave the entire BOTTOM-RIGHT corner completely empty and clean - a "
         "plain rectangular area about 2 inches wide by 1.2 inches tall, light and flat, with no artwork, "
         "no text, and no pattern. This space is reserved for the barcode that KDP prints."),
        "",
        "STYLE: " + cover_style_desc + ".",
        COLOR_COVER_LOCK,
        ("Keep the blurb the most prominent text. Do not repeat the full title lettering from the front "
         "cover. Do not add extra characters or unrelated text. Do not draw a barcode yourself."),
    ]
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------

if check_password():
    st.markdown('<div class="kdp-card">', unsafe_allow_html=True)
    st.title("📖 KDPEasy Storybook Prompt Kit")
    st.caption("Build ready-to-paste ChatGPT prompts for a full coloring storybook - black-and-white line "
               "art interior pages plus full-color covers. This kit writes prompts only; you generate the "
               "images in ChatGPT.")

    with st.expander("How this kit works (read first)"):
        st.markdown(
            "1. **Step 1** builds a prompt that makes ChatGPT write your whole story, split into pages.\n"
            "2. Paste ChatGPT's reply into **Step 2** to get one image prompt per page.\n"
            "3. **Step 3** builds your front and back cover prompts.\n\n"
            "**For the crispest line art, generate each page in a NEW ChatGPT chat** - not the same "
            "chat you wrote the story in. In one long chat the linework fades page after page. Each "
            "page prompt already carries the full character description, so the character stays "
            "consistent across separate chats. For extra safety, upload your finished Page 01 image "
            "into each new chat along with the prompt and say \"match this character exactly\".\n\n"
            "Interior pages come out as clean black-and-white line art with the page text drawn in. "
            "**Covers come out in full color** - upload one finished interior page (front cover) or your "
            "finished front cover (back cover) so the character matches.\n\n"
            "The kit does not add page numbers - add those later when you lay the book out as a PDF. "
            "ChatGPT's text-in-image is good but not perfect; expect to regenerate a few pages."
        )

    cs1, cs2 = st.columns(2)
    with cs1:
        style_label = st.selectbox("Illustration style", list(STYLE_PRESETS))
    with cs2:
        shape_label = st.selectbox("Book shape", list(BOOK_SHAPE))
    style_desc = STYLE_PRESETS[style_label]
    shape_desc = BOOK_SHAPE[shape_label]

    tab1, tab2, tab3 = st.tabs(["Step 1 - Story & Character", "Step 2 - Page prompts", "Step 3 - Cover prompts"])

    with tab1:
        idea = st.text_area(
            "Story idea",
            height=150,
            placeholder=("One line works, but the more you describe the closer the story stays to what "
                         "you pictured. Example:\n\n"
                         "A shy little fox named Finn loves the forest choir but is too afraid to sing. "
                         "He practices alone by the pond at night. When the choir needs a new voice, "
                         "his friends encourage him and he finally sings with them."),
        )
        st.caption("A short idea is fine. A detailed paragraph - characters, setting, what happens, how "
                   "it ends - gives you a story much closer to what you had in mind.")
        page_count = st.text_input("Page count (optional)", placeholder="leave blank = let AI choose 10-16")
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
                st.success("Paste this into ChatGPT. When it finishes, copy the WHOLE reply into Step 2.")
                st.code(build_story_prompt(idea, page_count, ctype, cage, coutfit, style_desc, shape_label),
                        language=None)

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
                    st.error("Could not find any pages. Make sure you pasted the whole reply, including the "
                             "lines that look like '=== PAGE 01 ==='. If ChatGPT used a different format, "
                             "re-run the Step 1 prompt.")
                else:
                    if not bible:
                        st.warning("No Character Bible block found in the paste - prompts will still work, "
                                   "but double-check character consistency.")
                    st.success("Built %d page prompt(s)." % len(pages))
                    out = []
                    for num, block in pages:
                        fields = {lbl: extract_field(block, lbl) for lbl in FIELD_LABELS}
                        p = build_page_prompt(num, fields, bible, comp_label, shape_desc, style_desc)
                        out.append((num, p))
                        st.markdown("**Page %02d**" % num)
                        st.code(p, language=None)
                    all_text = "\n\n\n".join("PAGE %02d\n%s" % (n, p) for n, p in out)
                    st.download_button("Download all page prompts (.txt)",
                                       data=all_text.encode("utf-8"),
                                       file_name="storybook_page_prompts.txt",
                                       mime="text/plain")

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
                                             summary, char_colors, shape_desc, COVER_STYLE[style_label])
            back = build_back_cover_prompt(summary, char_colors, COVER_STYLE[style_label], shape_desc)
            st.markdown("**FRONT COVER prompt** - upload one finished interior page with this prompt.")
            st.code(front, language=None)
            st.markdown("**BACK COVER prompt** - upload your finished front cover with this prompt.")
            st.code(back, language=None)
            both = "FRONT COVER\n" + front + "\n\n\nBACK COVER\n" + back
            st.download_button("Download both cover prompts (.txt)",
                               data=both.encode("utf-8"),
                               file_name="storybook_cover_prompts.txt",
                               mime="text/plain")

    st.markdown('</div>', unsafe_allow_html=True)
