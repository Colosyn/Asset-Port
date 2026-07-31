from pathlib import Path
from .models import AssetType, TextureSlot, DetectedAsset, AssetGroup
import re

PREFIX_MAP = {
    "sm": AssetType.STATIC_MESH,
    "sk": AssetType.SKELETAL_MESH,
    "t": AssetType.TEXTURE,
    "a": AssetType.ANIMATION,
    }

SUFFIX_MAP ={
    "b": TextureSlot.BASE_COLOUR,
    "basecolour": TextureSlot.BASE_COLOUR,
    "d": TextureSlot.BASE_COLOUR,
    "diffuse" : TextureSlot.BASE_COLOUR,
    "albedo": TextureSlot.BASE_COLOUR,
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
    
    "ao" : TextureSlot.AO,
    "ambientocclusion" : TextureSlot.AO,
    
    "e" : TextureSlot.EMISSIVE,
    "emissive" : TextureSlot.EMISSIVE,
    
    "o" : TextureSlot.OPACITY,
    "opacity" : TextureSlot.OPACITY,
    
    "mask" : TextureSlot.OPACITY_MASK,
    "opacitymask" : TextureSlot.OPACITY_MASK,
    
    "h" : TextureSlot.HEIGHT,
    "height" : TextureSlot.HEIGHT,
    "disp" : TextureSlot.HEIGHT,
    "displacement" : TextureSlot.HEIGHT,
    
    "orm" : TextureSlot.ORM,
}


CATEGORY_MAP ={
    "env" : "Environment",
    "wpn" : "Weapons",
    "prop" : "Props",
    "char" : "Characters",

}

class AssetDetector:
    
    def __init__(self) -> None:
        
        prefix_pattern = "|".join(PREFIX_MAP.keys())
        category_pattern = "|".join(CATEGORY_MAP.keys())
        suffix_pattern = "|".join(SUFFIX_MAP.keys())
    
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
        
        udim_tile = None
        udim_match = re.search(r"_(1[0-9]{3})$", stem)
        if udim_match:
            udim_tile = udim_match.group(1)
            stem = stem[:udim_match.start()]
        
        match = self.regax.match(stem)
        
        if not match:
            return DetectedAsset(
                filename=path_obj.name,
                source_path=str(path_obj.as_posix()),
                prefix="",
                base_name=stem,
                suffix="",
                asset_type=AssetType.UNKNOWN,
                texture_slot=None,
                extension=path_obj.suffix,
                category=None,
                material_slot_name=None
            )
        
        group = match.groupdict()
        
        prefix_raw = group.get("prefix")
        prefix = prefix_raw.lower() if prefix_raw else ""
        
        category_raw = group.get("category")
        category_str = category_raw.lower() if category_raw else ""
        
        base_name = group.get("base")
        material_raw = group.get("material")
        suffix_raw = group.get("suffix")
        
        if material_raw and not suffix_raw:
            if material_raw.lower() in SUFFIX_MAP:
                suffix_raw = material_raw
                material_raw = None
                
        material_slot_name = material_raw if material_raw else None
        suffix = suffix_raw if suffix_raw else ""
            
        
        asset_type = PREFIX_MAP.get(prefix, AssetType.UNKNOWN)
        
        category = CATEGORY_MAP.get(category_str, None) if category_str else None
        
        texture_slot = None
        if asset_type == AssetType.TEXTURE and suffix:
            texture_slot = SUFFIX_MAP.get(suffix.lower(), TextureSlot.UNKNOWN)
            
  
        detected_asset = DetectedAsset(
            filename=path_obj.name,
            source_path=str(path_obj.as_posix()),
            prefix=prefix,
            base_name = base_name or stem,
            suffix= suffix,
            asset_type= asset_type,
            texture_slot= texture_slot,
            extension= path_obj.suffix,
            category=category,
            material_slot_name=material_slot_name,
            udim_tile=udim_tile
        )
        

        return detected_asset
        
        
    def group_assets(self, assets : list[DetectedAsset]) -> list[AssetGroup]:
        
        groups = {}
        
        for asset in assets:
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
                group.mesh = asset
                
            
            if asset.category:
                group.category = asset.category
        
        return list(groups.values())
            