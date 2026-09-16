import unreal
from typing import Optional

def _clean_character_name(mesh: unreal.SkeletalMesh) -> str:
    name = mesh.get_name()
    for prefix in ("SKM_", "SK_", "skm_", "sk_"):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name

def get_or_create_ik_rig(skeletal_mesh: unreal.SkeletalMesh, package_path: Optional[str] =None) -> unreal.IKRigDefinition:
   
    char_name = _clean_character_name(skeletal_mesh)
    target_folder = package_path or f"/Game/Characters/{char_name}/Rigs"
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
    
    target_folder = package_path or F"/Game/Characters/{tgt_mesh}/Rigs"
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
    
    rtg_controller.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    
    if hasattr(rtg_controller, "add_default_ops"):
        rtg_controller.add_default_ops()
        
    if hasattr(rtg_controller, "auto_align_all_bones"):
        try:
            rtg_controller.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
        except Exception:
            pass
        
    unreal.EditorAssetLibrary.save_loaded_asset(retargeter)
    return True

def batch_retarget_animation(retargeter: unreal.IKRetargeter, source_mesh: unreal.SkeletalMesh, target_mesh: unreal.SkeletalMesh, anim_assets: list, search: str ="", replace: str ="", prefix: str ="", suffix: str ="",) -> list:
    
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
        