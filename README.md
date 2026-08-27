# AssetPort

An automated, pipeline-friendly batch importer and organizer for **Unreal Engine 5** using Python and Editor Utility Widgets. Stop importing meshes and textures one-by-one; AssetPort automates category routing, texture settings configuration, material instance generation, and mesh linkage in a single click.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Unreal Engine Version](https://img.shields.io/badge/Unreal%20Engine-5.3%2B%20Supported-blue)](https://www.unrealengine.com/)
[![Language: Python](https://img.shields.io/badge/Language-Python-green)](https://www.python.org/)

---
## Demo

[<img src="https://img.youtube.com/vi/8COCp4ntF4A/maxresdefault.jpg" width="800">](https://youtu.be/8COCp4ntF4A)

## Key Features

* **📦 Smart Batch Importing**: Import meshes FBX and textures (PNG, TGA, EXR, JPG) recursively from any source folder.
* **📂 Automated Organization**: Auto-detects asset category prefixes (e.g. `_env_`, `_wpn_`, `_prop_`) and organizes them into clean, structured subfolders inside Unreal’s Content Browser.
* <img width="800" height="450" alt="Category" src="https://github.com/user-attachments/assets/4a80d53a-06aa-40db-a1c8-cd28c085f62b" />

* **🎨 Automatic Material Instances (MI)**: Automatically generates Material Instances derived from a custom Master Material.
* **🔗 Dynamic Parameter Wiring**: Detects texture suffix tags (e.g. `_N`, `_ORM`, `_Albedo`) and plugs them into the corresponding slot of the Material Instance with the correct **sRGB** and **Compression Settings** (like TC_Normalmap and TC_Masks).
* **⚙️ ORM/Packed Map Switch**: Automatically detects Packed ORM maps and activates the material instance's `"UseORM"` static switch.
* **🟢 Mesh Auto-Link**: Automatically assigns the newly generated Material Instance to Slot 0 of the imported Static/Skeletal Mesh.
* **⚡ Responsive Progress Dialog**: Displays a cancellable progress bar via `unreal.ScopedSlowTask` during saves and material compilation, preventing editor hangs on large batches.
* **👁️ Interactive Preview Mode (Dry Run)**: Run a simulation scan to view the proposed folder routing and clean asset tree in a dedicated EUW window (`EUW_AssetPort_Preview`) before performing an actual import.
* <img width="800" height="450" alt="Preview" src="https://github.com/user-attachments/assets/a8b8d919-ffe7-41f2-bc69-1a868716cd17" />

* **💎 Automated Transparency & Blend Mode Management**: Auto-detects alpha channels in Base Colour textures (PNG, TGA, EXR) and launches an interactive EUW popup (`EUW_TransparencySetup`) for artists to select Blend Modes (`Masked` vs `Translucent`). Automatically assigns `M_Master_Masked` or `M_Master_Translucent` and configures `UseBaseColourAlpha` switches.
* <img width="800" height="450" alt="Transpareny" src="https://github.com/user-attachments/assets/b3f369c4-1f9d-419f-abf4-6c5af34c516a" />

* **🎭 Multi-Material Slot Detection & Subfolder Routing**: Automatically detects assets with multiple material slots (e.g., `T_Chair_Metal_D`, `T_Chair_Wood_D`). Generates per-slot Material Instances (`MI_Chair_Metal`, `MI_Chair_Wood`), links each to its corresponding static mesh slot, and routes assets into `/Materials/` and `/Textures/` subfolders. Single-material assets remain 100% flat!
* <img width="800" height="450" alt="Multi-Material" src="https://github.com/user-attachments/assets/049b1b2d-8775-4feb-8325-50ffa05c4abd" />

* **🧩 UDIM & Virtual Texture Support**: Automatically detects UDIM tile sequences (`_1001` to `_1999`) and 4K Auto-VTs, routes them to dedicated Virtual Texture parameters, and displays tile counts inline in the Preview window (`[UDIM: 6 Tiles]`). 

* **🏺 Atlas & Modular Kit Detection**: Automatically detects kit-based asset groups using hyphen delimiters (e.g. `SM_Rock01-RockKit.fbx`). Unifies all kit meshes under a flat folder (`/Game/Environment/RockKit/`), cleans asset names on import (`SM_Rock01`), shares a single Material Instance (`MI_RockKit`) across all meshes at slot 0, and badges kit summaries in the Preview UI (`[Atlas: X Meshes]`).
* **📐 Static Mesh LOD Import**: Imports LOD groups embedded in one FBX and attaches separately exported `_LOD0`, `_LOD1`, ... FBX files to regular or Atlas Static Meshes.


---

## Installation & Setup

To install AssetPort, place the script files and assets inside your Unreal Engine project's **`Content/Python`** directory.

1. **Clone or Download** this repository.
2. In your Windows File Explorer, navigate to your Unreal project's directory and go to:
   `YourProject/Content/Python/` (Create the `Python` folder if it doesn't exist).
3. **Copy the following folders and files** into `YourProject/Content/Python/`:
   * `asset_port/` (Python core pipeline)
   * `Materials/` (Master Materials: `M_Master_Opaque`, `M_Master_Masked`, `M_Master_Translucent`)
   * `Widgets/` (Editor Utility Widgets & Row Widgets)
   * `importer_config.json`
   * `init_unreal.py`
4. **Start (or restart) Unreal Engine**. The **AssetPort** buttons will automatically load in your Content Browser's main Toolbar and Context Menu.

> [!NOTE]
> Make sure **Python Foundation Scripting** and **Editor Scripting Utilities** plugins are enabled in your Unreal Engine project settings.

---

## How to Use
1. Click the **AssetPort** button on the Content Browser Toolbar, or right-click anywhere in the Content Browser and select **AssetPort**.
2. Click **Browse** and select a folder on your computer containing the meshes and textures you want to import.
3. Select an option from the **Category Dropdown**:
   * **Auto-Detect (Recommended)**: Auto-detects categories based on file prefixes.
   * **Weapons/Environment/Props/Characters/Vehicles/Effects**: Overrides detection and forces all assets into the selected category.
4. **Choose your path**:
   * Click **Preview**: Runs a simulation scan and opens a collapsible tree UI. If it looks correct, click **Confirm Import** at the bottom, or **Cancel** to abort.
   * Click **Import**: Directly runs the import pipeline.
5. When finished, you will find a report (`assetport_report.txt` or `assetport_preview_report.txt`) inside your source folder detailing the scanned, imported, and failed items.

---

## Mappings & Naming Conventions

The importer relies on simple naming tags to automate paths and slots. For a full list of prefix tags (like `sm_`, `sk_`, `t_`) and texture suffixes (like `_BaseColor`, `_N`, `_ORM`), see [CONVENTIONS.md](CONVENTIONS.md).

> [!TIP]
> **Using a Custom Master Material?**
> If you want to use your own Master Material, see the [Custom Master Material Setup Guide in CONVENTIONS.md](CONVENTIONS.md#4-custom-master-material-setup-guide) to ensure your texture parameters and static switches match the expected naming conventions. If any names do not match, they will be ignored without breaking the import pipeline.


---

## Configuration (`importer_config.json`)

You can edit `importer_config.json` inside your project's `Content/Python/` folder to customize default settings:

```json
{
    "master_opaque": "/Game/Python/Materials/M_Master_Opaque",
    "master_masked": "/Game/Python/Materials/M_Master_Masked",
    "master_translucent": "/Game/Python/Materials/M_Master_Translucent",
    "auto_create_mi": true,
    "auto_assign_to_mesh": true,
    "auto_import_lods": true,
    "replace_existing": false,
    "organize_asset": true
}
```

* **`master_opaque` / `master_masked` / `master_translucent`**: Paths to your Master Materials. By default, they point to the included materials under `/Game/Python/Materials/`.
* **`auto_create_mi`**: Automatically generate a Material Instance for textures.
* **`auto_assign_to_mesh`**: Link the created Material Instance to the imported mesh.
* **`auto_import_lods`**: Import embedded FBX LOD groups and attach separate `_LOD#` Static Mesh files.
* **`replace_existing`**: If true, overwrites any existing Material Instances with the same name.

---
## Documentation
* [View Changelog](CHANGELOG.md)

## 🌍 Community Translations

| Language | Maintainer | Repository |
|----------|-----------|------------|
| 🇨🇳 简体中文 (Simplified Chinese) | [@skywa1keri7](https://github.com/skywa1keri7) | [AssetPort-CN](https://github.com/skywa1keri7/AssetPort-CN) |

> [!NOTE]
> AssetPort-CN provides a bilingual (CN/EN) interface while preserving English asset naming conventions. Officially recommended for Chinese-speaking users.

*Community contributions from AssetPort-CN have been merged upstream — see [PR #13](https://github.com/Colosyn/Asset-Port/pull/13).*

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## Roadmap

Feature planning and upcoming development tracked on the [Project Board](https://github.com/Colosyn/Asset-Port/projects).

## Contributing

Have a feature idea or naming convention to propose? Join the conversation in [Discussions](https://github.com/Colosyn/Asset-Port/discussions).
