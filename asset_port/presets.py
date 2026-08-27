import unreal
from asset_port.models import DetectedAsset, AssetType, TextureSlot

def get_mesh_setting(asset: DetectedAsset, import_lods=True):
    
    fbx = unreal.FbxImportUI()
    
    fbx.import_materials = False
    fbx.import_textures = False
    
    if asset.asset_type == AssetType.STATIC_MESH :
        fbx.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        static_mesh = fbx.static_mesh_import_data
        # Import LOD groups embedded in a single FBX. Separate _LOD files are
        # attached after the base mesh has been imported.
        try:
            static_mesh.import_mesh_lods = bool(import_lods)
        except Exception:
            pass
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

def evaluate_smart_nanite(mesh_obj, group, config, blend_mode = "Opaque") -> bool:
    
    if not getattr(config, "smart_nanite", True):
        return False
    if not isinstance(mesh_obj, unreal.StaticMesh):
        return False
    if group.lod_meshes or mesh_obj.get_num_lods() > 1:
        return False
    if blend_mode in ("Masked", "Translucent"):
        return False
    min_tris = getattr(config, "nanite_min_triangles", 2500)
    if mesh_obj.get_num_triangles(0) <= min_tris:
        return False
    
    return True


def apply_nanite_settings(mesh_obj, enabled: bool):
    nanite = mesh_obj.get_editor_property("nanite_settings")
    nanite.enabled = enabled

    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if subsystem and hasattr(subsystem, "set_nanite_settings"):
        subsystem.set_nanite_settings(mesh_obj, nanite, apply_changes=True)
        return

    # fallback
    mesh_obj.set_editor_property("nanite_settings", nanite)
    unreal.log_warning(f"Nanite subsystem unavailable — settings applied to {mesh_obj.get_name()} but build not triggered")
    