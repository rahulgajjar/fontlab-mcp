# Changelog

## v0.4.1 — First public prerelease

The unofficial MCP adapter exposes 35 scoped tools for licensed FontLab 8 on macOS. The tested build is FontLab 8.4.2.8950, and the external helper requires Python 3.11 or later.

- Create and open fonts, list open documents, select the active font, close clean documents and save native VFC/VFJ files under documented path and overwrite rules.
- Read and edit Font Info, master metrics, glyph metadata, numeric spacing and anchors.
- Read indexed contour points and exchange existing layer coordinates as JSON or GLIF XML while preserving contour topology.
- Inspect and edit axes, master locations and instance metadata. Inspect native layer roles.
- Edit OpenType feature source and class membership, compile layout tables with FontTools and publish managed GSUB, GPOS and GDEF tables. Inspect stored OpenType tables, master zones and stems and stored glyph hints.
- Export through native Glyphs, Glyphs Package, Designspace+UFO, UFO, TTF and OTF profiles.
- Provide MCP workflow guidance and a persistent Python namespace that executes inside FontLab with the local user's privileges.

Native Undo and visual Lookup behavior remain unqualified. Arbitrary native Save As, component construction and manual kerning are outside this release's tool coverage. FontLab 7 and Windows are outside the supported platform scope. See [feature details and limits](docs/FEATURES.md) and [test and support status](docs/TESTING.md).
