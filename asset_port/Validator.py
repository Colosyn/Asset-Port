from pathlib import Path
from asset_port.models import AssetType, AssetGroup, TextureSlot,DetectedAsset

def asset_validator(asset : DetectedAsset ):
    
    warnings = []
    errors = []

    
    file_path = asset.source_path
    
    file_size = Path(file_path).stat().st_size

    if file_size == 0:
        errors.append("file is empty or corrupted")
        
    if file_size > 500*1024*1024 and asset.asset_type in (AssetType.STATIC_MESH, AssetType.SKELETAL_MESH):
        warnings.append("Mesh size is bigger than 500 MB")
        
    if file_size > 100*1024*1024 and asset.asset_type == AssetType.TEXTURE:
        warnings.append("Texture Size is bigger than 100 MB")
        
    extensions = [".fbx",".png",".tga", ".jpg", ".exr"]
    extension = asset.extension
    lower_extension = extension.lower()
    
    if lower_extension not in extensions:
        errors.append("File Format not supported")
        
    if asset.prefix == "":
        warnings.append("Asset doesn't have Prefix")
    
    return warnings, errors 
        

def group_validator(group : AssetGroup):
    
    warnings = []
    found_texture = []
    textures = group.texture_list
    for texture in textures:
        found_texture.append(texture.texture_slot)
        
    if group.mesh is None and len(group.texture_list) > 0:
        warnings.append(f"group {group.base_name} has no mesh but textures" )
        
    if TextureSlot.BASE_COLOUR not in found_texture:
        warnings.append(f"group {group.base_name} base colour map is missing")
        
    if TextureSlot.NORMAL not in found_texture:
        warnings.append(f"group {group.base_name} Normal map is missing")
        
    if TextureSlot.ROUGHNESS not in found_texture and TextureSlot.ORM not in found_texture:
        warnings.append(f"group {group.base_name} Roughness or ORM map is missing ") 
        
        
    return warnings