# KDPEasy Storybook Prompt Kit

Part of the KDPEasy Suite - free/paid tools for KDP creators.

Builds ready-to-paste ChatGPT prompts for a full black-and-white **coloring storybook**:
a complete narrative story split into pages, plus a matching front and back cover. The kit
writes prompts only - the customer generates the images in ChatGPT themselves.

## The 3 steps

1. **Story & Character** - enter one story idea (plus optional page count and character
   type/age/outfit). The kit builds a single prompt that makes ChatGPT write the whole
   story: a Story Concept, a locked Character Bible, and a page-by-page plan where every
   page has Story Text / Story Scene / Illustration Type / Illustration Direction, split
   with `=== PAGE 01 ===` markers.
2. **Page prompts** - paste ChatGPT's whole reply back in. The kit parses the Character
   Bible and every page, then outputs one image prompt per page. Controls: where the story
   text sits on the page (AUTO / TOP / BOTTOM / LEFT / RIGHT) and page numbering
   (AUTO odd=bottom-left / even=bottom-right, none, or forced left/right).
3. **Cover prompts** - enter title, optional subtitle / author / brand / badge, cover type,
   title position, and optional ISBN. The kit outputs a front-cover prompt (upload one
   finished interior page as the style reference) and a back-cover prompt (upload the
   finished front cover), including a reserved barcode area when an ISBN is given.

## Illustration style

One style preset is chosen at the top and applied to every step:
Pencil & ink linework, Bold simple outlines (ages 4-7), Classic storybook,
Whimsical thick-and-thin, or Clean modern minimal.

Every image prompt locks the output to pure black-and-white line art - no shading, no
grayscale, no color, white background, thick child-colorable lines, generous margins - with
only the story text and page number drawn as solid black.

## How it works

No AI is called to build the prompts - this is pure template-based text generation, so it
is instant and free to run. All customer-facing prompt text is plain ASCII so it survives a
copy-paste into ChatGPT unchanged.

Note: ChatGPT's text-in-image rendering is good but not perfect. Short captions usually come
out clean; some pages or covers will need regenerating. This is outside the kit's control
and should be stated plainly in the product description.

## Planned for v2

- Optional full-color output preset (same page structure, different style block)
- A "no plot" mode: consistent-character coloring pages without a story
- Optional one-click in-tool story generation (would use a paid API)

## Stack

Streamlit only - no fpdf2 / PyMuPDF / Pillow, since this tool outputs text, not a PDF. No
paid API, no AI calls.

Password-protected, same pattern as the rest of the KDPEasy Suite. Passwords are checked
against `PASSWORD_EXPIRY` in `app.py` - a value of `None` means permanent access, a date
means the password stops working after that day (used for time-limited trials).
