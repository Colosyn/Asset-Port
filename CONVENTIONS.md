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

---

## 1. Prefixes (Asset Type)

Prefixes tell the tool what type of asset is being imported. This is case-insensitive.

| Prefix | Asset Type | Destination Unreal Class |
| :--- | :--- | :--- |
| `sm_` | Static Mesh | `unreal.StaticMesh` |
| `sk_` | Skeletal Mesh | `unreal.SkeletalMesh` |
| `t_` | Texture | `unreal.Texture2D` |
| `a_` | Animation | `unreal.AnimSequence` |

*If no prefix is found, the asset type defaults to `Unknown` and will not be automated.*

---

## 2. Categories (Automatic Folder Routing)

Categories determine the subfolder under `/Game/` where the assets will be stored. This is case-insensitive.

| Tag | Category | Destination Content Browser Path |
| :--- | :--- | :--- |
| `env_` | Environment | `/Game/Environment/[BaseName]/` |
| `wpn_` | Weapons | `/Game/Weapons/[BaseName]/` |
| `prop_` | Props | `/Game/Props/[BaseName]/` |
| `char_` | Characters | `/Game/Characters/[BaseName]/` |

* **Dropdown Override:** You can override this auto-sorting in the tool UI by selecting an explicit category.
* **Unsorted Fallback:** If no tag is matched and no override is selected, assets are routed to `/Game/_Unsorted/[BaseName]/`.

---

## 3. Texture Suffixes (Material Slots & Settings)

Suffixes determine how textures are mapped inside the created **Material Instance** parameters, and automatically sets their Unreal Engine texture compression and sRGB flags.

| Suffix | Texture Slot / Parameter | sRGB | Compression Setting |
| :--- | :--- | :--- | :--- |
| `_b`, `_basecolour`, `_d`, `_diffuse`, `_albedo`, `_basecolor` | **BaseColour** | `True` | `TC_Default` |
| `_n`, `_nrm`, `_normal` | **Normal** | `False` | `TC_Normalmap` |
| `_r`, `_roughness`, `_rough` | **Roughness** | `False` | `TC_Masks` |
| `_m`, `_metal`, `_metallic` | **Metallic** | `False` | `TC_Masks` |
| `_ao`, `_ambientocclusion` | **AmbientOcclusion** (AO) | `False` | `TC_Masks` |
| `_e`, `_emissive` | **Emissive** | `True` | `TC_Default` |
| `_o`, `_opacity`, `_mask`, `_opacitymask` | **Opacity / Mask** | `False` | `TC_Alpha` |
| `_h`, `_height`, `_disp`, `_displacement`  | **Height** | `False` | `TC_Masks` |
| `_orm` | **ORM** (Occlusion, Roughness, Metallic) | `False` | `TC_Masks` |

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
| Emissive | `Emissive` | The emissive map input |
| Opacity | `Opacity` | The opacity / transparency input |
| Height | `Height` | The height / displacement input |
| ORM | `ORM` | The occlusion, roughness, and metallic packed input |

### Static Switches

* **`UseORM`**: Automatically set to `True` when an `_orm` texture is detected.
* **`UseBaseColourAlpha`**: Automatically set to `True` when a Base Colour texture with an embedded alpha channel is detected and the material blend mode is set to `Masked` or `Translucent`.

### Unmatched Suffixes and Parameters

If a texture's suffix doesn't match any known slots, or if a slot is not found on your custom Master Material:
* **Safe Fallback:** The assignment will be silently ignored.
* **Pipeline Continues:** It will not raise an error or crash the import process. The mesh will still be imported, the material instance will be created, other matching parameters will be connected, and the material will be assigned to the mesh successfully.
