import unreal
from typing import Optional

def get_mesh_for_skeleton(skeleton: unreal.Skeleton):
    if not skeleton:
        return None
    pkg = skeleton.get_package().get_name()
    
    candidate = pkg.replace("_Skeleton", "")
    if unreal.EditorAssetLibrary.does_asset_exist(candidate):
        return unreal.EditorAssetLibrary.load_asset(candidate)
    for ref in unreal.EditorAssetLibrary.find_package_referencers_for_asset(pkg):
        asset = unreal.EditorAssetLibrary.load_asset(ref)
        if isinstance(asset, unreal.SkeletalMesh):
            return asset
    return None

def _clean_character_name(mesh: unreal.SkeletalMesh) -> str:
    name = mesh.get_name()
    for prefix in ("SKM_", "SK_", "skm_", "sk_"):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name

def get_character_folder(mesh: unreal.SkeletalMesh):
    pkg = mesh.get_package().get_name()
    parts = [p for p in pkg.split("/")[:-1] if p not in ("Meshes", "Mesh")]
    return "/".join(parts)

def get_or_create_ik_rig(skeletal_mesh: unreal.SkeletalMesh, package_path: Optional[str] =None) -> unreal.IKRigDefinition:
   
    char_name = _clean_character_name(skeletal_mesh)
    target_folder = package_path or f"{get_character_folder(skeletal_mesh)}/Rigs"
    asset_name = f"IK_{char_name}"
    asset_path = f"{target_folder}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    
    unreal.EditorAssetLibrary.make_directory(target_folder)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.IKRigDefinitionFactory() 
    return tools.create_asset(asset_name, target_folder, unreal.IKRigDefinition, factory)

def get_or_create_retargeter(source_mesh: unreal.SkeletalMesh, target_mesh: unreal.SkeletalMesh, package_path: Optional[str] = None) -> unreal.IKRetargeter:
    
    src_name = _clean_character_name(source_mesh)
    tgt_mesh = _clean_character_name(target_mesh)
    
    target_folder = package_path or F"{get_character_folder(target_mesh)}/Rigs"
    asset_name = f"RTG_{src_name}_to_{tgt_mesh}"
    asset_path = f"{target_folder}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    
    unreal.EditorAssetLibrary.make_directory(target_folder)
    
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.IKRetargetFactory()   
    return tools.create_asset(asset_name, target_folder, unreal.IKRetargeter, factory)

def auto_characterize_ik_rig(ik_rig: unreal.IKRigDefinition, skeletal_mesh: unreal.SkeletalMesh) -> bool:
    
    ikr_controller = unreal.IKRigController.get_controller(ik_rig)
    if not ikr_controller:
        unreal.log_error(f"AssetPort: Could not get IKRigCOntroller for {ik_rig.get_name()}")
        return False
        
    if len(ikr_controller.get_retarget_chains()) >= 4:
        return True
    
    ikr_controller.set_skeletal_mesh(skeletal_mesh)
    if not ikr_controller.apply_auto_generated_retarget_definition():
        unreal.log_warning(f"AssetPort: Auto-characterization failed for {skeletal_mesh.get_name()} - unknown rig template.")
        return False
    
    chains = ikr_controller.get_retarget_chains()
    if not chains or len(chains) < 4:
        unreal.log_warning(f"AssetPort: Insufficient retarget chains ({len(chains) if chains else 0}/4 minimum) for {skeletal_mesh.get_name()}.")
        return False
    
    try:
        ikr_controller.apply_auto_fbik()
    except Exception as e:
        unreal.log_warning(f"AssetPort: Auto-FBIK skipped for {skeletal_mesh.get_name()}: {e}")
        
    unreal.EditorAssetLibrary.save_loaded_asset(ik_rig)
    return True

def setup_retargeter(retargeter: unreal.IKRetargeter, source_ik_rig: unreal.IKRigDefinition, target_ik_rig: unreal.IKRigDefinition, source_mesh: unreal.SkeletalMesh, target_mesh: unreal.SkeletalMesh,) -> bool:
    
    rtg_controller = unreal.IKRetargeterController.get_controller(retargeter)
    if not rtg_controller:
        unreal.log_error(f"AssetPort: COuld not get IkRetargerController for {retargeter.get_name()}")
        return False
    
    rtg_controller.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, source_ik_rig)
    rtg_controller.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, target_ik_rig)
    rtg_controller.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, source_mesh)
    rtg_controller.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, target_mesh)
    
    src_chains = [str(c.chain_name).lower() for c in unreal.IKRigController.get_controller(source_ik_rig).get_retarget_chains()]
    has_metacarpals = any("metacarpal" in c for c in src_chains)
    has_root = any(c == "root" for c in src_chains)
    
    if hasattr(rtg_controller, "add_default_ops"):
        need_ops =True
        if hasattr(rtg_controller, "get_num_retarget_ops") and rtg_controller.get_num_retarget_ops() > 0:
            for op_idx in range(rtg_controller.get_num_retarget_ops()):
                if "fk" in str(rtg_controller.get_op_name(op_idx)).lower():
                    if len(rtg_controller.get_op_controller(op_idx).get_settings().get_editor_property("chains_to_retarget")) >0:
                        need_ops = False
                        break
        if need_ops:
            while hasattr(rtg_controller, "remove_retarget_op") and rtg_controller.get_num_retarget_ops() > 0:
                rtg_controller.remove_retarget_op(0)
            rtg_controller.add_default_ops()
            
    rtg_controller.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
        
    
    finger_kw = ("thumb","index","middle", "ring", "pinky")
    fk_mode = getattr(getattr(unreal, "FKChainRotationMode", None), "ONE_TO_ONE", None)
    legacy_mode = getattr(getattr(unreal, "RetargetRotationMode", None), "ONE_TO_ONE", None)
   
    for tgt_chains in unreal.IKRigController.get_controller(target_ik_rig).get_retarget_chains():
        name = str(tgt_chains.chain_name)
        if ("metacarpal" in name.lower() and not has_metacarpals) or (name.lower() == "root" and not has_root):
            rtg_controller.set_source_chain(unreal.Name("None"), tgt_chains.chain_name)
    
    if hasattr(rtg_controller, "get_num_retarget_ops"):
        for op_idx in range(rtg_controller.get_num_retarget_ops()):
            if "fk" in str(rtg_controller.get_op_name(op_idx)).lower():
                op_c = rtg_controller.get_op_controller(op_idx)
                op_settings = op_c.get_settings()
    
                new_chains = []
                for ch in op_settings.get_editor_property("chains_to_retarget"):
                    t_name = str(ch.get_editor_property("target_chain_name")).lower()
                    if "metacarpal" in t_name and not has_metacarpals:
                        ch.set_editor_property("enable_fk", False)
                    elif any(f in t_name for f in finger_kw) and fk_mode is not None:
                        ch.set_editor_property("rotation_mode", fk_mode)
                    new_chains.append(ch)
                op_settings.set_editor_property("chains_to_retarget", new_chains)
                op_c.set_settings(op_settings)
                break      
    else:
        for s in rtg_controller.get_all_chain_settings():
            if any(k in str(s.get_editor_property("target_chain")).lower() for k in finger_kw):
                if legacy_mode is not None:
                    s.get_editor_property("settings").get_editor_property("fk").set_editor_property("rotation_mode", legacy_mode)
                    
    src_h = max(1.0, source_mesh.get_bounds().box_extent.z * 2.0)
    tgt_h = max(1.0, target_mesh.get_bounds().box_extent.z * 2.0)
    scale_ratio = tgt_h / src_h
    
    if hasattr(rtg_controller, "get_root_settings"):
        root_settings = rtg_controller.get_root_settings()
        root_settings.scale_vertical = scale_ratio
        rtg_controller.set_root_settings(root_settings)
             
    unreal.EditorAssetLibrary.save_loaded_asset(retargeter)
    return True

def batch_retarget_animation(retargeter: unreal.IKRetargeter, source_mesh: unreal.SkeletalMesh, target_mesh: unreal.SkeletalMesh, anim_assets: list, search: str ="", replace: str ="", prefix: str ="RTG_TMP_", suffix: str ="",) -> list:
    
    if not anim_assets:
        return []
    
    asset_data_list = [ a if isinstance(a, unreal.AssetData) else unreal.AssetRegistryHelpers.create_asset_data(a) for a in anim_assets]
    
    if hasattr(unreal.IKRetargetBatchOperation, "run_batch_retarget"):
        inputs = unreal.IKRetargetBatchOperationInputs()
        inputs.assets_to_retarget = asset_data_list
        inputs.source_mesh = source_mesh
        inputs.target_mesh = target_mesh
        inputs.ik_retarget_asset = retargeter
        inputs.search = search
        inputs.replace = replace
        inputs.prefix = prefix
        inputs.suffix = suffix
        inputs.include_referenced_assets = True
        return list(unreal.IKRetargetBatchOperation.run_batch_retarget(inputs))
    
    try:
        return list(unreal.IKRetargetBatchOperation.duplicate_and_retarget(asset_data_list, source_mesh, target_mesh, retargeter, search,replace,prefix,suffix, True,True))
    except TypeError:
        pass
    
    try:
        return list(unreal.IKRetargetBatchOperation.duplicate_and_retarget(asset_data_list, source_mesh, target_mesh, retargeter, search,replace,prefix,suffix, True))
    except TypeError:
        pass
    
    unreal.log_error(f"AssetPort: Unsupported engine version for batch retargeting.")
    return []
        