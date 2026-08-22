# Changelog

## [1.5.0] - 2026-08-22
### Added
- **Atlas & Modular Kit Grouping**: Hyphen-delimited kit mesh detection (`SM_Mesh-KitName`) linking multiple static meshes to a single shared PBR texture set.
- **Dedicated Kit Folder Router**: Flat routing for all kit assets into `/Game/{Category}/{KitName}/`.
- **Automated Kit Mesh Renaming**: Automatically strips kit suffixes during Unreal asset creation (e.g., `SM_Rock01-RockKit.fbx` $\rightarrow$ `SM_Rock01`).
- **Shared Atlas Material Instance Generation**: `create_atlas_material_instance` builds and assigns a single shared MI (`MI_{KitName}`) to Slot 0 across all kit static meshes.
- **Atlas Group Validation**: `atlas_group_validator` checks for orphaned kit meshes, missing PBR maps, and single-mesh kits.
- **Preview UI Kit Badges**: Dry Run preview tree displays kit folders with `[Atlas: X Meshes]` badges.
- **Pipeline Statistics Logging**: Tracks `Atlas Groups` found and `Atlas Meshes Imported` in console and summary reports.
### Refactored & Fixed
- **Decoupled 3-Phase Import Architecture**: Separated filesystem discovery, domain grouping, and task generation into clean, independent pipeline phases.
- **Task-Asset Tuple Pairing**: Replaced uncoordinated list indices with direct `(asset, task)` tuple pairing, permanently resolving UDIM and batch import desynchronization.


## [1.4.0] - 2026-07-31
### Added
- **UDIM Streaming Virtual Texture Support**: Automatically detects UDIM tile sequences (`_1001` through `_1999`) and imports them as single Streaming Virtual Textures. Secondary tile tasks are filtered to prevent import collisions.
- **Dynamic VT Parameter Routing**: Automatically detects Virtual Textures (UDIMs or 4K Auto-VTs) in `materials.py` and toggles the `UseVT` static switch to assign textures to `_VT` parameter slots.
- **Inline UDIM Tile Count in Preview Window**: Dry Run simulation preview now displays `[UDIM: X Tiles]` inline with each UDIM texture map.
- **Multi-Engine Version Compatibility**: Verified compatibility across Unreal Engine 5.3, 5.7, and 5.8.
### Refactored & Optimized
- **Shader Permutation Optimization**: Removed 3 redundant static switches (`UV Control Switch`, `HasMetalicTexture`, `IsMetalic`) across all Master Materials (`M_Master_Opaque`, `M_Master_Masked`, `M_Master_Translucent`), reducing active shader permutations while preserving solid-green shader complexity.
- **PBR Default Textures & Strengths**: Updated default VT textures (`T_Default_Black_VT`, `T_Default_White_VT`) and set `HeightStrength` and `EmissiveStrength` defaults to `1.0` for instant out-of-the-box texture assignment.

## [1.3.0] - 2026-07-27

### Added
- **Multi-Material Slot Detection & Regex:** Regex engine detects per-slot material tags (`(?P<material>...)`) for assets with multiple material slots (e.g. `T_Chair_Metal_D`, `T_Chair_Wood_D`).
- **Automated Subfolder Routing:** Multi-material assets automatically place Material Instances in `/Materials/` and textures in `/Textures/` subfolders, while single-material assets remain flat under `/Game/{category}/{base_name}/`.
- **Per-Slot Material Instance Generation:** Generates slot-specific Material Instances (`MI_<MeshName>_<SlotName>`) and links them directly to matching static mesh material slot indices in Unreal Engine.
- **Multi-Slot Transparency Popup Integration:** Transparency scanning (`scan_for_transparency`) inspects each material slot independently, allowing artists to select blend modes per slot.

### Fixed
- **OBJ Importer Safety:** Removed unsupported `.obj` file extension check to prevent `FbxImportUI` runtime exceptions during batch processing.

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