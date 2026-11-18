# Installation and troubleshooting

The current installer supports macOS and FontLab 8 only. Install the external dependencies into `.venv` and run `install.py` as your normal user. No administrator privileges or app-bundle patching are needed.

## Installed files

- `~/Library/Application Support/FontLab8MCP/plugin/fontlab8_mcp/`: app-side Python modules.
- `~/Library/Application Support/FontLab8MCP/backups/`: previous startup scripts/plugins and native-save backups.
- `~/Library/Application Support/FontLab/FontLab 8/initScript.py`: one marked startup block, preserving other content.
- `~/Library/Application Support/FontLab/FontLab 8/Scripts/Start Native FontLab 8 MCP.py`: optional manual start script.
- `~/Library/Application Support/FontLab8MCP/{requests,results,ready.json}`: private local request queue and session state.

The helper has no network listener. The private queue is accessible to your local user; the adapter is not a sandbox. A trusted agent can change opened fonts and run Python. Do not point untrusted clients at it.

## Connection checks

Start FontLab, open a font, and call `list_fonts`. `get_active_font` reports the selected document. IDs are valid only in the current process and can change after reopening. Prefer explicit `font_id` for every write. Tool discovery can work while FontLab is closed, but font operations require the app/runtime to be running.

## Common failures

- **No ready session:** launch FontLab or run the manual script once. Check the app's Python output for startup errors.
- **Moved checkout:** recreate `.venv`, reinstall dependencies and update the MCP client's absolute command path.
- **Unknown tool after updating:** reload the client's MCP connection to refresh its tool catalog.
- **Timeout:** a write may already have executed. Inspect its result/font before retrying; the adapter does not replay mutations automatically.
- **Save refusal:** review destination/overwrite/master restrictions in FEATURES.md. Arbitrary native Save As is not supported.
- **Dirty close refusal:** review/save/close the document in FontLab; the helper does not force a discard or click save dialogs.
- **Malformed startup markers:** installer stops before changing the script. Repair only the owned block, preserving other user code and backups.

## Disable

```sh
.venv/bin/python uninstall.py
```

This removes only the owned startup block. Restart FontLab when your documents are safely saved to stop the existing timer. Plugin files and backups are retained for recovery. This does not uninstall or modify FontLab.
