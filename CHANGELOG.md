# Changelog

All notable changes to GNZ Online Scoring will be documented in this file.

## [0.2.1] - 2026-05-03

### Added
- CONTRIBUTING.md with conventional commits and development guide

### Fixed
- Lint errors (unused imports, bare except handling, f-string fixes)
- pyproject.toml editable install

### Changed
- ruff configuration (per-file ignores for PyInstaller imports)

## [0.2.2] - 2026-05-03

### Fixed
- Remove duplicate run_season call in GUI download (was running twice)

## [Unreleased]

### Added

### Fixed

### Changed

## [0.2.0] - 2026-05-03

### Fixed
- CSV totals now show correctly when pilots have fewer than 5 flights (points padded to 5 columns, total calculated from non-empty values)

### Added
- Flight validity handling (rank field from WeGlide API maps to valid boolean)
- Invalid flight detection and marking in GUI and CSV
- Notes column in CSV showing invalid flight numbers
- --include-invalid flag for CLI to include invalid flights in output
- Yellow row highlighting for pilots with invalid flights in GUI
- ->pts<- markers for invalid flights in GUI

### Changed
- Uses WeGlide API flight "rank" field for validity instead of separate filter parameter

## [0.1.0] - 2026-04-28

### Added
- Initial release
- CLI mode for downloading flights from WeGlide API
- GUI mode for viewing results with maps
- Polygon-based island detection (North/South)
- CSV and JSON output formats
- PyInstaller-based executable build