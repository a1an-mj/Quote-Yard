# Quote Yard brand — "Side-eye"

**The idea:** two eyes glancing sideways, with pupils shaped like quote marks. It's a shopper checking the next shop's price before buying.
**Line:** *Give every price the side-eye.* · എല്ലാ വിലയും ഒന്ന് നോക്കിയിട്ട് വാങ്ങാം.

## 1. Logo files (`svg/` masters, `png/` renders)

| File | Use |
|---|---|
| `quoteyard-horizontal-*.svg` | Default logo: site header, documents, social banners |
| `quoteyard-stacked-*.svg` | Square-ish spaces: posters, splash screens, merch |
| `quoteyard-symbol.svg` | The mark alone: avatars, stickers, anywhere the name is already shown |
| `quoteyard-symbol-small.svg` | **At 32 px and below** (favicon, tab, tiny UI): bigger eyes and pupils |
| `quoteyard-wordmark-*.svg` | Name only, when the symbol appears nearby |
| `quoteyard-app-icon*.svg` | Full-bleed app icons; the OS applies the corner mask. `-maskable` has Android safe-zone padding |

Colourways: `colour` (on cream or white), `on-dark` (on ink), `on-red` (cream one-colour on red), `black`, `white`.
In the one-colour versions the eyes are real cut-outs, so they show the background colour.

## 2. Colour

| Name | HEX | RGB | Role |
|---|---|---|---|
| Side-eye Red | `#F2492B` | 242 73 43 | Logo tile, CTA buttons, big headlines |
| Red Deep | `#C8341A` | 200 52 26 | Red **text** under 24 px on light grounds (4.9:1) |
| Cream | `#FFF4E4` | 255 244 228 | Eye whites, warm panels |
| Paper | `#FFF8EF` | 255 248 239 | Page background |
| Ink | `#1A1413` | 26 20 19 | Text, pupils, dark grounds |
| Red (dark mode) | `#FF6B4A` | 255 107 74 | Brand red on ink grounds (6.6:1) |
| Deal Green *(functional)* | `#127A3E` | 18 122 62 | Lowest price, price down, in stock |

For print, match Side-eye Red against a physical Pantone swatch book. Don't trust a screen conversion. It sits in the warm-red / red-orange family.

**The red rule:** red is the *brand* colour, **never a data colour**. Lowest price, savings and "in stock" are always green. Price-up and error states use their own muted crimson (`--qy-err #A3203B`), never Side-eye Red. On a price site, red usually means "worse", and we don't want the logo colour to say that.

**Contrast:** ink text on red is 5.0:1, which passes AA. Cream or white text on red is about 3.4:1, which is only OK for large text (24 px+ bold) or the logo itself. Buttons use **ink text on red**.

## 3. Typography

| Role | Font | Settings |
|---|---|---|
| Wordmark, big headlines, Log in / Create your account titles | **Bricolage Grotesque** | ExtraBold 800, opsz 96, tracking −1.5 % |
| Page titles ("Today's deals", "Categories"…) | **Bricolage Grotesque** | Bold 700, opsz 48, tracking −1 % |
| UI, body, section titles | **Geist** | 400–600 |
| Prices, small labels, codes | **Geist Mono** | 400–500, `tabular-nums` |
| Big counters and step numbers | **Doto** (dot-matrix) | 800 |

The site has no Malayalam text, so no Malayalam font is loaded. If Malayalam is added later, add a Malayalam font (Anek Malayalam fits Bricolage) after Geist.

Bricolage Grotesque is SIL Open Font License (free, logo use allowed). The site self-hosts it from `frontend/src/assets/fonts/`.

## 4. Clear space and minimum size

- **Clear space:** keep at least **one eye's width** (≈ 35 % of the symbol height) clear on every side.
- **Minimum size:** horizontal logo 96 px wide on screen / 25 mm in print. Symbol 20 px. Below 32 px, use `symbol-small`.
- In the horizontal lockup, the symbol height = wordmark height (ascender to descender), and the gap = 30 % of the symbol height. Don't re-space it.

## 5. Motion

On hover or focus, the pupils glance the other way (`translateX(-30)` on the pupils, 450 ms, ease-out). It's already built into `.qy-logo`, and it switches off when the user prefers reduced motion. Good places to reuse it: the pupils sliding towards the cheapest row, or a "looking…" loading state.

## 6. Don'ts

- Don't recolour the pupils, or put the mark on red without the cream one-colour version.
- Don't use red for prices, savings badges or "lowest" highlights.
- Don't stretch, rotate, outline or add shadows to the mark.
- Don't retype "quoteyard" in a font. Use the outlined wordmark (the spacing is custom).
- Don't put the colour logo on busy photos. Use the one-colour version on a solid panel.
- Don't make the eyes look left by default. The resting glance is to the right (forward, to the next price).

## 7. Notes

- Get a trademark search (Indian Trade Marks Registry, classes 35/42) and a reverse image search before registering.
- The wordmark is Bricolage Grotesque, outlined and re-spaced. The spacing is custom, but the letter shapes are the font's. A later step could redraw a few letters (the `y` and `q`) to fully own them.
