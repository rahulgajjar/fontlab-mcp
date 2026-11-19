# Releasing

`v0.4.1` is the first public tag and is designated a GitHub prerelease. The MCP server reports `0.4.1` during initialization. The GitHub prerelease flag communicates the status of this release.

Use Semantic Versioning for the adapter's public MCP interface. Increment the patch for compatible fixes, the minor for compatible additions and the major for breaking changes once the API reaches 1.0. During the 0.x series, document breaking changes explicitly and increment the minor version when introducing them. Prefix release tags with `v`.

1. Set `__version__` in `fontlab8_mcp/__init__.py`. The MCP server uses that value directly.
2. Add a matching entry to [the changelog](../CHANGELOG.md) with changes, tested platforms and relevant limits.
3. Run `python -m pytest tests/test_version.py` in the development environment and run targeted tests for the changes. Check the test and support notes before describing runtime qualification.
4. After the release commit is ready, use its matching version tag for the GitHub release. Copy the corresponding changelog entry into the release notes and select **This is a pre-release** for `v0.4.1`.
