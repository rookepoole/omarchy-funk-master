# Funk Master — design research

Researched September 5, 2026. These are three strong historical directions for this project, not a statistical ranking of current trends.

## 1. Psychedelic poster graphics

The V&A describes the revival of Art Nouveau motifs within 1960s psychedelic graphics. This supports fluid contours, rhythmic repetition, and expressive display lettering. For the desktop, concentrate distortion in the artwork and branding while keeping interface text legible.

Source: [V&A — A short history of the poster](https://www.vam.ac.uk/articles/a-short-history-of-the-poster).

## 2. P-Funk and Afrofuturist world-building

The Smithsonian's National Museum of African American History and Culture describes Parliament-Funkadelic's cosmic narratives, Mothership stage imagery, and comic-inspired visual universe, including the contributions of Pedro Bell, Overton Loyd, and Diem Jones. This is rooted in Black musical and cultural innovation; it provides the project's cosmic, humorous attitude. The new wallpaper uses an original vinyl planet and strange floating eyes, without reproducing an album cover or an existing character.

Source: [NMAAHC — Parliament Funkadelic, Nona Hendryx, and LaBelle](https://www.searchablemuseum.com/parliament-funkadelic-nona-hendryx-and-labelle/).

## 3. Memphis postmodern design

The Design Museum documents the Memphis group's unconventional materials, exuberant colors, kitsch motifs, and patterned surfaces. This suggests the warped checkerboard fragments, angular squiggles, contrasting color accents, and deliberately playful proportions used in Funk Master. Memphis is a separate design movement, combined here with psychedelic and funk references as a contemporary interpretation.

Source: [Design Museum — Memphis](https://designmuseum.org/memphis).

## Design decisions

| Element | Translation into the desktop |
|---|---|
| Background | Near-black aubergine, with a quieter left side for working windows |
| Primary text | Warm cream rather than pure white |
| Primary action / focus | Acid lime |
| Hover / secondary emphasis | Hot pink |
| Extra rhythm | Tangerine, electric lilac, mint |
| Windows | 20 px rounding, 3 px three-color borders, 16 px outer gaps |
| Motion | Brief glides and subtle pop-in, no continuous desktop animation |
| Bar | 38 px high, record badge, ON AIR clock label |
| Typography | Existing system monospace for tools; C059 bold italic on the badge |
| Native apps | Dark mode and Yaru magenta folders, with app theming through Omarchy templates |

The live install uses Omarchy 4.0.2-1 with Hyprland 0.56.2 and the Lua/Quickshell configuration architecture. Source files under `/usr/share/omarchy/` were inspected to confirm supported theme keys; package files were not changed.

Technical reference: [Hyprland — Variables](https://wiki.hypr.land/Configuring/Basics/Variables/).
