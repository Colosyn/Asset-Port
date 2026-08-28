# Naming Conventions

AssetPort parses filenames using a regex-based parser. To ensure that your meshes and textures are imported, categorized, and connected correctly, name your files using the following convention structure:

### Single-Material Assets:
```text
[Prefix]_[Category]_[BaseName]_[Suffix].[extension]
```
*Example:* `SM_env_WallStone.fbx` or `T_env_WallStone_N.png`

### Multi-Material Assets:
```text
[Prefix]_[Category]_[BaseName]_[MaterialSlotName]_[Suffix].[extension]
```
*Example:* `T_env_Chair_Metal_D.png` or `T_env_Chair_Wood_N.png`

### UDIM Texture Sets:
```text
[Prefix]_[Category]_[BaseName]_[Suffix]_[TileID].[extension]
```
*Example*: `T_env_Door_N_1001.png`, `T_env_Door_N_1002.png`

### Atlas / Modular Kit Assets:
```text
Mesh:    [Prefix]_[Category]_[IndividualName]-[KitName].[extension]
Texture: [Prefix]_[Category]_[KitName]_[Suffix].[extension]
```
*Example*: `SM_env_Rock01-RockKit.fbx`, `SM_env_Rock02-RockKit.fbx`, `T_env_RockKit_D.png`, `T_env_RockKit_ORM.png`

### Separate Static Mesh LODs:
```text
[StaticMeshName]_LOD0.fbx
[StaticMeshName]_LOD1.fbx
[StaticMeshName]_LOD2.fbx
```
*Example*: `SM_env_Rock_LOD0.fbx`, `SM_env_Rock_LOD1.fbx`. An unsuffixed base mesh such as `SM_env_Rock.fbx` can also be paired with `_LOD1` and later files. Atlas LODs place the marker after the kit name, for example `SM_env_Rock01-RockKit_LOD1.fbx`.
---


## 1. Prefixes (Asset Type)

Prefixes tell the tool what type of asset is being imported. This is case-insensitive.

| Prefix | Asset Type | Destination Unreal Class |
| :--- | :--- | :--- |
| `sm_` | Static Mesh | `unreal.StaticMesh` |
| `sk_`, `skm_` | Skeletal Mesh | `unreal.SkeletalMesh` |
| `t_` | Texture | `unreal.Texture2D` |
| `a_`, `anim_` | Animation | `unreal.AnimSequence` |

*If no prefix is found, supported image extensions are inferred as textures and
`.fbx` files are inferred as static meshes. Explicit prefixes still take
priority and should be used for skeletal meshes and animations.*

---

## 2. Categories (Automatic Folder Routing)

Categories determine the subfolder under `/Game/` where the assets will be stored. This is case-insensitive.

| Tag | Category | Destination Content Browser Path |
| :--- | :--- | :--- |
| `env_` | Environment | `/Game/Environment/[BaseName]/` |
| `wpn_` | Weapons | `/Game/Weapons/[BaseName]/` |
| `prop_` | Props | `/Game/Props/[BaseName]/` |
| `char_` | Characters | `/Game/Characters/[BaseName]/` |
| `veh_` | Vehicles | `/Game/Vehicles/[BaseName]/` |
| `fx_` | Effects | `/Game/Effects/[BaseName]/` |

* **Category Inheritance:** In asset groups (including UDIM sequences) or modular kits, tagging just ONE file with a category prefix (e.g., `SM_env_Chest.fbx` or `T_prop_RockKit_D.png`) automatically propagates that category to all other meshes and textures in the group.
* **Dropdown Override:** You can override this auto-sorting in the tool UI by selecting an explicit category.
* **Unsorted Fallback:** If no tag is matched and no override is selected, assets are routed to `/Game/_Unsorted/[BaseName]/`.

---

## 3. Texture Suffixes (Material Slots & Settings)

Suffixes determine how textures are mapped inside the created **Material Instance** parameters, and automatically sets their Unreal Engine texture compression and sRGB flags.

| Suffix | Texture Slot / Parameter | sRGB | Compression Setting |
| :--- | :--- | :--- | :--- |
| `_b`, `_basecolour`, `_d`, `_diffuse`, `_albedo`, `_basecolor`, `_alb` | **BaseColour** | `True` | `TC_Default` |
| `_n`, `_nrm`, `_normal` | **Normal** | `False` | `TC_Normalmap` |
| `_r`, `_roughness`, `_rough` | **Roughness** | `False` | `TC_Masks` |
| `_m`, `_metal`, `_metallic` | **Metallic** | `False` | `TC_Masks` |
| `_metalness` | **Metallic** | `False` | `TC_Masks` |
| `_ao`, `_ambientocclusion` | **AmbientOcclusion** (AO) | `False` | `TC_Masks` |
| `_cavity` | **Cavity** | `False` | `TC_Masks` |
| `_e`, `_emissive` | **Emissive** | `True` | `TC_Default` |
| `_o`, `_opacity` | **Opacity** | `False` | `TC_Alpha` |
| `_mask`, `_opacitymask` | **Opacity Mask** | `False` | `TC_Masks` |
| `_specular`, `_gloss` | **Specular / Gloss** | `False` | `TC_Masks` |
| `_translucency` | **Translucency** | `True` | `TC_Default` |
| `_h`, `_height`, `_disp`, `_displacement`, `_bump`  | **Height** | `False` | `TC_Masks` |
| `_orm`, `_arm` | **ORM** (Occlusion, Roughness, Metallic) | `False` | `TC_Masks` |
| `_rma` | **RMA** (Roughness, Metallic, Ambient Occlusion) | `False` | `TC_Masks` |

Resolution tokens such as `_2K_` and `_4K_` are treated as metadata rather
than material-slot names when they appear before a recognized texture suffix.

### Special Material Features:
* **ORM Textures:** If an `_orm` texture suffix is detected, the tool automatically turns on the static switch parameter **"UseORM"** in the material instance, allowing you to feed packed maps directly.

---

## 4. Multi-Material Asset Behavior

When `AssetPort` detects a `[MaterialSlotName]` tag in texture filenames (e.g. `Metal` or `Wood` in `T_Chair_Metal_D`):

1. **Per-Slot Material Instances**: Generates individual Material Instances for each slot (`MI_Chair_Metal`, `MI_Chair_Wood`).
2. **Mesh Slot Linkage**: Automatically assigns each Material Instance to the matching material slot name on the `StaticMesh`.
3. **Automated Subfolder Routing**:
   * **Single-Material Assets**: Placed 100% flat inside `/Game/[Category]/[BaseName]/`.
   * **Multi-Material Assets**: Material Instances are routed to `/Game/[Category]/[BaseName]/Materials/` and textures to `/Game/[Category]/[BaseName]/Textures/`.

## 5. Custom Master Material Setup Guide

If you configure a custom Master Material in `importer_config.json` via the `"parent_material"` property, your master material must use specific parameter names for AssetPort to correctly bind the scanned textures.

### Required Texture Parameter Names

Ensure your Master Material defines texture parameters matching these exact names (case-sensitive):

| Texture Slot | Required Parameter Name | Description |
| :--- | :--- | :--- |
| Base Colour | `BaseColour` | The diffuse / albedo input |
| Normal | `Normal` | The normal map input |
| Roughness | `Roughness` | The roughness map input |
| Metallic | `Metallic` | The metallic map input |
| Ambient Occlusion | `AmbientOcclusion` | The AO map input |
| Cavity | `Cavity` | The cavity map input |
| Emissive | `Emissive` | The emissive map input |
| Specular | `Specular` | The specular map input |
| Gloss | `Gloss` | The gloss map input |
| Translucency | `Translucency` | The translucency map input |
| Opacity | `Opacity` | The opacity / transparency input |
| Height | `Height` | The height / displacement input |
| ORM | `ORM` | The occlusion, roughness, and metallic packed input |
| RMA | `RMA` | The roughness, metallic, and ambient-occlusion packed input |

### Static Switches

* **`UseORM`**: Automatically set to `True` when an `_orm` texture is detected.
* **`UseBaseColourAlpha`**: Automatically set to `True` when a Base Colour texture with an embedded alpha channel is detected and the material blend mode is set to `Masked` or `Translucent`.
* **`UseVT`**: Automatically set to `True` when UDIM tile sequences (`_1001` to `_1999`) or Virtual Textures are detected, binding to parameters named `[ParamName]_VT` (e.g. `BaseColour_VT`, `Normal_VT`, `ORM_VT`).

### Unmatched Suffixes and Parameters

If a texture's suffix doesn't match any known slots, or if a slot is not found on your custom Master Material:
* **Safe Fallback:** The assignment will be silently ignored.
* **Pipeline Continues:** It will not raise an error or crash the import process. The mesh will still be imported, the material instance will be created, other matching parameters will be connected, and the material will be assigned to the mesh successfully.

## 6. Atlas & Modular Kit Behavior
AssetPort supports texture atlas workflows where multiple static meshes share a single texture set and Material Instance:
1. **Hyphen Delimiter (`-`)**: The hyphen is **reserved exclusively** for Atlas / Kit meshes to separate the individual mesh name from its shared kit name (`SM_PropName-KitName.fbx`).
2. **Automated Clean Naming**: When imported into Unreal Engine, kit meshes are automatically cleaned and renamed without the kit suffix (e.g. `SM_Rock01-RockKit.fbx` $\rightarrow$ `SM_Rock01`).
3. **Shared Material Instance**: A single Material Instance (`MI_[KitName]`) is generated and linked to Slot 0 across all meshes in the kit.
4. **Flat Folder Routing**: All kit meshes, textures, and the shared Material Instance are placed flat inside `/Game/[Category]/[KitName]/`.
> [!IMPORTANT]
> **Hyphen Constraint:** Do not use hyphens (`-`) in standard non-kit asset filenames, as AssetPort treats hyphens as the kit separator.

## 7. Static Mesh LOD Behavior

1. FBX LOD groups embedded in a single file are enabled automatically.
2. Separately exported files ending in `_LOD0`, `_LOD1`, and later indices are grouped with the base Static Mesh and attached after its import.
3. An unsuffixed base mesh takes priority if both it and `_LOD0` are present.
4. Separate-file attachment currently targets Static Meshes; Skeletal Meshes stay on their existing import path.
5. Set `"auto_import_lods": false` in `importer_config.json` to skip both embedded and separate-file LOD import.

## 8. Smart Nanite Rules & Guardrails
When `"smart_nanite": true` is enabled in `importer_config.json`:
1. **Triangle Threshold:** Only Static Meshes with triangle counts strictly greater than `nanite_min_triangles` (default: `2500`) have Nanite enabled.
2. **LOD Exclusion:** Meshes with custom LOD chains (`_LOD1`, etc.) or multiple LOD levels are skipped to preserve custom hand-crafted LOD budgets.
3. **Material Blend Mode Guardrail:** Masked and Translucent meshes bypass Nanite to prevent overdraw and rasterization artifacts.
4. **Subsystem Build:** Settings are committed via `StaticMeshEditorSubsystem.set_nanite_settings` with change application enabled.
