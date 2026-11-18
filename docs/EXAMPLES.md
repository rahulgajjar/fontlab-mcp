# MCP workflow examples

These show tool names/arguments, not raw client-specific configuration. Start with `list_fonts` and replace every sample ID with a current result. Read tool descriptions for scoped limits.

## Inspect and patch metadata

```json
{"name":"get_font_info","arguments":{"font_id":123}}
```

```json
{"name":"set_glyph_info","arguments":{"font_id":123,"edits":[{"glyph_name":"A","note":"Reviewed","mark":3,"unicodes":[65]},{"glyph_name":"V","note":"Check spacing"}]}}
```

```json
{"name":"set_glyph_metrics","arguments":{"font_id":123,"glyph_name":"A","lsb":70,"rsb":80}}
```

## Exchange every existing point in a layer

```json
{"name":"get_glyph_source","arguments":{"font_id":123,"glyph_name":"A","layer_name":"Regular","format":"glif"}}
```

Keep the returned revision. Edit the returned XML point coordinates, width or anchors and pass it to `set_glyph_source` using `format:glif`, `xml`, that revision and the same font/glyph/layer. Use `dry_run:true` first. Preserve identifiers, topology and point types. Alternatively edit the returned `source` JSON and pass it as `source` with `format:json`. Do not pass the whole response wrapper as the source object.

## Feature files and classes

Read `get_features`, retaining the revision. `get_features` can write panel source using `format:fea,output_path:"/absolute/features.fea"`. After editing that file, `set_features` accepts `version:1`, the current revision, `format:fea,data_path:"/absolute/features.fea"`. Native classes may be separate from file source; `get_classes` / `set_classes` expose their membership.

Use `compile_features` with the new source revision and `dry_run:true`, then publish explicitly. Additional name/BASE/variable context is not supported by this compiler path; see FEATURES.md. Save natively to retain the helper-managed compiled archive.

## Save and export

```json
{"name":"save_font","arguments":{"font_id":123,"path":"/absolute/current-document.vfc","format":"vfc","overwrite":true}}
```

This example requires that exact existing native document path. First-save basename restrictions differ; arbitrary Save As is refused.

```json
{"name":"export_font","arguments":{"font_id":123,"format":"designspace","directory":"/absolute/new-export-directory"}}
```

The directory must not already exist. Supported profile names are `glyphs`, `glyphspackage`, `designspace`, `ufo`, `ttf` and `otf`. Validate resulting files for your workflow; interchange is not lossless native storage.
