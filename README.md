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

- **Illustration style** - FE: 1 B&W preset ("Bold & simple", for ages 4-8). Rendered as a
  caption, not a dropdown, when it is the only option. OTO1 adds 3 more B&W presets
  ("A little more detail" for 7-8s, "Chunky marker", "Storybook classic"). The full-color
  mode replaces the menu with 6 `STYLE_COLOR` presets (Bold & simple, Soft watercolor,
  Colored pencil, Flat vector, Papercut collage, Kawaii chibi). "Adults - clean & detailed"
  and "Vintage midcentury" were removed 2026-08-31 - the kit is 4-8 only; standing rule is
  to drop any adult-leaning style.
- **Book size** - FE: Portrait / Square / Landscape (generic). OTO1 adds the exact KDP trims
  (8.5x8.5, 8x8, 6x9, 8x10, 8.5x11), each showing its Canva document size.

## The 3 steps

1. **Story** - a story idea (one line or a detailed paragraph) + optional page count. The
   character comes from the idea text; if there is none the AI invents one. Books are always
   **20-40 pages** (blank = AI picks ~24-32; a number is clamped). Output is one big ChatGPT
   prompt that produces: a Story Concept, a Character Bible (`=== CHARACTER BIBLE START/END
   ===`), a global `=== ART STYLE START/END ===` block, total page count, story arc, and a
   page-by-page plan (`=== PAGE 01 ===` markers, each page = STORY TEXT / STORY SCENE /
   ILLUSTRATION TYPE / ILLUSTRATION DIRECTION). The prompt tells ChatGPT to reach the page
   count with real beats not padding, to end with `(continue)` if it will be cut off, and to
   keep each ILLUSTRATION DIRECTION a plain scene description (no rendering/shading words).
   In the no-text (coloring-book) mode, ChatGPT still writes a STORY TEXT line per page, but
   is told it will not be printed on the pages.
2. **Page prompts** - paste ChatGPT's whole reply back in (repeated page numbers after a
   `(continue)` are de-duped, later block wins). Outputs one image prompt per page + a bulk
   `.txt`. With text: the story text is drawn onto the page and a "text position" control
   (AUTO/TOP/BOTTOM/LEFT/RIGHT) appears. No-text mode: the page is illustration only, the
   control is hidden, and the prompt hard-forbids any text/letters/numbers. B&W pages carry
   `LINE_ART_LOCK` + a one-line `COLORING_REMINDER`; color pages carry `COLOR_INTERIOR_LOCK`.
   No page numbers (added at the PDF-layout stage).
3. **Cover prompts + KDP listing helper** - story summary + optional title / subtitle /
   author / brand / badge / character colors + cover type + title position. Outputs a
   full-color front-cover prompt and a full-color back-cover prompt (barcode-safe:
   bottom-right corner kept clear of text/focal art, no white box). The **KDP listing
   helper** builds a prompt for ChatGPT to write a plain-text book description (7 sections,
   no HTML), 7 backend keyword phrases, and 3 category suggestions.

## Line-art lock

`LINE_ART_LOCK` forces pure black-and-white coloring-page line art: solid even-weight black
outlines on pure white, shapes closed with open white interiors, and an explicit ban on
color, grayscale, shading, shadows, hatching, crosshatching, stippling, gradients,
halftones, solid black fills, heavy ink, dark backgrounds, sketch/pencil/charcoal texture,
painterly effects, and realistic lighting. Enforced in three places (hardened from trial
feedback that images came out shaded grey): the Step 1 `=== ART STYLE ===` block, the Step 1
instruction to keep directions plain, and the Step 2 per-page `LINE_ART_LOCK` +
`COLORING_REMINDER`.

## Best results

Use **two separate ChatGPT chats**: a story chat for Step 1, and one image chat for every
page prompt and both cover prompts. All images in one chat keeps the character consistent
with no reference upload. Generating images in the story chat makes the linework fade page
to page. If an image chat gets too long, start a fresh one and upload a finished page first.
The kit stops at the images - assemble them into a print-ready PDF elsewhere (that is also
where page numbers go). **Nothing is saved** - a visible warning tells the customer to keep
the ChatGPT story reply and the prompt `.txt` files; recovery is re-pasting the story into
Step 2.

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

Flags: **pages** = OTO1 (coloring-book mode + 3 extra B&W styles + KDP trims); **pro** =
OTO2 (full-color mode + 6 color styles). `expires: None` = permanent; a `datetime.date`
works up to and including that day.

**Funnel:** FE $17 / OTO1 $27 (coloring-book mode + Upscaler + PDF Builder - the two tools
are separate apps whose own passwords go on the OTO1 thank-you page; open question whether
the Upscaler is still needed now the PDF Builder handles 300 DPI) / OTO2 $37. Series was
considered as an OTO3 and dropped for now.

**Upsell visibility for FE:** style/size stay clean (FE options only). Below them a bordered
"Unlock more with the upgrades:" panel shows one short locked line per upgrade the buyer
lacks. Locked modes also show under the Book-type radio as greyed caption lines. Light
gating, not DRM.

## Stack

Streamlit only. No fpdf2 / PyMuPDF / Pillow, no paid API, no AI calls.
