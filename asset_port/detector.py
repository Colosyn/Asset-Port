from pathlib import Path
from .models import AssetType, TextureSlot, DetectedAsset, AssetGroup, AtlasGroup
import re

PREFIX_MAP = {
    "sm": AssetType.STATIC_MESH,
    "sk": AssetType.SKELETAL_MESH,
    "skm": AssetType.SKELETAL_MESH,
    "t": AssetType.TEXTURE,
    "a": AssetType.ANIMATION,
    "anim": AssetType.ANIMATION,
    }

SUFFIX_MAP ={
    "b": TextureSlot.BASE_COLOUR,
    "basecolour": TextureSlot.BASE_COLOUR,
    "d": TextureSlot.BASE_COLOUR,
    "diffuse" : TextureSlot.BASE_COLOUR,
    "albedo": TextureSlot.BASE_COLOUR,
    "alb": TextureSlot.BASE_COLOUR,
    "basecolor": TextureSlot.BASE_COLOUR,
    
    
    "n": TextureSlot.NORMAL,
    "nrm": TextureSlot.NORMAL,
    "normal" : TextureSlot.NORMAL,
    
    "r" : TextureSlot.ROUGHNESS,
    "roughness" : TextureSlot.ROUGHNESS,
    "rough" : TextureSlot.ROUGHNESS,
    
    "m" : TextureSlot.METALLIC,
    "metal" : TextureSlot.METALLIC,
    "metallic" : TextureSlot.METALLIC,
    "metalness" : TextureSlot.METALLIC,
    
    "ao" : TextureSlot.AO,
    "ambientocclusion" : TextureSlot.AO,
    "cavity" : TextureSlot.CAVITY,
    
    "e" : TextureSlot.EMISSIVE,
    "emissive" : TextureSlot.EMISSIVE,
    
    "o" : TextureSlot.OPACITY,
    "opacity" : TextureSlot.OPACITY,
    
    "mask" : TextureSlot.OPACITY_MASK,
    "opacitymask" : TextureSlot.OPACITY_MASK,

    "specular" : TextureSlot.SPECULAR,
    "gloss" : TextureSlot.GLOSS,
    "translucency" : TextureSlot.TRANSLUCENCY,
    
    "h" : TextureSlot.HEIGHT,
    "height" : TextureSlot.HEIGHT,
    "disp" : TextureSlot.HEIGHT,
    "displacement" : TextureSlot.HEIGHT,
    "bump" : TextureSlot.HEIGHT,
    
    "orm" : TextureSlot.ORM,
    "arm" : TextureSlot.ORM,
    
    "rma" : TextureSlot.RMA,
}


CATEGORY_MAP ={
    "env" : "Environment",
    "wpn" : "Weapons",
    "prop" : "Props",
    "char" : "Characters",
    "veh" : "Vehicles",
    "fx" : "Effects",

}

class AssetDetector:
    
    def __init__(self) -> None:
        
        # Prefer longer aliases so overlapping names are parsed deterministically.
        prefix_pattern = "|".join(sorted(PREFIX_MAP.keys(), key=len, reverse=True))
        category_pattern = "|".join(sorted(CATEGORY_MAP.keys(), key=len, reverse=True))
        suffix_pattern = "|".join(sorted(SUFFIX_MAP.keys(), key=len, reverse=True))
    
        pattern = (
            rf"^(?:(?P<prefix>{prefix_pattern})_)?"
            rf"(?:(?P<category>{category_pattern})_)?"
            rf"(?P<base>.+?)"
            rf"(?:_(?P<material>[A-Za-z0-9]+?))?"
            rf"(?:_(?P<suffix>{suffix_pattern}))?$"
                 
        )
        
        self.regax = re.compile(pattern, re.IGNORECASE)
        
    
    def detect_file(self, file_path ) -> DetectedAsset :
        
        path_obj = Path(file_path)
        stem = path_obj.stem

        # Keep separately exported Mesh_LOD0.fbx, Mesh_LOD1.fbx, ... in the
        # same asset group without treating the marker as a material token.
        lod_index = None
        if path_obj.suffix.lower() == ".fbx":
            lod_match = re.search(r"_LOD(?P<index>\d+)$", stem, re.IGNORECASE)
            if lod_match:
                lod_index = int(lod_match.group("index"))
                if parsed_index <= 7:
                    lod_index = parsed_index
                    stem = stem[:lod_match.start()]
                    # Any index > 7 will leave lod_index =None and prwserve the original stem
        
        udim_tile = None
        udim_match = re.search(r"_(1[0-9]{3})$", stem)
        if udim_match:
            udim_tile = udim_match.group(1)
            stem = stem[:udim_match.start()]
        
        match = self.regax.match(stem)
        inferred_type = self._infer_type(path_obj.suffix)
        
        if not match:
            return DetectedAsset(
                filename=path_obj.name,
                source_path=str(path_obj.as_posix()),
                prefix="",
                base_name=stem,
                suffix="",
                asset_type=inferred_type,
                texture_slot=None,
                extension=path_obj.suffix,
                category=None,
                material_slot_name=None,
                lod_index=lod_index,
            )
        
        group = match.groupdict()
        
        prefix_raw = group.get("prefix")
        prefix = prefix_raw.lower() if prefix_raw else ""
        
        category_raw = group.get("category")
        category_str = category_raw.lower() if category_raw else ""
        
        parsed_name = group.get("base")
        material_raw = group.get("material")
        suffix_raw = group.get("suffix")
        
        kit_name = ""
        ue_asset_name = ""
        
        if "-" in parsed_name and prefix in ("sm", "sk"):
            parts = parsed_name.rsplit("-", 1)
            individual_name = parts[0]
            kit_name =parts[1]
            ue_asset_name = f"{prefix.upper()}_{individual_name}"
        
        if material_raw and not suffix_raw:
            if material_raw.lower() in SUFFIX_MAP:
                suffix_raw = material_raw
                material_raw = None

        # Marketplace filenames commonly include resolution metadata before the
        # texture suffix (for example ``Rock_2K_BaseColor``). It is not a
        # material-slot name and should not split the asset into a separate slot.
        if material_raw and re.fullmatch(r"\d+[Kk]", material_raw):
            material_raw = None
                
        material_slot_name = material_raw if material_raw else None
        suffix = suffix_raw if suffix_raw else ""
            
        
        asset_type = PREFIX_MAP.get(prefix, inferred_type)
        
        category = CATEGORY_MAP.get(category_str, None) if category_str else None
        
        texture_slot = None
        if asset_type == AssetType.TEXTURE and suffix:
            texture_slot = SUFFIX_MAP.get(suffix.lower(), TextureSlot.UNKNOWN)
            
  
        detected_asset = DetectedAsset(
            filename=path_obj.name,
            source_path=str(path_obj.as_posix()),
            prefix=prefix,
            base_name = parsed_name,
            suffix= suffix,
            asset_type= asset_type,
            texture_slot= texture_slot,
            extension= path_obj.suffix,
            category=category,
            material_slot_name=material_slot_name,
            udim_tile=udim_tile,
            kit_name=kit_name,
            ue_asset_name=ue_asset_name,
            lod_index=lod_index,
        )
        

        return detected_asset

    @staticmethod
    def _infer_type(extension):
        extension = extension.lower()
        if extension in (".png", ".tga", ".jpg", ".exr"):
            return AssetType.TEXTURE
        if extension == ".fbx":
            return AssetType.STATIC_MESH
        return AssetType.UNKNOWN
        
        
    def group_assets(self, assets : list[DetectedAsset]) -> list[AssetGroup]:
        
        groups = {}
        
        for asset in assets:
            if asset.asset_type not in (
                AssetType.TEXTURE,
                AssetType.STATIC_MESH,
                AssetType.SKELETAL_MESH,
            ):
                continue
            if asset.base_name not in groups:
                groups[asset.base_name] = AssetGroup(
                    base_name= asset.base_name,
                ) 
            
            group = groups[asset.base_name]
            if asset.asset_type == AssetType.TEXTURE:
                if asset.is_udim and not asset.is_udim_primary:
                    primary = next((t for t in group.texture_list 
                                    if t.suffix == asset.suffix and
                                    t.material_slot_name == asset.material_slot_name), None)
                    if primary:
                        primary.tile_count += 1
                    continue
                group.texture_list.append(asset)
                
                if asset.material_slot_name:
                    if asset.material_slot_name not in group.material_slots:
                        group.material_slots[asset.material_slot_name] = []
                    group.material_slots[asset.material_slot_name].append(asset)
                
            elif asset.asset_type in (AssetType.SKELETAL_MESH, AssetType.STATIC_MESH):
                if asset.lod_index in (None, 0):
                    # Prefer an unsuffixed base mesh if both it and LOD0 exist.
                    if group.mesh is None or group.mesh.lod_index == 0:
                        group.mesh = asset
                else:
                    group.lod_meshes.append(asset)
                
            
            if asset.category:
                group.category = asset.category
        
        for group in groups.values():
            if group.category:
                if group.mesh:
                    group.mesh.category = group.category
                for tex in group.texture_list:
                    tex.category = group.category
                for lod in group.lod_meshes:
                    lod.category = group.category
        
        return list(groups.values())
            
            
    def group_atlas_assets(self, assets: list[DetectedAsset]) -> tuple[list[AtlasGroup], list[DetectedAsset]]:
        
        kit_meshes ={}
        atlas_lods = {}
        
        for asset in assets:
            if asset.kit_name and asset.lod_index not in (None, 0):
                mesh_key = asset.ue_asset_name or asset.base_name
                atlas_lods.setdefault(asset.kit_name, {}).setdefault(mesh_key, []).append(asset)
            elif asset.kit_name:
                if asset.kit_name not in kit_meshes:
                    kit_meshes[asset.kit_name] = []
                kit_meshes[asset.kit_name].append(asset)
                
        
        kit_textures = {}
        
        remaining = []
        
        for asset in assets:
            if asset.kit_name:
                continue
            
            if asset.asset_type == AssetType.TEXTURE and asset.base_name in kit_meshes:
                
                if asset.base_name not in kit_textures:
                    kit_textures[asset.base_name] = []
                kit_textures[asset.base_name].append(asset)
                
            else:
                remaining.append(asset)
                
                
        atlas_group = []
        
        for kit_name, meshes in kit_meshes.items():
            lod_assets = [
                lod
                for lod_list in atlas_lods.get(kit_name, {}).values()
                for lod in lod_list
            ]
            all_kit_assets = meshes + lod_assets + kit_textures.get(kit_name, [])
            kit_category = next((a.category for a in all_kit_assets if a.category), None)
            
            if kit_category:
                for asset in all_kit_assets:
                    asset.category = kit_category
                    
            group = AtlasGroup(
                kit_name=kit_name,
                mesh_list=meshes,
                texture_list=kit_textures.get(kit_name,[]),
                category=kit_category,
                lod_meshes=atlas_lods.get(kit_name, {}),
            )
            atlas_group.append(group)
            
        return atlas_group, remaining
