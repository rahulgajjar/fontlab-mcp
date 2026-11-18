# Features and qualification limits

Test target: macOS, FontLab 8.4.2.8950, embedded Python 3.11.6. The development qualification used disposable font fixtures, actual MCP stdio calls, direct saved-file inspection, native reopen checks, FontTools/GlyphsLib parsing and HarfBuzz shaping. Pure transport/compiler/serialization tests are included. Private test fonts and raw diagnostics are not distributed here. This public checkout has not been qualified on FontLab 7 or Windows.

## Font Info and glyph metadata

`get_font_info` exposes 96 readable native FontInfo properties, not a whole VFJ document. Representative naming/legal/version/metrics edits and two-master targeting were tested; every setter, localized record and null state has not been qualified. `set_font_info` is a patch. Family-name changes do not rebuild every related name automatically.

`get_glyph_info` / `set_glyph_info` cover notes, color marks, tags and Unicode lists, plus basic `new_name` renaming. Source-feature/class text references are not automatically rewritten. `.notdef` is protected. Numeric `get_glyph_metrics` / `set_glyph_metrics` cover active-layer width and sidebearings. LSB shifts ink/anchors and adjusts advance to retain RSB; conflicting width/sidebearing requests are refused. Empty glyph sidebearings are null; Auto/bound-expression layers are refused. Sidebearings use axis-aligned layer bounds; italic metrics-plane behavior is unqualified.

## Points, anchors and layers

`get_glyph_source` returns all existing points/anchors/width in one selected layer as JSON, optionally standard GLIF XML. `set_glyph_source` applies coordinate/anchor/width updates with a revision and optional dry-run. Shape/contour/node counts, ordering, types, smoothness, closure and transforms must stay unchanged. This is not full VFJ replacement or arbitrary topology editing. JSON retains local shape coordinates/transforms; GLIF exchange currently requires non-component identity-transform shapes. Components must be edited at their source. Literal anchor expression storage and cloud state were tested; general expression evaluation and mark-anchor flags remain unqualified.

`get_glyph` requires `detail:construction` in this port; it reports layer roles and anchors, not a full writable VFJ glyph. `get_glyph_nodes` gives indexed coordinates/transforms. `edit_glyph_nodes` supports coordinate set/move and adjacent-handle movement; add/delete/split/type/smooth operations are not implemented. Native Undo is not qualified. A 40-point JSON/GLIF roundtrip and a cubic endpoint/handle roundtrip were tested; fractional/quadratic/open-contour/native-group breadth remains incomplete.

## Axes, masters and instances

`get_font_structure` reads axes, master locations and instances with a revision. `set_font_structure` patches/adds axes, patches named master locations and explicitly replaces `instances` when that array is supplied. Use native axis short names, such as `wt`, for coordinates. Identity renaming/deleting axes and rollback of axis insertion are not qualified. Two scalar weight-master positions and instances survived native saving. Unknown location keys cannot be enumerated from this binding.

## Features, classes and compilation

`get_features` / `set_features` exchange source, JSON files or `.fea` files with revision checks and dry-run. The source limit is 1 MiB; validation rejects include directives. Shared native classes are supplied to detached FontTools validation. `get_classes` / `set_classes` edit native OpenType memberships, not kerning classes. Nonzero class marks are refused; IDs may change. Source-defined classes and native Classes panel records are distinct.

`compile_features` compiles static GSUB/GPOS/GDEF using FontTools in the external helper, then publishes raw bytes in FontLab. Stale revisions and invalid candidates do not publish; compensation restores bytes/library data if native publication fails. Additional generated tables such as name/BASE are refused rather than silently omitted. Full variable/naming context, native Undo, visual Lookup equivalence and in-process `fontpr` compilation are unqualified. Do not start a nested MCP compiler call inside `run_python` on the same main thread.

`get_opentype_tables` inspects actual stored bytes, not a fresh export. It supports hashes, base64 and JSON/binary file export. Inline bytes are limited to 512 KiB. Publication is limited to 1 MiB of managed data.

FontLab 8 drops runtime table buffers during native saving. Explicitly published state therefore uses a checksummed **helper-managed package-library archive** under `org.fontcraft.fontlab8-mcp.storedTables.v1`, capped at 8 MiB. It is contained in the native file and rehydrates an empty byte cache through this helper. Ordinary FontLab 8 without the helper does not restore those buffers itself. Recompile after changing archived glyph order. Imported bytes inspected before publication are not automatically archived; export them if required. Unrelated library keys are preserved.

## Hint inspection

`get_font_hinting` reads stored native PS/TT/family zones and standard stems, paginated by master. `get_layer_hints` reads actual stored glyph hints, not preview detections. Positions/widths/orientation and TTH count are available; ghost, lock/link and TTH command-string decoding remain unqualified. `include_tth:true` is refused. No automatic hinting is performed.

## Native save and export

`save_font` supports constrained native VFC/VFJ saving with retained backups and restored temporary preferences. Existing native documents must use their current path and explicit `overwrite:true`. First native save requires the original basename with `.vfc`; a VFJ sidecar is created. Arbitrary Save As is not qualified. Repeated native saving and two-master data were tested. Dirty close and native Undo remain unfinished.

`export_font` writes native Glyphs, Glyphs Package, Designspace+UFO, UFO, TTF or OTF profiles to a new directory. Parser validation and a two-master descriptor were tested, not all cross-format fidelity. FontLab's no-axis single-master Designspace contains redundant empty locations rejected by FontTools; the helper preserves raw XML and removes only those empty locations. Native export can use a lowercase axis name and clip ranges to master positions even while the native document retains wider ranges.

The legacy single-master UFO snapshot path in `save_font` lost kerning in qualification and is not a whole-font backup. Prefer native source saving and the separate native export profile.

## Known gaps and safe contribution targets

Manual kerning, components/recipes, full glyph replacement, visual Lookup editing, cleanup actions and current-glyph/preview helpers need further work. Preferences and native9 assistant-file tools are intentionally low priority. Avoid broad property introspection on detached native objects: reading `fgPackage` on an unowned glyph caused a native crash during qualification. Use owned objects and disposable fixtures. Never ship a stub as a supported call just because the underlying feature exists in FontLab.
