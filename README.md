# AssetPort

An automated, pipeline-friendly batch importer and organizer for **Unreal Engine 5** using Python and Editor Utility Widgets. Stop importing meshes and textures one-by-one; AssetPort automates category routing, texture settings configuration, material instance generation, and mesh linkage in a single click.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Unreal Engine Version](https://img.shields.io/badge/Unreal%20Engine-5.3%2B%20Supported-blue)](https://www.unrealengine.com/)
[![Language: Python](https://img.shields.io/badge/Language-Python-green)](https://www.python.org/)

---
## Demo

[<img src="https://img.youtube.com/vi/Cm26pc_Ob-U/maxresdefault.jpg" width="800">](https://youtu.be/Cm26pc_Ob-U)

## Key Features

* **📦 Smart Batch Importing**: Import meshes FBX and textures (PNG, TGA, EXR, JPG) recursively from any source folder.
* **📂 Automated Organization**: Auto-detects asset category prefixes (e.g. `_env_`, `_wpn_`, `_prop_`) and organizes them into clean, structured subfolders inside Unreal’s Content Browser.
* **🎨 Automatic Material Instances (MI)**: Automatically generates Material Instances derived from a custom Master Material.
* **🔗 Dynamic Parameter Wiring**: Detects texture suffix tags (e.g. `_N`, `_ORM`, `_Albedo`) and plugs them into the corresponding slot of the Material Instance with the correct **sRGB** and **Compression Settings** (like TC_Normalmap and TC_Masks).
* **⚙️ ORM/Packed Map Switch**: Automatically detects Packed ORM maps and activates the material instance's `"UseORM"` static switch.
* **🟢 Mesh Auto-Link**: Automatically assigns the newly generated Material Instance to Slot 0 of the imported Static/Skeletal Mesh.
* **⚡ Responsive Progress Dialog**: Displays a cancellable progress bar via `unreal.ScopedSlowTask` during saves and material compilation, preventing editor hangs on large batches.

---

## Installation & Setup

To install AssetPort, place the script files and assets inside your Unreal Engine project's **`Content/Python`** directory.

1. **Clone or Download** this repository.
2. In your Windows File Explorer, navigate to your Unreal project's directory and go to:
   `YourProject/Content/Python/` (Create the `Python` folder if it doesn't exist).
3. **Copy the following files** into `YourProject/Content/Python/`:
   * The `asset_port/` directory
   * `EUW_AssetPort.uasset`
   * `M_Master.uasset`
   * `init_unreal.py`
   * `importer_config.json`
4. **Start (or restart) Unreal Engine**. The **AssetPort** buttons will automatically load in your Content Browser's main Toolbar and Context Menu.

> [!NOTE]
> Make sure **Python Foundation Scripting** and **Editor Scripting Utilities** plugins are enabled in your Unreal Engine project settings.

---

## How to Use

1. Click the **AssetPort** button on the Content Browser Toolbar, or right-click anywhere in the Content Browser and select **AssetPort**.
2. Click **Browse** and select a folder on your computer containing the meshes and textures you want to import.
3. Select an option from the **Category Dropdown**:
   * **None (Recommended)**: Auto-detects categories based on file prefixes.
   * **Weapon/Environment/Props/Character**: Overrides the detection and forces all assets into the selected category directory.
4. Click **Import**.
5. When finished, you will find an `assetport_report.txt` report inside your source folder detailing the scanned, imported, and failed items.

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
    "parent_material": "/Game/Python/M_Master",
    "auto_create_mi": true,
    "auto_assign_to_mesh": true,
    "replace_existing": false,
    "organize_asset": true
}
```

* **`parent_material`**: The path to your Master Material. By default, it points to the included `M_Master`. If you move `M_Master` or want to use your own material, change this path.
* **`auto_create_mi`**: Automatically generate a Material Instance for textures.
* **`auto_assign_to_mesh`**: Link the created Material Instance to the imported mesh.
* **`replace_existing`**: If true, overwrites any existing Material Instances with the same name.

---
## Documentation
* [View Changelog](CHANGELOG.md)

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## Roadmap

Feature planning and upcoming development tracked on the [Project Board](https://github.com/Colosyn/Asset-Port/projects).

## Contributing

Have a feature idea or naming convention to propose? Join the conversation in [Discussions](https://github.com/Colosyn/Asset-Port/discussions).
