# KDPEasy Storybook Prompt Kit

Part of the KDPEasy Suite - free/paid tools for KDP creators. Targets children's books for
**ages 4-8**.

Builds ready-to-paste ChatGPT prompts for a full children's storybook: a complete narrative
story split into 20-40 pages, plus a matching **full-color** front and back cover. The kit
writes prompts only - the customer generates the images in ChatGPT themselves. No AI is
called here; it is pure text templating, instant and free to run. All prompt text is plain
ASCII so it survives a copy-paste into ChatGPT unchanged.

## Book type (3 modes)

Shown at the top. The radio lists only the modes the buyer owns (FE = one mode, shown as a
label, no radio). Modes the buyer does not own appear below as greyed, non-clickable
`st.caption` lines with a lock icon (Streamlit radio has no per-option disable). The three
Steps below work the same for all three modes.

| Mode | What it makes | Tier | `(color_mode, no_text)` |
|---|---|---|---|
| Storybook - black & white, with text | line-art coloring storybook, story text printed on each page | FE | `(F, F)` |
| Coloring book - has a story, NO text on the pages | same full story, pages are illustration-only | OTO1 (`pages`) | `(F, T)` |
| Storybook - full color, with text | finished color illustrations + printed text | OTO2 (`pro`) | `(T, F)` |

## Style & size

- **Illustration style** - FE: 2 B&W presets ("Bold & simple" - the cleanest, thickest-line,
  least-detail look - and "Bold & rounded"). OTO1 adds 3 more ("A little more detail" for
  7-8s, "Chunky marker", "Storybook classic"). The full-color mode replaces the menu with 6
  `STYLE_COLOR` presets (Bold & simple, Soft watercolor, Colored pencil, Flat vector,
  Papercut collage, Kawaii chibi). "Adults - clean & detailed" and "Vintage midcentury" were
  removed 2026-08-31 - the kit is 4-8 only; standing rule is to drop any adult-leaning style.
  v3.2 (2026-08-31): every style string was rewritten shorter and cleaner, and the shared
  line-art spec now explicitly bans detail creep (see Line-art spec below) after anh compared
  a busy output to the original clean Pip test.
- **Book size** - one shared list for every tier (`BOOK_SHAPE`, merged out of the old
  FE/OTO1 split 2026-08-31): six real KDP trims - 8.5x8.5, 8x8, 6x9, 8x10, 8.5x11, and
  11x8.5 landscape. Each option's prompt **leads with the trim in inches** ("Printed at
  8.5 x 11 inches - a tall portrait page. Ask ChatGPT for a tall portrait image.") plus the
  shared `SAFE_AREA` centered-safe-area rule. ChatGPT's image tool only outputs 1:1, 2:3,
  3:2, so a raw ratio number appears ONLY where a trim genuinely is one (1:1 for the two
  squares, 2:3 for 6x9); everywhere else it just says "tall portrait" / "wide landscape".
  8x10 and 8.5x11 are not a clean 2:3, so their prompts add "keep the top and bottom of the
  image especially open (background only)" and their captions say to **crop** (not stretch,
  not letterbox) the slightly-too-tall portrait down to the page. Rewrite 2026-08-31 (v3.1.1)
  after anh flagged that picking 8.5x11 produced a prompt talking about "2:3". Page size is a
  basic need, and gating it behind OTO1 was what made FE pages crop.

All prompts were rewritten in v3.2 (2026-08-31) as clean, sectioned briefs - customers read
them closely, and the previous versions had grown a visible pile of patch clauses. Each
prompt is now half the length of the v3.1 one and reads professionally.

1. **Story** - a story idea (one line or a detailed paragraph) + optional page count. Books
   are always **20-40 pages** (blank = 24-32; a number is clamped). Output is one ChatGPT
   prompt, laid out as sections (STORY / CHARACTER / ART & SCENES / OUTPUT), that makes
   ChatGPT produce: a Story Concept, a Character Bible (`=== CHARACTER BIBLE START/END ===`),
   an `=== ART STYLE START/END ===` block, total page count, story arc, and a page-by-page
   plan (`=== PAGE 01 ===` markers; each page = STORY TEXT / STORY SCENE / ILLUSTRATION TYPE
   / ILLUSTRATION DIRECTION). It tells ChatGPT to reach the count with real beats, to end
   with `(continue)` if cut off, to **keep every scene simple - one main action, a few large
   elements, an open background**, and (B&W only) to keep each ILLUSTRATION DIRECTION a plain
   scene description with no rendering/shading words. Character consistency: one fixed
   identity (species, body, face, hair/fur, colors, and the *complete* outfit and
   accessories) kept identical on every page; only pose, gesture, expression, camera angle,
   action, and background change. In no-text mode ChatGPT still writes a STORY TEXT line per
   page, just not printed.
2. **Page prompts** - paste ChatGPT's whole reply back in (repeated page numbers after a
   `(continue)` are de-duped, later block wins). Outputs one image prompt per page + a bulk
   `.txt`, with a **Download button both above and below** the prompts (a tester copied 30
   boxes by hand because the single bottom button was past a long scroll). Each page prompt is
   a sectioned brief: opening + trim + "work only from this brief, no uploaded reference
   needed" / STYLE (`LINE_ART_LOCK` or `COLOR_INTERIOR_LOCK` + the chosen preset + any Extra
   art direction) / CHARACTER (match the fixed details, fresh pose for this page) / SCENE
   (the ILLUSTRATION DIRECTION + "keep the scene simple") / PAGE LAYOUT. With text: the exact
   line is drawn on the page, a text-position control (AUTO/TOP/BOTTOM/LEFT/RIGHT) appears,
   and `TEXT_SAFE` keeps a >=10% edge margin at a **read-aloud size** (fill most of the text
   area over 2-4 lines - not shrunk). No-text mode: illustration only, control hidden, all
   text/letters/numbers forbidden. No page numbers (added at the PDF-layout stage).

**Extra art direction** (v3.3, 2026-08-31): a free-text field next to the style menu. Its
text is appended to the STYLE section of every page prompt and to the story prompt's ART &
SCENES note (`extra_art` param on `build_story_prompt` / `build_page_prompt`), so one nudge
- "even thicker outlines", "fewer background objects" - flows into the whole book instead of
being pasted into 32 prompts by hand. It is part of the Step 1 / Step 2 signatures, so
changing it invalidates the stashed output.
3. **Cover prompts + KDP listing helper** - story summary + optional title / subtitle /
   author / brand / badge / character colors + cover type + title position. Outputs a
   full-color front-cover prompt and a full-color back-cover prompt (barcode-safe:
   bottom-right corner kept clear of text/focal art, no white box). The **KDP listing
   helper** builds a prompt for ChatGPT to write a plain-text book description (7 sections,
   no HTML), 7 backend keyword phrases, and 3 category suggestions.

## Line-art spec

`LINE_ART_LOCK` is one clean paragraph (rewritten v3.2 from the old shouty "ABSOLUTELY NO:"
wall; the redundant `COLORING_REMINDER` patch line is gone). It asks for bold, smooth,
even-weight black outlines on pure white, big simple shapes with open white interiors, and
bans, in one list: color, gray, shading/shadows, hatching/crosshatching, stippling,
solid black fills, **fur / hair / wood-grain / fabric texture**, **scribbled ground lines**,
**sparkle or motion marks**, and **busy backgrounds** - the last four added after anh
compared a cluttered output to the original clean Pip test. It appears in the Step 1
`=== ART STYLE ===` block and once per Step 2 page prompt (STYLE section). `COLOR_INTERIOR_LOCK`
is the color-mode equivalent ("a few large elements, not a busy scene").

## Best results

Use **two separate ChatGPT chats**: a story chat for Step 1, and one image chat for every
page prompt and both cover prompts. All images in one chat keeps the character consistent
with no reference upload. Generating images in the story chat makes the linework fade page
to page. If an image chat gets too long, start a fresh one and upload a finished page first.
The kit stops at the images - assemble them into a print-ready PDF elsewhere (that is also
where page numbers go). **Nothing is saved to disk** - a visible warning tells the customer
to keep the ChatGPT story reply and the prompt `.txt` files; recovery is re-pasting the
story into Step 2.

Within a session, every built output (story prompt, page prompts, cover prompts, listing
prompt) is stashed in `st.session_state` via `_stash` / `_recall`, keyed by the inputs that
produced it. Streamlit reruns the whole script on any click - including the download
buttons - so before this, clicking Download wiped the prompts off screen (a repeated trial
complaint: "the tool disappeared"). Now the output stays visible until an input actually
changes, then clears itself cleanly. A full browser refresh still clears everything (that is
the "nothing is saved to disk" case).

## Tiers (funnel) & passwords

`PASSWORDS` maps each password to `{pages, pro, expires}`. **One password per product - it
unlocks ONLY that product's mode. Not stacked.** The cart delivers each product's own
password automatically. A buyer logs in with one password per session; the green banner
shows what it unlocked. A buyer who owns both OTOs switches by logging in again with the
other password (the automated cart can't tell who owns what, so no combo password and no
in-app accumulation - decided 2026-08-30/31).

| Password | Unlocks | Delivered by |
|---|---|---|
| `KDPSTORY2026` | access only | FE |
| `KDPSTORYPAGES2026` | `pages` | OTO1 |
| `KDPSTORYPRO2026` | `pro` | OTO2 |
| `KDPSTORYTRIAL2026` | access only, expires 2026-09-01 | 3-day free trial |

Flags: **pages** = OTO1 (coloring-book mode + 3 extra B&W styles); **pro** =
OTO2 (full-color mode + 6 color styles). Book size is not gated - every tier gets all
six KDP trims. `expires: None` = permanent; a `datetime.date` works up to and including
that day.

**Funnel:** FE $17 / OTO1 $27 (coloring-book mode + Upscaler + PDF Builder - the two tools
are separate apps whose own passwords go on the OTO1 thank-you page; open question whether
the Upscaler is still needed now the PDF Builder handles 300 DPI) / OTO2 $37. Series was
considered as an OTO3 and dropped for now.

**Upsell visibility for FE:** the style menu stays clean (FE options only); book size is the
full list for everyone. Below them a bordered "Unlock more with the upgrades:" panel shows
one short locked line per upgrade the buyer lacks. Locked modes also show under the
Book-type radio as greyed caption lines. Light gating, not DRM.

## Stack

Streamlit only. No fpdf2 / PyMuPDF / Pillow, no paid API, no AI calls.
