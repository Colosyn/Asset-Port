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