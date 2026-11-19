# Unofficial MCP Adapter for FontLab 8

**Independent community project. Not developed, supplied, endorsed or supported by Fontlab. Requires your own valid FontLab license.**

Control an opened FontLab 8 font from an MCP-capable agent: inspect and edit Font Info, glyph metadata, contours, anchors, spacing, masters, axes, instances, features and OpenType classes, then save or export through FontLab.

**Tested on macOS with FontLab 8.4.2.8950.** The app's embedded Python 3.11 and PythonQt run native operations on its main thread. The external helper was tested with Python 3.14; Python 3.11+ is required. Windows and FontLab 7 are not currently supported or verified.

This is an independent compatibility adapter, not an official FontLab product and not FontLab 9's binary backend. You need your own licensed FontLab installation. The app bundle is not modified.

## Releases

**v0.4.1 is the first public prerelease.** See the [changelog](CHANGELOG.md), [GitHub releases](https://github.com/rahulgajjar/fontlab-mcp/releases) and [release workflow](docs/RELEASING.md). Use a tagged release for a reproducible installation; the main branch may contain newer changes.

## Install

1. Download or clone this repository, then open a terminal in its directory.
2. Create an isolated environment and install dependencies:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python install.py
   ```

3. Save your documents and restart FontLab 8. Alternatively, refresh Scripts and run **Start MCP Adapter for FontLab 8** for first-time loading. Avoid starting multiple runtime copies in one session.
4. Add the server to your MCP client's configuration, replacing the command with the absolute path to this checkout:

   ```json
   {
     "mcpServers": {
       "fontlab8-native": {
         "command": "/absolute/path/to/this/repository/fontlab8-mcp",
         "args": []
       }
     }
   }
   ```

   See [mcp-config.example.json](mcp-config.example.json). Reload the client's MCP connection, open a font in FontLab, and call `list_fonts`. Use the returned font ID on writes.

### Codex

From this repository directory, register the same launcher with Codex:

```sh
codex mcp add fontlab8-native -- "$(pwd)/fontlab8-mcp"
codex mcp get fontlab8-native --json
```

This writes a `[mcp_servers.fontlab8-native]` entry in Codex configuration. Refresh/reconnect MCP or start a fresh Codex session if an existing conversation still has its previous tool catalog. A configured/enabled entry is not by itself proof of a live font connection: test `list_fonts` after FontLab starts. See [OpenAI's MCP configuration guide](https://developers.openai.com/codex/mcp).

The launcher finds this checkout's `.venv`; no machine-specific username or interpreter path is embedded. If you move the checkout, recreate `.venv` and update the MCP command path.

See [test/support status](docs/TESTING.md), [Font Info field reference](docs/FONT_INFO.md) and [installation and troubleshooting](docs/INSTALLATION.md) for installed locations, removal and recovery.

## What works

- **Font Info:** read native metadata and bulk-edit representative naming, legal, version and metric fields; target individual masters.
- **Glyph data:** names, Unicode, notes, marks, tags, width, LSB and RSB.
- **Outlines:** indexed points or whole-layer JSON/GLIF XML read/write, including anchors. Coordinate exchange preserves existing topology.
- **Families:** inspect/edit axes, master locations and instance metadata; inspect native layer roles.
- **Features/classes:** view/edit source or `.fea` files, revision checks, native OpenType class membership, detached FontTools compilation and managed layout-table publication.
- **Engineering:** inspect stored OpenType bytes, zones/stems and stored glyph hints.
- **Saving/export:** constrained native VFC/VFJ saving; native Glyphs, Glyphs Package, Designspace+UFO, UFO, TTF and OTF export.

These are **scoped implementations, not full FontLab 9 parity**. Native Undo, arbitrary Save As, component construction, manual kerning and several advanced workflows remain incomplete. Some node operations, hint fields, variable-feature context and visual Lookup behavior are unqualified. Read [feature details and limits](docs/FEATURES.md) and [workflow examples](docs/EXAMPLES.md) before bulk edits.

Keep backups and verify exported fonts. A timed-out write can have an unknown outcome: inspect the document before retrying. `run_python` executes code inside FontLab with your local user's privileges; connect only trusted clients.

## Contributions and bug reports

Pull requests, issues and reproducible bug reports are welcome. Include macOS/FontLab/Python versions, the exact tool call, expected/actual results and a minimal **disposable** font or reproduction script you are permitted to share. Remove private font data, credentials and personal paths from logs.

**FontLab 7 support is welcome as a contribution.** It needs explicit Python/runtime, profile-path and native API qualification; do not assume the FontLab 8 installer works with it. Windows ports and additional verified workflows are also welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Free to use, including professional font work. Project software cannot be sold or incorporated into closed derivatives. Distributed/deployed modifications must provide source under the same terms and be submitted upstream within the license's stated period. Your fonts and other outputs retain their own licenses.

This uses a **custom source-available license**, not an OSI-approved open-source license. See [LICENSE](LICENSE) and [license policy](LICENSE_POLICY.md). The custom terms should receive legal review before publication; no standard-license approval or universal enforceability is claimed.

## MCP tool comparison: FontLab 9 and this FontLab 8 adapter

This is a tool-availability comparison, not a comparison of the full applications or a claim of equivalent behavior. FontLab 9 provides its own MCP integration; this unofficial adapter connects MCP clients to FontLab 8 through its Python scripting APIs.

The table covers the 56 tools in the compared FontLab 9 MCP catalog and nine additional adapter tools. “Listed” records catalog presence only; it does not independently verify every FontLab 9 operation. “Supported, with limits” describes this adapter’s documented scope, not identical options or output. Unsupported tools are not advertised.

MCP is a separate protocol, and FontLab Python scripting is an existing extension mechanism. The table describes tool availability, not authorship or licensing of those technologies. See the separate [provenance notes](docs/PROVENANCE.md) for how the compatibility interfaces were developed.

<!-- BEGIN PUBLIC COMPARISON -->

**This adapter offers 35 tools: 26 share names with tools in FontLab 9 MCP, and 9 are additional adapter tools.**

| Tool | Purpose | FontLab 9 MCP catalog | This FontLab 8 adapter | Adapter coverage / limitations |
|---|---|---|---|---|
| `new_font` | Create a font. | Listed | Supported, with limits | Only the default Latin Simple repertoire is qualified. |
| `open_font` | Open a font file. | Listed | Supported, with limits | Basic native operation. |
| `save_font` | Save the opened font. | Listed | Supported, with limits | Native in-place VFC/VFJ save with retained backups; existing files require overwrite=true. First native save requires original basename.vfc and creates a VFJ sidecar. Native Save As to another path is refused. UFO remains a limited single-master snapshot. |
| `close_font` | Close a font document. | Listed | Supported, with limits | Clean fonts only. Dirty fonts and save=true are refused without opening a dialog. No forced discard. |
| `list_fonts` | List opened fonts. | Listed | Supported, with limits | Basic native operation. |
| `get_active_font` | Identify the active font. | Listed | Supported, with limits | Basic native operation. |
| `set_active_font` | Choose the active font. | Listed | Supported, with limits | Basic native operation. |
| `get_features` | Read feature source and revision. | Listed | Supported, with limits | Native source, shared FontGate classes and glyph order with revision. Not native compiled lookup access. |
| `set_features` | Replace feature source with validation. | Listed | Supported, with limits | Source replacement with FontTools validation, revision/dry-run and 1 MiB limit; include() refused. Raw layout bytes preserved. Native Undo and visual Lookup state not qualified. |
| `compile_features` | Compile and publish layout tables. | Listed | Supported, with limits | FontTools feaLib detached compilation via MCP stdio, then raw GSUB/GPOS/GDEF publication with compensation and native package-library archive for persistence. 1 MiB compiled/8 MiB archive limits; additional generated tables refused. Native Undo, visual lookup behavior and fontpr compilation are not qualified. |
| `get_opentype_tables` | Inspect/export stored OpenType bytes. | Listed | Supported, with limits | Reads native runtime table bytes; helper-managed archives rehydrate after native save/reopen. Not fresh export/compilation. Inline data limited to 512 KiB; larger data requires file export. |
| `get_font_info` | Read font metadata. | Listed | Supported, with limits | Returns 96 native FontInfo fields, not full VFJ package JSON; detail=full only. Master selection is supported. |
| `get_font_hinting` | Read master zones and standard stems. | Listed | Supported, with limits | Reads native PS/TT/family zones and PS/TT stems, per master with pagination. No automatic hinting. |
| `set_font_info` | Bulk-edit font metadata. | Listed | Supported, with limits | Native FontInfo field patches and masters[] are supported. scale_upm=true, axes/instances and arbitrary VFJ replacement are not qualified. |
| `list_glyphs` | List/filter glyph names and Unicode values. | Listed | Supported, with limits | Names/unicodes and query/has_unicode pagination only; facts/geometry filters are not ported. |
| `get_glyph` | Read glyph construction/data. | Listed | Supported, with limits | detail=construction only: layer flags and anchors; full VFJ/component detail and attachment analysis not ported. |
| `set_glyph_anchors` | Add/edit/remove anchors. | Listed | Supported, with limits | Native position/name/remove/expression/cloud fields; mark_enabled and native undo not qualified. |
| `get_layer_hints` | Read stored glyph-layer hints. | Listed | Supported, with limits | Reads native stored PS hint position/width/orientation/name and TTH count. Ghost, lock/link decoding and include_tth command strings are not qualified; no hint detection. |
| `get_glyph_nodes` | Read indexed contour points. | Listed | Supported, with limits | Indexed local nodes and transforms; extrema computation not ported. |
| `edit_glyph_nodes` | Edit indexed contour points. | Listed | Supported, with limits | Coordinate set/move only; preflight/dry-run supported, native undo not qualified. Components and Auto layers refused. |
| `get_font_metrics` | Read font metrics. | Listed | Supported, with limits | Basic native operation. |
| `set_font_metrics` | Change font metrics. | Listed | Supported, with limits | Basic native operation. |
| `get_glyph_metrics` | Read width and sidebearings. | Listed | Supported, with limits | Numeric width/LSB/RSB and current expression strings; empty glyph sidebearings are null. |
| `set_glyph_metrics` | Change numeric width and sidebearings. | Listed | Supported, with limits | Manual numeric width/LSB/RSB. LSB shifts ink and advance together to retain RSB; explicit width/RSB conflicts rejected. Bound expressions and Auto layers refused. |
| `run_python` | Execute Python inside FontLab. | Listed | Supported, with limits | Persistent agent namespace inside FontLab 8; not the Scripting panel namespace. fontpr/mcp_tools expose only this ported subset. |
| `get_python_output` | Read captured Python output. | Listed | Supported, with limits | Only output captured from this adapter’s most recent run_python call, not the entire FontLab Output panel. |
| `export_font` | Export through native font profiles. | Not in compared catalog | Supported, with limits | FontLab 8 extension (not one of the native 9 catalog's 56 names): export using a native profile to a new directory. Interchange may omit FontLab-only data. |
| `get_glyph_info` | Read name, Unicode, spacing and glyph metadata. | Not in compared catalog | Supported, with limits | read notes, color marks, tags and Unicode scalars for named glyphs. |
| `set_glyph_info` | Bulk-edit names, Unicode, notes, marks and tags. | Not in compared catalog | Supported, with limits | preflight and apply bulk glyph metadata patches; native undo not qualified. Supports explicit new_name; does not rewrite feature/class text references or replace outlines. |
| `get_glyph_source` | Read all layer points/anchors as JSON or GLIF. | Not in compared catalog | Supported, with limits | Read all existing layer points/anchors/width as native JSON or GLIF XML. Not a full FontLab document serializer. |
| `set_glyph_source` | Write point/anchor coordinates while preserving topology. | Not in compared catalog | Supported, with limits | Write layer coordinates, width and anchors from JSON or GLIF; revision required. Existing shape/contour/node topology, types and smooth flags must remain unchanged; no native undo. |
| `get_font_structure` | Read axes, master locations and instances. | Not in compared catalog | Supported, with limits | Read native axes, master locations and instance metadata with revision. Locations enumerate known axis short names only. |
| `set_font_structure` | Change axes, locations and instance metadata. | Not in compared catalog | Supported, with limits | Patch/add axes and master locations; instances[] replaces the instance list. Revision/preflight/dry-run; native undo and rollback of axis insertion are not qualified. |
| `get_classes` | Read native OpenType class membership. | Not in compared catalog | Supported, with limits | Read native OpenType class memberships plus native panel summary; kerning class editing is excluded. |
| `set_classes` | Create/edit/remove OpenType class membership. | Not in compared catalog | Supported, with limits | Patch/create/remove OpenType class memberships by name, with revision and dry-run. No native undo; nonzero class marks and kerning groups are refused. |
| `get_preferences` | Read application preferences. | Listed | Not supported | Not implemented; not advertised. |
| `set_preferences` | Change application preferences. | Listed | Not supported | Not implemented; not advertised. |
| `list_aidus_files` | List assistant workspace files. | Listed | Not supported | Not implemented; not advertised. |
| `read_aidus_file` | Read an assistant workspace file. | Listed | Not supported | Not implemented; not advertised. |
| `write_aidus_file` | Write an assistant workspace file. | Listed | Not supported | Not implemented; not advertised. |
| `get_lookups` | Read visual lookup definitions. | Listed | Not supported | Not implemented; not advertised. |
| `set_lookups` | Change visual lookup definitions. | Listed | Not supported | Not implemented; not advertised. |
| `get_current_glyphs` | Read current/selected glyphs. | Listed | Not supported | Not implemented; not advertised. |
| `get_active_glyphs` | Read current glyphs (alias). | Listed | Not supported | Not implemented; not advertised. |
| `explain` | Explain native object properties. | Listed | Not supported | Not implemented; not advertised. |
| `set_active_glyph` | Choose the current glyph. | Listed | Not supported | Not implemented; not advertised. |
| `build_glyph` | Construct a glyph from a recipe. | Listed | Not supported | Not implemented; not advertised. |
| `edit_layer_hints` | Edit glyph-layer PostScript hints. | Listed | Not supported | Not implemented; not advertised. |
| `geometry` | Calculate vector/Bezier geometry. | Listed | Not supported | Not implemented; not advertised. |
| `get_vfj_schema` | Describe writable native glyph data. | Listed | Not supported | Not implemented; not advertised. |
| `edit_glyph_components` | Change component references/transforms. | Listed | Not supported | Not implemented; not advertised. |
| `set_glyph` | Create/replace a whole glyph. | Listed | Not supported | Not implemented; not advertised. |
| `list_kerning_pairs` | List manual kerning pairs. | Listed | Not supported | Not implemented; not advertised. |
| `get_kerning_pair` | Read a kerning pair. | Listed | Not supported | Not implemented; not advertised. |
| `set_kerning_pair` | Set a kerning pair. | Listed | Not supported | Not implemented; not advertised. |
| `delete_kerning_pair` | Remove a kerning pair. | Listed | Not supported | Not implemented; not advertised. |
| `delete_all_kerning_pairs` | Clear kerning pairs. | Listed | Not supported | Not implemented; not advertised. |
| `list_kerning_classes` | List kerning classes. | Listed | Not supported | Not implemented; not advertised. |
| `set_kerning_class` | Create/edit a kerning class. | Listed | Not supported | Not implemented; not advertised. |
| `delete_kerning_class` | Remove a kerning class. | Listed | Not supported | Not implemented; not advertised. |
| `delete_all_kerning_classes` | Clear kerning classes. | Listed | Not supported | Not implemented; not advertised. |
| `rename_kerning_class` | Rename a kerning class. | Listed | Not supported | Not implemented; not advertised. |
| `list_actions` | List available editing actions. | Listed | Not supported | Not implemented; not advertised. |
| `run_actions` | Apply editing actions to glyphs. | Listed | Not supported | Not implemented; not advertised. |
| `set_notepad_content` | Set preview/proof text. | Listed | Not supported | Not implemented; not advertised. |

<!-- END PUBLIC COMPARISON -->

## Agent context and Python API guidance

The server supplies connection instructions, the `fontlab8://guide/agent-workflow` resource, and the `fontlab8-workflow` prompt. Dedicated tool descriptions include API limitations. Prefer get/set tools to arbitrary Python; `fgFont` has no `.fg` attribute and Python errors do not roll back earlier edits. Client support determines whether resources/prompts are loaded automatically. Reconnect the MCP server after updating to refresh connection instructions and tool descriptions.

## Interface provenance and third-party rights

See [interface provenance](docs/PROVENANCE.md). Compatibility names and parameter contracts were informed by FontLab 9 interface research; this is not a clean-room implementation or a redistribution of its backend. Our license covers only rights held by project contributors and does not grant permission to FontLab software, documentation or trademarks.
