# Naming Conventions

AssetPort parses filenames using a regex-based parser. To ensure that your meshes and textures are imported, categorized, and connected correctly, name your files using the following convention structure:

```text
[Prefix]_[Category]_[BaseName]_[Suffix].[extension]
```
*Example:* `SM_env_WallStone.fbx` or `T_env_WallStone_N.png`

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
| `_o`, `_opacity` | **Opacity** | `False` | `TC_Alpha` |
| `_h`, `_height` | **Height** | `False` | `TC_Masks` |
| `_orm` | **ORM** (Occlusion, Roughness, Metallic) | `False` | `TC_Masks` |

### Special Material Features:
* **ORM Textures:** If an `_orm` texture suffix is detected, the tool automatically turns on the static switch parameter **"UseORM"** in the material instance, allowing you to feed packed maps directly.
