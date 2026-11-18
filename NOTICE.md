# Notices

This is an independent adapter. FontLab is a trademark/product of its respective owner. This project is not affiliated with, endorsed by or sponsored by FontLab. It does not provide a FontLab license or distribute the application.

Project-owned code and documentation use LICENSE. The runtime API catalog contains only the functional compatibility interfaces needed by implemented tools and project-authored descriptions. The 56-name comparison describes compatibility; it is not a claim of complete parity. No FontLab executable, proprietary source, decompiled listing, test font or raw diagnostic is included.

Dependencies are installed separately, not relicensed by this project:

- **FontTools:** MIT license; OpenType/UFO validation and feature compilation.
- **jsonschema:** MIT license; MCP input validation. Its transitive dependencies retain their own licenses.
- **pytest** (development): MIT license.
- FontLab's embedded Python/PythonQt and native APIs are supplied by the user's installation under their respective terms; they are not bundled here.

Preserve dependency notices when redistributing dependency code or binaries. No FontTools, TypeRig, third-party MCP server or FontLab source tree is vendored in this repository. API behavior from other versions/platforms requires independent qualification.
