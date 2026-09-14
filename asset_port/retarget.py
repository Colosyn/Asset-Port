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