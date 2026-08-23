import unreal
from asset_port.models import DetectedAsset, AssetType, TextureSlot

def get_mesh_setting(asset: DetectedAsset):
    
    fbx = unreal.FbxImportUI()
    
    fbx.import_materials = False
    fbx.import_textures = False
    
    if asset.asset_type == AssetType.STATIC_MESH :
        fbx.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        static_mesh = fbx.static_mesh_import_data
        static_mesh.combine_meshes = True
        static_mesh.generate_lightmap_u_vs = True
        
    elif asset.asset_type == AssetType.SKELETAL_MESH:
      fbx.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH  
      fbx.import_as_skeletal = True
      
    else:
        fbx.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH


    return fbx



def texture_settings(texture_asset, slot: TextureSlot):
    

    if slot in (TextureSlot.BASE_COLOUR, TextureSlot.EMISSIVE):
        texture_asset.srgb = True
        
        texture_asset.compression_settings =unreal.TextureCompressionSettings.TC_DEFAULT
        
    if slot == TextureSlot.NORMAL:
        texture_asset.srgb = False
        texture_asset.compression_settings =unreal.TextureCompressionSettings.TC_NORMALMAP
        
        
    if slot in (
        TextureSlot.ROUGHNESS,
        TextureSlot.METALLIC,
        TextureSlot.AO,
        TextureSlot.CAVITY,
        TextureSlot.SPECULAR,
        TextureSlot.GLOSS,
        TextureSlot.ORM,
        TextureSlot.RMA,
        TextureSlot.HEIGHT,
        TextureSlot.OPACITY_MASK,
    ):
        texture_asset.srgb = False
        texture_asset.compression_settings =unreal.TextureCompressionSettings.TC_MASKS
        
    if slot == TextureSlot.OPACITY:
        texture_asset.srgb = False
        texture_asset.compression_settings =unreal.TextureCompressionSettings.TC_ALPHA

    if slot == TextureSlot.TRANSLUCENCY:
        texture_asset.srgb = True
        texture_asset.compression_settings =unreal.TextureCompressionSettings.TC_DEFAULT
