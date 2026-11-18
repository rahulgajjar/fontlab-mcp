# Interface provenance and rights boundaries

This independent adapter implements operations through a user's installed FontLab
8 Python APIs and project-owned MCP transport. It does not distribute the FontLab
application or its MCP backend. This statement is not a certification of every
line's authorship or of legal permission for the preceding research.

## What informed the interfaces

- The 26 compatibility entries in tool-catalog.json retain functional names and
  parameter schemas derived from a FontLab 9 interface reference. Descriptions
  were written for this project. They must not be represented as independently
  designed or clean-room interfaces.
- comparison.json contains compatibility names, project-authored purposes and
  scoped implementation status, including tools not offered by this adapter.
- Additional tools and adapter behavior are project implementations, informed
  by FontLab 8 API experiments and saved-file verification. Describing them this
  way does not constitute a historical, line-by-line copyright audit.
- FontTools and jsonschema are separately licensed dependencies; FontLab's
  embedded modules come from the user's installation. See NOTICE.md.

## Unresolved permissions

The project's license covers only rights contributors hold. It does not establish
permission to extract or redistribute vendor interfaces or override a FontLab EULA.
The actual accepted FontLab agreements and any applicable mandatory-law exceptions
require separate review. No vendor permission or legal clearance is claimed.
Existing development used interface/reverse-engineering research; it must not be
relabeled as clean-room by rewriting descriptions or renaming files.

## Future contributions

Use original code and minimal interface definitions needed for implemented
operations. Record whether each change comes from public documentation, observed
behavior, a licensed source, or independently designed behavior. Link public
documentation rather than copying manuals. Do not submit vendor binaries,
decompiled code, extracted descriptions, unlicensed examples, private fonts or
credentials. Obtain appropriate permission before incorporating third-party code.
