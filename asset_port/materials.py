import unreal
from asset_port.models import AssetGroup , MaterialBuildResult, TextureSlot
from asset_port.config import ImporterSettings
def create_material_instance(group : AssetGroup, config: ImporterSettings):
    folder_path = group.folder_path
    
    m_master = config.parent_material
    mi_path = f"{folder_path}/MI_{group.base_name}"
    mi = None
    mesh = group.mesh
    material_report = MaterialBuildResult(base_name=group.base_name)
    
    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        if not config.replace_existing:
            mi = unreal.EditorAssetLibrary.load_asset(mi_path)
            
        else:
            unreal.EditorAssetLibrary.delete_asset(mi_path)
            
    mi_name = f"MI_{group.base_name}"      
      
    if mi is None:
        factory =unreal.MaterialInstanceConstantFactoryNew()
        
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name=mi_name,
            package_path= group.folder_path,
            asset_class= unreal.MaterialInstanceConstant,
            factory=factory
            
            )
        
        
            
    parent_material = unreal.EditorAssetLibrary.load_asset(m_master)
    mi.set_editor_property("parent", parent_material)
    
    for texture in group.texture_list:
        texture_path = texture.ue_path
        texture_object = unreal.EditorAssetLibrary.load_asset(texture_path)
        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            mi,
            texture.texture_slot.value,
            texture_object
            )
        material_report.texture_assigned[texture.texture_slot.value] = texture.ue_path
        if texture.texture_slot == TextureSlot.ORM:
            unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                mi,
                "UseORM",
                value= True
            )
    
    if mesh is not None:
        
        mesh_object = unreal.EditorAssetLibrary.load_asset(mesh.ue_path)
        mesh_object.set_material(0,mi)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh_object)
        material_report.mesh_linked = mesh.base_name
        
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
           
    material_report.base_name = mi_name
    material_report.mi_path = mi_path
    material_report.success = True
        
    return material_report