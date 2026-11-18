# Contributing

Contributions are welcome through this repository's Pull requests and Issues tabs. Please discuss large behavior changes in an issue first. Small fixes, documentation improvements and reproducible bug reports are valuable too.

By submitting code you confirm you have the right to contribute it and make it available under [LICENSE](LICENSE). You retain your copyright; no copyright assignment is required. Do not submit FontLab binaries, decompiled/proprietary source, license material, private fonts or code copied from incompatible third-party projects.

## Development

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests -q
```

Pure tests do not require FontLab. To run the optional integration smoke test on the tested Mac setup, start FontLab with the adapter installed, then run:

```sh
.venv/bin/python scripts/smoke_test.py --live
```

It creates disposable fonts and native files in ignored `local-test-output`, restores the prior active font when possible, and leaves test documents open for review. Do not use production fonts for integration tests. Routine verification should use MCP and saved files, not screen automation.

For a new editing capability, add negative-input/preflight checks, preserved-data assertions, native save/reopen checks and suitable unit/integration coverage. Validate exports with mature font libraries and shaping with HarfBuzz where relevant. A successful in-memory getter or a tool count is not proof of full feature support.

Update README's comparison, `comparison.json`, tool schemas and feature limits together. Run `scripts/update_comparison.py` after editing comparison data. Unimplemented names must not appear in the advertised tool list.

## FontLab 7 and other platforms

FontLab 7 contributions are welcome, but it is currently untested and unsupported. Establish its embedded Python/Qt ABI, user-profile paths, startup hook and native APIs before adding a compatibility flag. Use owned glyph/package objects; some native property getters are unsafe on detached objects. Keep behavior differences explicit, and verify nonempty fixtures and native roundtrips.

Windows support also needs a real installer/runtime transport qualification, not only path substitutions. Please state exact OS, FontLab build and Python versions in your PR.

## Good issue reports

Include:

- OS version/architecture, FontLab version/build, external and embedded Python versions if known.
- The exact tool call and whether FontLab was open with a font loaded.
- Expected and actual behavior, complete error text and reproducible steps.
- A minimal synthetic fixture/reproduction script, if you can share it legally.
- Save/export format, master/layer and whether the failure occurs after reopening.

Redact private paths, font contents and credentials. For a crash or timeout, do not repeatedly replay a write; preserve autosaves and describe whether recovery was needed. Report security-sensitive details privately through GitHub's private vulnerability reporting if enabled; otherwise open an issue requesting a private contact without posting the sensitive details.
