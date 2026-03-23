# Changelog

## [0.2.2] - 2026-03-23

- The `readable` helper now forwards `--path-mode` and `--base-path` to pytest so nested repositories can be launched from the CLI with the right display-path strategy.
- The CLI help now documents the new path-resolution options and shows an explicit nested-repository example.
- Added coverage for CLI forwarding of `--path-mode` and `--base-path`.

## [0.2.1] - 2026-03-23

- `xfailed` and `xpassed` test outcomes are now tracked and displayed separately in the readable summary.
- The final summary line now shows `xfailed` and `xpassed` counts between `skipped` and `error`, matching pytest's own ordering.
- Terminal color for `xfailed` lines is yellow; `xpassed` lines are green.
- `deselected` items (filtered by `-k` or `-m`) are now counted and shown in the final summary line.
- Warnings emitted during the session are now counted and shown in the final summary line.
- When no tests are collected or all are deselected, the summary shows "no tests ran" instead of an empty result line.
- Added `deselected`, `warnings`, and `no_tests` labels to English and Spanish language packs.

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
