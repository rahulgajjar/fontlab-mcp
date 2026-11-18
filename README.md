# FontLab 8 MCP

Control an opened FontLab 8 font from an MCP-capable agent: inspect and edit Font Info, glyph metadata, contours, anchors, spacing, masters, axes, instances, features and OpenType classes, then save or export through FontLab.

**Tested on macOS with FontLab 8.4.2.8950.** The app's embedded Python 3.11 and PythonQt run native operations on its main thread. The external helper was tested with Python 3.14; Python 3.11+ is required. Windows and FontLab 7 are not currently supported or verified.

This is an independent compatibility adapter, not an official FontLab product and not FontLab 9's binary backend. You need your own licensed FontLab installation. The app bundle is not modified.

## Install

1. Download or clone this repository, then open a terminal in its directory.
2. Create an isolated environment and install dependencies:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python install.py
   ```

3. Save your documents and restart FontLab 8. Alternatively, refresh Scripts and run **Start Native FontLab 8 MCP** for first-time loading. Avoid starting multiple runtime copies in one session.
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

## Compatibility with FontLab 9 MCP

The comparison below lists all 56 reference names and the additional tools. “Available, scoped” does not mean every option or identical output is supported. Unavailable names are not advertised by the server.

<!-- BEGIN PUBLIC COMPARISON -->

**26/56 reference names available with scoped coverage + 9 additional tools = 35 advertised calls.**

| Tool | Origin | Purpose | Availability | Scope / limit |
|---|---|---|---|---|
| `get_preferences` | FontLab 9 name | Read application preferences. | Not available | Not implemented; not advertised. |
| `set_preferences` | FontLab 9 name | Change application preferences. | Not available | Not implemented; not advertised. |
| `list_aidus_files` | FontLab 9 name | List assistant workspace files. | Not available | Not implemented; not advertised. |
| `read_aidus_file` | FontLab 9 name | Read an assistant workspace file. | Not available | Not implemented; not advertised. |
| `write_aidus_file` | FontLab 9 name | Write an assistant workspace file. | Not available | Not implemented; not advertised. |
| `new_font` | FontLab 9 name | Create a font. | Available, scoped | Only the default Latin Simple repertoire is qualified. |
| `open_font` | FontLab 9 name | Open a font file. | Available, scoped | Basic native operation. |
| `save_font` | FontLab 9 name | Save the opened font. | Available, scoped | Native in-place VFC/VFJ save with retained backups; existing files require overwrite=true. First native save requires original basename.vfc and creates a VFJ sidecar. Native Save As to another path is refused. UFO remains a limited single-master snapshot. |
| `close_font` | FontLab 9 name | Close a font document. | Available, scoped | Clean fonts only. Dirty fonts and save=true are refused without opening a dialog. No forced discard. |
| `list_fonts` | FontLab 9 name | List opened fonts. | Available, scoped | Basic native operation. |
| `get_active_font` | FontLab 9 name | Identify the active font. | Available, scoped | Basic native operation. |
| `set_active_font` | FontLab 9 name | Choose the active font. | Available, scoped | Basic native operation. |
| `get_features` | FontLab 9 name | Read feature source and revision. | Available, scoped | Native source, shared FontGate classes and glyph order with revision. Not native compiled lookup access. |
| `set_features` | FontLab 9 name | Replace feature source with validation. | Available, scoped | Source replacement with FontTools validation, revision/dry-run and 1 MiB limit; include() refused. Raw layout bytes preserved. Native Undo and visual Lookup state not qualified. |
| `compile_features` | FontLab 9 name | Compile and publish layout tables. | Available, scoped | FontTools feaLib detached compilation via MCP stdio, then raw GSUB/GPOS/GDEF publication with compensation and native package-library archive for persistence. 1 MiB compiled/8 MiB archive limits; additional generated tables refused. Native Undo, visual lookup behavior and fontpr compilation are not qualified. |
| `get_opentype_tables` | FontLab 9 name | Inspect/export stored OpenType bytes. | Available, scoped | Reads native runtime table bytes; helper-managed archives rehydrate after native save/reopen. Not fresh export/compilation. Inline data limited to 512 KiB; larger data requires file export. |
| `get_lookups` | FontLab 9 name | Read visual lookup definitions. | Not available | Not implemented; not advertised. |
| `set_lookups` | FontLab 9 name | Change visual lookup definitions. | Not available | Not implemented; not advertised. |
| `get_font_info` | FontLab 9 name | Read font metadata. | Available, scoped | Returns 96 native FontInfo fields, not full VFJ package JSON; detail=full only. Master selection is supported. |
| `get_font_hinting` | FontLab 9 name | Read master zones and standard stems. | Available, scoped | Reads native PS/TT/family zones and PS/TT stems, per master with pagination. No automatic hinting. |
| `set_font_info` | FontLab 9 name | Bulk-edit font metadata. | Available, scoped | Native FontInfo field patches and masters[] are supported. scale_upm=true, axes/instances and arbitrary VFJ replacement are not qualified. |
| `list_glyphs` | FontLab 9 name | List/filter glyph names and Unicode values. | Available, scoped | Names/unicodes and query/has_unicode pagination only; facts/geometry filters are not ported. |
| `get_current_glyphs` | FontLab 9 name | Read current/selected glyphs. | Not available | Not implemented; not advertised. |
| `get_active_glyphs` | FontLab 9 name | Read current glyphs (alias). | Not available | Not implemented; not advertised. |
| `explain` | FontLab 9 name | Explain native object properties. | Not available | Not implemented; not advertised. |
| `set_active_glyph` | FontLab 9 name | Choose the current glyph. | Not available | Not implemented; not advertised. |
| `get_glyph` | FontLab 9 name | Read glyph construction/data. | Available, scoped | detail=construction only: layer flags and anchors; full VFJ/component detail and attachment analysis not ported. |
| `build_glyph` | FontLab 9 name | Construct a glyph from a recipe. | Not available | Not implemented; not advertised. |
| `set_glyph_anchors` | FontLab 9 name | Add/edit/remove anchors. | Available, scoped | Native position/name/remove/expression/cloud fields; mark_enabled and native undo not qualified. |
| `get_layer_hints` | FontLab 9 name | Read stored glyph-layer hints. | Available, scoped | Reads native stored PS hint position/width/orientation/name and TTH count. Ghost, lock/link decoding and include_tth command strings are not qualified; no hint detection. |
| `edit_layer_hints` | FontLab 9 name | Edit glyph-layer PostScript hints. | Not available | Not implemented; not advertised. |
| `get_glyph_nodes` | FontLab 9 name | Read indexed contour points. | Available, scoped | Indexed local nodes and transforms; extrema computation not ported. |
| `edit_glyph_nodes` | FontLab 9 name | Edit indexed contour points. | Available, scoped | Coordinate set/move only; preflight/dry-run supported, native undo not qualified. Components and Auto layers refused. |
| `geometry` | FontLab 9 name | Calculate vector/Bezier geometry. | Not available | Not implemented; not advertised. |
| `get_vfj_schema` | FontLab 9 name | Describe writable native glyph data. | Not available | Not implemented; not advertised. |
| `edit_glyph_components` | FontLab 9 name | Change component references/transforms. | Not available | Not implemented; not advertised. |
| `set_glyph` | FontLab 9 name | Create/replace a whole glyph. | Not available | Not implemented; not advertised. |
| `get_font_metrics` | FontLab 9 name | Read font metrics. | Available, scoped | Basic native operation. |
| `set_font_metrics` | FontLab 9 name | Change font metrics. | Available, scoped | Basic native operation. |
| `get_glyph_metrics` | FontLab 9 name | Read width and sidebearings. | Available, scoped | Numeric width/LSB/RSB and current expression strings; empty glyph sidebearings are null. |
| `set_glyph_metrics` | FontLab 9 name | Change numeric width and sidebearings. | Available, scoped | Manual numeric width/LSB/RSB. LSB shifts ink and advance together to retain RSB; explicit width/RSB conflicts rejected. Bound expressions and Auto layers refused. |
| `list_kerning_pairs` | FontLab 9 name | List manual kerning pairs. | Not available | Not implemented; not advertised. |
| `get_kerning_pair` | FontLab 9 name | Read a kerning pair. | Not available | Not implemented; not advertised. |
| `set_kerning_pair` | FontLab 9 name | Set a kerning pair. | Not available | Not implemented; not advertised. |
| `delete_kerning_pair` | FontLab 9 name | Remove a kerning pair. | Not available | Not implemented; not advertised. |
| `delete_all_kerning_pairs` | FontLab 9 name | Clear kerning pairs. | Not available | Not implemented; not advertised. |
| `list_kerning_classes` | FontLab 9 name | List kerning classes. | Not available | Not implemented; not advertised. |
| `set_kerning_class` | FontLab 9 name | Create/edit a kerning class. | Not available | Not implemented; not advertised. |
| `delete_kerning_class` | FontLab 9 name | Remove a kerning class. | Not available | Not implemented; not advertised. |
| `delete_all_kerning_classes` | FontLab 9 name | Clear kerning classes. | Not available | Not implemented; not advertised. |
| `rename_kerning_class` | FontLab 9 name | Rename a kerning class. | Not available | Not implemented; not advertised. |
| `list_actions` | FontLab 9 name | List available editing actions. | Not available | Not implemented; not advertised. |
| `run_actions` | FontLab 9 name | Apply editing actions to glyphs. | Not available | Not implemented; not advertised. |
| `set_notepad_content` | FontLab 9 name | Set preview/proof text. | Not available | Not implemented; not advertised. |
| `run_python` | FontLab 9 name | Execute Python inside FontLab. | Available, scoped | Persistent agent namespace inside FontLab 8; not the Scripting panel namespace. fontpr/mcp_tools expose only this ported subset. |
| `get_python_output` | FontLab 9 name | Read captured Python output. | Available, scoped | Only output captured from this adapter’s most recent run_python call, not the entire FontLab Output panel. |
| `export_font` | Additional tool | Export through native font profiles. | Available, scoped | FontLab 8 extension (not one of the native 9 catalog's 56 names): export using a native profile to a new directory. Interchange may omit FontLab-only data. |
| `get_glyph_info` | Additional tool | Read name, Unicode, spacing and glyph metadata. | Available, scoped | read notes, color marks, tags and Unicode scalars for named glyphs. |
| `set_glyph_info` | Additional tool | Bulk-edit names, Unicode, notes, marks and tags. | Available, scoped | preflight and apply bulk glyph metadata patches; native undo not qualified. Supports explicit new_name; does not rewrite feature/class text references or replace outlines. |
| `get_glyph_source` | Additional tool | Read all layer points/anchors as JSON or GLIF. | Available, scoped | Read all existing layer points/anchors/width as native JSON or GLIF XML. Not a full FontLab document serializer. |
| `set_glyph_source` | Additional tool | Write point/anchor coordinates while preserving topology. | Available, scoped | Write layer coordinates, width and anchors from JSON or GLIF; revision required. Existing shape/contour/node topology, types and smooth flags must remain unchanged; no native undo. |
| `get_font_structure` | Additional tool | Read axes, master locations and instances. | Available, scoped | Read native axes, master locations and instance metadata with revision. Locations enumerate known axis short names only. |
| `set_font_structure` | Additional tool | Change axes, locations and instance metadata. | Available, scoped | Patch/add axes and master locations; instances[] replaces the instance list. Revision/preflight/dry-run; native undo and rollback of axis insertion are not qualified. |
| `get_classes` | Additional tool | Read native OpenType class membership. | Available, scoped | Read native OpenType class memberships plus native panel summary; kerning class editing is excluded. |
| `set_classes` | Additional tool | Create/edit/remove OpenType class membership. | Available, scoped | Patch/create/remove OpenType class memberships by name, with revision and dry-run. No native undo; nonzero class marks and kerning groups are refused. |

<!-- END PUBLIC COMPARISON -->

## Agent context and Python API guidance

The server supplies connection instructions, the `fontlab8://guide/agent-workflow` resource, and the `fontlab8-workflow` prompt. Dedicated tool descriptions include API limitations. Prefer get/set tools to arbitrary Python; `fgFont` has no `.fg` attribute and Python errors do not roll back earlier edits. Client support determines whether resources/prompts are loaded automatically. Reconnect the MCP server after updating to refresh connection instructions and tool descriptions.
