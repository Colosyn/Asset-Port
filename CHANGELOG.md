# Changelog

## [1.0.1] - 2026-06-04
### Added
- UE 5.3 compatibility support (making assets and Python backward-compatible).
- Recreated UAssets (`EUW_AssetPort` and `M_Master`) in UE 5.3.
- Renamed UI option "None" to "Auto-Detect" for clarity.

### Fixed
- Python 3.9 type hints error (replaced `|` with `Optional`).
- Texture naming mismatch where the importer ignored destination names.
- Menu registration warning logs in the console.

## [1.0.0] - 2026-05-30
- Initial release of AssetPort automated import pipeline for Unreal Engine.