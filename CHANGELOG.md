# Changelog

## [1.2.0] - 2026-07-21

### Added
- **New Master Materials:** Created dedicated Master Materials (`M_Master_Opaque`, `M_Master_Masked`, `M_Master_Translucent`) supporting full PBR shading and forward shading translucency.
- **Automatic Transparency Detection:** PNG, TGA, and EXR base colour textures with embedded alpha channels are now automatically detected at import time via binary header inspection.
- **Interactive Transparency EUW Setup:** Spawns a compact 2-column Editor Utility Widget popup (`EUW_TransparencySetup`) allowing artists to review and select Blend Modes (`Masked`, `Translucent`, `Opaque`) before materials are created.
- **Dynamic Parent Material Assignment:** Material Instances automatically inherit from appropriate Master Materials (`M_Master_Opaque`, `M_Master_Masked`, `M_Master_Translucent`) based on chosen blend modes.
- **Static Switch Parameter Wiring:** Automatically toggles `UseBaseColourAlpha` or `UseOpacityMap` parameters on generated Material Instances.
- **Zero-Dependency Binary Header Inspection:** Fast header inspection for PNG, TGA, EXR, and JPEG texture format validation.

## [1.1.0] - 2026-06-16
### Added
- Added "Preview Mode" (Dry Run) button to the main importer panel.
- Interactive, collapsible preview window (`EUW_AssetPort_Preview`) showing the proposed folder structure and clean asset tree (e.g., `SM_Door`, `T_Door_N`).
- Direct **Confirm Import** and **Cancel** buttons within the preview window for an optimized workflow.
- Native warning dialog window if a user attempts to run a preview without selecting a folder.
- Auto-generation of a simulation report (`assetport_preview_report.txt`) saved to the source folder during dry runs.

## [1.0.2] - 2026-06-08
### Added
- Added naming conventions guide for custom Master Materials.
- Added tip in the main README referencing the custom Master Material setup.
- Suffix support for displacement maps (`_disp` and `_displacement`).

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