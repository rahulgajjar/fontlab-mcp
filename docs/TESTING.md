# Testing and support status

The source distribution was installed from a fresh `.venv` using the README's commands on macOS with FontLab 8.4.2.8950. FontLab was restarted to load the installed adapter. Its external stdio launcher was registered as `fontlab8-native` in Codex configuration.

The exact registered launcher advertised 35 tools and completed real MCP requests that:

- Listed opened fonts and read 96 Font Info fields.
- Changed designer/manufacturer/version metadata on a disposable font.
- Changed glyph width to 675 and added an anchor at 100,700.
- Saved a native VFC, inspected its VFJ sidecar and reopened a file copy to verify those values.

These requests were driven through the configured server command from a Codex session. An existing conversation may still require its MCP connection/catalog to refresh before exposing tool names directly. Configuration presence alone is not a connection test.

After restarting Codex, all 35 tools appeared directly in the conversation tool catalog. Direct tool calls edited disposable Font Info designer/manufacturer fields, set glyph width to 680 and moved an anchor to 110,710. A native VFC save followed by opening a separately named file copy preserved all three changes. The original user font was left unchanged and restored as active. `close_font` conservatively refused the edited test document because FontLab still reported it as dirty after saving; it did not discard anything. This remains a documented close-operation limitation.

The public pure test suite passed at staging: transport/deadlines, GLIF exchange, detached compilation, stored-table archive integrity, installer/uninstaller preservation, catalog/comparison consistency and publication hygiene. Native smoke tests require the separately licensed app and are opt-in; CI tests do not claim FontLab compatibility on Linux.

FontLab 7 and Windows have not been qualified. Contributions are welcome. Include exact versions and a minimal saved-file reproduction when reporting an issue or submitting a compatibility PR. Do not upload private fonts or raw personal diagnostics.
