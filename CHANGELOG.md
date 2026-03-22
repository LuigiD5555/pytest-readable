# Changelog

## [0.2.0] - 2026-03-21

- Added configurable path resolution for nested repositories.
- Readable output can now resolve display paths from the current working directory, the project root, or an explicit base path.
- Added coverage for path strategy behavior and the new `--path-mode` / `--base-path` options.
- Bumped the package version to `0.2.0`.

## [0.1.0] - 2026-03-09

- Initial public release.
- Human-readable pytest rendering from explicit `@readable(...)` metadata.
- Terminal summaries with readable intention, steps, and pass conditions.
- Markdown and CSV export for documented test suites.
- Helper CLI command: `readable`.
- Non-inferential architecture: render only what the author explicitly declares.
- Built for use outside the original repository as a reusable pytest plugin.
