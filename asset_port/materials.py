import unreal
from asset_port.models import AssetGroup , MaterialBuildResult, TextureSlot
from asset_port.config import ImporterSettings

def create_material_instance(group : AssetGroup, config: ImporterSettings, decisions: dict = None):

    folder_path = group.folder_path
   
    material_report = MaterialBuildResult(base_name=group.base_name)
    mesh_object = unreal.EditorAssetLibrary.load_asset(group.mesh.ue_path) if group.mesh else None
    
    if group.is_multi_material:
       slot_to_process = group.material_slots
    else:    
       slot_to_process = {"": group.texture_list}
    
    for slot_name, textures in slot_to_process.items():
        if group.is_multi_material:
            mi_name = f"MI_{group.base_name}_{slot_name}"
            mi_package = f"{folder_path}/Materials"
        else:
            mi_name = f"MI_{group.base_name}"
            mi_package = folder_path
        
        mi_path =f"{mi_package}/{mi_name}"
        
        blend_mode = decisions.get(mi_name, "Opaque") if decisions else "Opaque"
        
        if blend_mode =="Masked":
            m_master = config.parent_material_masked
        elif blend_mode == "Translucent":
            m_master = config.parent_material_translucent
        else:
            m_master = config.parent_material_opaque
        
        parent_material = unreal.EditorAssetLibrary.load_asset(m_master)
        
        mi = None
        if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            if not config.replace_existing:
                mi = unreal.EditorAssetLibrary.load_asset(mi_path)
            else:
                unreal.EditorAssetLibrary.delete_asset(mi_path)
                
        if mi is None:
            factory = unreal.MaterialInstanceConstantFactoryNew()
            mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                asset_name=mi_name,
                package_path=mi_package,
                asset_class=unreal.MaterialInstanceConstant,
                factory=factory
            )
            
        mi.set_editor_property("parent", parent_material)
        
        if blend_mode in ("Masked", "Translucent"):
            base_color_tex = next((t for t in textures if t.texture_slot == TextureSlot.BASE_COLOUR),None)
            use_alpha = base_color_tex.has_alpha if base_color_tex else False
            
            unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                mi,
                "UseBaseColourAlpha",
                value=use_alpha
            )
            
        has_vt = False
        for texture in textures:
            if not texture.ue_path:
                continue
            tex_obj = unreal.EditorAssetLibrary.load_asset(texture.ue_path)
            if tex_obj and tex_obj.get_editor_property("virtual_texture_streaming"):
                has_vt = True
                break
            
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            mi,
            "UseVT",
            value=has_vt,
        )
        
        for texture in textures:
            if not texture.ue_path:
                continue
            texture_object = unreal.EditorAssetLibrary.load_asset(texture.ue_path)
            
            if has_vt and not texture_object.get_editor_property("virtual_texture_streaming"):
                texture_object.set_editor_property("virtual_texture_streaming", True)
                unreal.EditorAssetLibrary.save_loaded_asset(texture_object)
                
            param_name = texture.texture_slot.value
            if texture.texture_slot == TextureSlot.OPACITY_MASK:
                param_name = "OpacityMask"
            elif texture.texture_slot == TextureSlot.OPACITY:
                param_name = "Opacity"
                
            if has_vt:
                param_name = f"{param_name}_VT"
            
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                mi,
                param_name,
                texture_object
            )
            
            if texture.texture_slot == TextureSlot.ORM:
                unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                    mi,
                    "UseORM",
                    value=True
                )

            
            material_report.texture_assigned[param_name] = texture.ue_path
                
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        
        if mesh_object:
            if group.is_multi_material:
                static_mats = mesh_object.get_editor_property("static_materials")
                for idx ,mat_slot in enumerate(static_mats):
                    slot_str = str(mat_slot.get_editor_property("material_slot_name"))
                    
                    if slot_name.lower() in slot_str.lower() or slot_str.lower() in slot_name.lower():
                        mesh_object.set_material(idx, mi)
                        unreal.log(f"AssetPort: Assigned {mi_name} to slot [{idx}]'{slot_name}'")
                        break
                    
            else:
                mesh_object.set_material(0,mi)
                
            unreal.EditorAssetLibrary.save_loaded_asset(mesh_object)
            material_report.mesh_linked = group.mesh.base_name
            
    material_report.base_name = group.base_name
    material_report.success = True
    return material_report
    