import unreal
from pathlib import Path
from typing import Optional
from asset_port.detector import AssetDetector
from asset_port.router import AssetRouter
from asset_port.presets import get_mesh_setting,get_animation_setting, texture_settings, evaluate_smart_nanite, apply_nanite_settings
from asset_port.models import AssetType, PipelineReport, TextureSlot, AtlasGroup
from asset_port.Validator import asset_validator, group_validator, atlas_group_validator
from asset_port.config import config_loader
from asset_port.materials import create_material_instance,create_atlas_material_instance
from asset_port.retarget import get_character_folder, _clean_character_name,get_or_create_ik_rig,get_or_create_retargeter, auto_characterize_ik_rig,setup_retargeter, batch_retarget_animation

def check_source_has_alpha(file_path):
    if not file_path:
        return False
    try:
        ext = file_path.lower()
        if ext.endswith((".jpg",".jpeg",".bmp")):
            return False
        
        with open(file_path, "rb") as f:
            header = f.read(30)
            
            if ext.endswith(".png") and header.startswith(b"\x89PNG\r\n\x1a\n"):
                color_type = header[25]
                if color_type in (4,6):
                    return True
                
                f.seek(0)
                data = f.read(65536)
                if b"IDAT" in data:
                    data = data[:data.index(b"IDAT")]
                return b"tRNS" in data
            
            elif ext.endswith(".tga") and len(header) >= 18:
                descriptor = header[17]
                return (descriptor & 0x0F) > 0
            
            elif ext.endswith(".exr") and header.startswith(b"\x76\x2f\x31\x01"):
                f.seek(8)
                data = f.read(65536)
                idx = data.find(b"channels\x00")
                if idx == -1:
                    return False
                pos = idx + len(b"channels\x00")
                if data[pos:pos+7] != b"chlist\x00":
                    return False
                pos +=7
                size = int.from_bytes(data[pos:pos+7], "little")
                pos += 4
                end = pos = size
                while pos < end:
                    name_end = data.find(b"\x00", pos)
                    if name_end == -1 or name_end == pos:
                        break
                    name = data[pos:name_end].decode("ascii", errors="ignore")
                    if name in ("A","a","Alpha", "ALPHA"):
                        return True
                    pos = name_end +1 +16
                
                return False
    except Exception:
        pass
    return False

class AssetImporter():
    
    def __init__(self) -> None:
        self.router = AssetRouter()
        self.detector = AssetDetector()
        self.config = config_loader()
        
    def build_materials(self, group_asset, decisions=None, report= None):
        for group in group_asset:
            if not group.mesh and not group.texture_list:
                continue
            if isinstance(group, AtlasGroup):
                mi_report = create_atlas_material_instance(group, self.config, decisions)
                blend_mode = decisions.get(f"MI_{group.kit_name}", "Opaque") if decisions else "Opaque"
                for mesh in group.mesh_list:
                    if mesh.ue_path:
                        mesh_obj = unreal.EditorAssetLibrary.load_asset(mesh.ue_path)
                        if mesh_obj and evaluate_smart_nanite(mesh_obj, group, self.config, blend_mode):
                            apply_nanite_settings(mesh_obj, True)
                            unreal.EditorAssetLibrary.save_loaded_asset(mesh_obj)
                            
            else:
                mi_report = create_material_instance(group, self.config, decisions)
                
                if group.mesh and group.mesh.ue_path:
                    mesh_obj = unreal.EditorAssetLibrary.load_asset(group.mesh.ue_path)
                    if group.is_multi_material:
                        is_transparent = any(decisions.get(f"MI_{group.base_name}_{slot}", "Opaque") in ("Masked", "Translucent")
                        for slot in group.material_slots) if decisions else False
                        blend_mode = "Masked" if is_transparent else "Opaque"
                    else:
                        blend_mode = decisions.get(f"MI_{group.base_name}", "Opaque") if decisions else "Opaque"
                    if mesh_obj and evaluate_smart_nanite(mesh_obj,group,self.config, blend_mode):
                        apply_nanite_settings(mesh_obj,True)
                        unreal.EditorAssetLibrary.save_loaded_asset(mesh_obj)
                        
            if report and mi_report.success:
                report.mis_created += 1
                if mi_report.mesh_linked:
                    report.mis_linked += 1

    def _import_static_mesh_lod(self, mesh_asset, lod_asset, report):
        """Attach a separately exported FBX to an imported Static Mesh LOD."""
        if not self.config.auto_import_lods:
            return False
        if mesh_asset.asset_type != AssetType.STATIC_MESH:
            report.warnings.append(
                f"LOD{lod_asset.lod_index} skipped for non-static mesh {mesh_asset.base_name}"
            )
            return False

        static_mesh = unreal.EditorAssetLibrary.load_asset(mesh_asset.ue_path)
        if static_mesh is None:
            report.errors.append(f"Could not load base mesh for LOD import: {mesh_asset.ue_path}")
            return False

        result = -1
        try:
            subsystem_class = getattr(unreal, "StaticMeshEditorSubsystem", None)
            subsystem = unreal.get_editor_subsystem(subsystem_class) if subsystem_class else None
            if subsystem and hasattr(subsystem, "import_lod"):
                result = subsystem.import_lod(
                    static_mesh, int(lod_asset.lod_index), lod_asset.source_path
                )
            else:
                legacy = getattr(unreal, "EditorStaticMeshLibrary", None)
                if legacy and hasattr(legacy, "import_lod"):
                    result = legacy.import_lod(
                        static_mesh, int(lod_asset.lod_index), lod_asset.source_path
                    )
        except Exception as error:
            report.errors.append(
                f"LOD{lod_asset.lod_index} import failed for {mesh_asset.base_name}: {error}"
            )
            return False

        success = result if isinstance(result, bool) else result is not None and int(result) >= 0
        if not success:
            report.errors.append(
                f"LOD{lod_asset.lod_index} import failed for {mesh_asset.base_name}"
            )
            return False

        lod_asset.ue_path = mesh_asset.ue_path
        unreal.EditorAssetLibrary.save_loaded_asset(static_mesh)
        report.lods_imported += 1
        return True
        
    def import_directory(self, source_dir, category, dry_run = False, target_skeleton: Optional[unreal.Skeleton] =None, auto_retarget: bool = False, target_retarget_mesh: Optional[unreal.SkeletalMesh] = None):
        report = PipelineReport()
        file_path = Path(source_dir)
        task_pairs = []
        lod_pairs = []
        detect_group = []
        for file in file_path.rglob("*"):
            if file.is_dir():
                continue
            report.total_scanned += 1
            detected_asset = self.detector.detect_file(file)
            
            if detected_asset is None:
                report.asset_failed += 1
                continue
            validator = asset_validator(detected_asset )
            warnings, errors = validator
            
            if  len(errors) > 0 :
                report.errors.extend(errors)
                report.asset_failed += 1
                continue
                        
            if len(warnings) > 0:
                report.warnings.extend(warnings)
            
            detect_group.append(detected_asset)
        
        atlas_groups, remianing_assets = self.detector.group_atlas_assets(detect_group)
        group_asset = self.detector.group_assets(remianing_assets)
        
        all_group = atlas_groups + group_asset
        
        for atlas_group in atlas_groups:
            for mesh in atlas_group.mesh_list:
                folder, asset_path = self.router.get_atlas_folder_path(mesh, atlas_group,category)
                mesh.ue_path = asset_path
                atlas_group.folder_path = folder
                
                mesh_name = mesh.ue_path.split("/")[-1]
                if not dry_run:
                    task = unreal.AssetImportTask()  
                    task.filename = mesh.source_path
                    task.destination_path = folder
                    task.destination_name = mesh_name
                    task.automated = True
                    task.save = True
                                        
                    if mesh.extension.lower() == ".fbx" or mesh.asset_type in (AssetType.STATIC_MESH, AssetType.SKELETAL_MESH):
                        task.options = get_mesh_setting(mesh, self.config.auto_import_lods)
                                    
                    task_pairs.append((mesh, task))
                mesh_key = mesh.ue_asset_name or mesh.base_name
                for lod_asset in sorted(
                    atlas_group.lod_meshes.get(mesh_key, []),
                    key=lambda item: item.lod_index,
                ):
                    lod_asset.ue_path = asset_path
                    lod_pairs.append((mesh, lod_asset))
            for texture in atlas_group.texture_list:
                folder, asset_path = self.router.get_atlas_folder_path(texture, atlas_group,category)
                texture.ue_path = asset_path
                if texture.is_udim and not texture.is_udim_primary:
                    continue
                texture_name = texture.ue_path.split("/")[-1]
                if not dry_run:
                    task = unreal.AssetImportTask()  
                    task.filename = texture.source_path
                    task.destination_path = folder
                    task.destination_name = texture_name
                    task.automated = True
                    task.save = True
                                                            
                    task_pairs.append((texture, task))
            atlas_warnings = atlas_group_validator(atlas_group)
            if atlas_warnings:
                report.warnings.extend(atlas_warnings)
                    
        for group in group_asset:
            
            character_name = group.mesh.base_name if (group.mesh and group.mesh.asset_type == AssetType.SKELETAL_MESH) else None
            
            assets_in_group = []
            if group.mesh:
                assets_in_group.append(group.mesh)
            assets_in_group.extend(group.texture_list)
           
                
            for asset in assets_in_group: 
                folder, asset_path = self.router.get_folder_path(asset, category, character_name=character_name)
                asset.ue_path = asset_path
                if asset.is_udim and not asset.is_udim_primary:
                    continue
                
                asset_name = asset.ue_path.split("/")[-1]
                if not dry_run:
                        
                    task = unreal.AssetImportTask()  
                    task.filename = asset.source_path
                    task.destination_path = folder
                    task.destination_name = asset_name
                    task.automated = True
                    task.save = True
                    
                    if asset.asset_type == AssetType.ANIMATION:
                        task.options = get_animation_setting(skeleton=None)
                    elif asset.extension.lower() == ".fbx" or asset.asset_type in (AssetType.STATIC_MESH, AssetType.SKELETAL_MESH):
                        task.options = get_mesh_setting(asset, self.config.auto_import_lods)
                
                    task_pairs.append((asset, task)) 
            
            ref_asset = group.mesh or (group.texture_list[0] if group.texture_list else (group.animation_list[0] if group.animation_list else None))
            if ref_asset:
                if not ref_asset.ue_path:
                    _, ref_asset.ue_path = self.router.get_folder_path(ref_asset,category, character_name=character_name)
                folder_parts = ref_asset.ue_path.split("/")[:-1]
                if folder_parts and folder_parts[-1] in ("Textures", "Animations"):
                    folder_parts = folder_parts[:-1]
                group.folder_path = "/".join(folder_parts)   

                if group.mesh:
                    for lod_asset in sorted(group.lod_meshes, key=lambda item: item.lod_index):
                        lod_asset.ue_path = group.mesh.ue_path
                        lod_pairs.append((group.mesh, lod_asset))
                        
                group_warnings = group_validator(group)
                if group_warnings:
                    report.warnings.extend(group_warnings)
                    
        character_skeletons = {}
        character_meshs = {}
        if not dry_run:   
            unreal_tasks = [t for a, t in task_pairs]   
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(unreal_tasks)               
            for asset, task in task_pairs:
                if asset.asset_type == AssetType.SKELETAL_MESH:
                    for obj in task.get_objects():
                        if isinstance(obj, unreal.SkeletalMesh):
                            character_skeletons[asset.base_name] = obj.get_editor_property("skeleton")
                            character_meshs[asset.base_name] = obj
                            skel = obj.get_editor_property("skeleton")
                            phys = obj.get_editor_property("physics_asset")
                            if skel: 
                                unreal.EditorAssetLibrary.save_loaded_asset(skel)
                            if phys: 
                                unreal.EditorAssetLibrary.save_loaded_asset(phys)
                                
                imported_objs = task.get_objects()
                if not imported_objs:
                    continue
                for obj in imported_objs:
                    if isinstance(obj, (unreal.StaticMesh, unreal.SkeletalMesh, unreal.Texture2D)):
                        current_path = obj.get_package().get_name()
                        if current_path != asset.ue_path:
                            unreal.EditorAssetLibrary.rename_asset(current_path, asset.ue_path)
         
        anim_task_pairs = []
        for group in group_asset:
            if not group.animation_list:
                continue
            character_name = group.mesh.base_name if (group.mesh and group.mesh.asset_type == AssetType.SKELETAL_MESH)  else None
            if isinstance(target_skeleton, dict):
                group_skeleton = character_skeletons.get(group.base_name, target_skeleton.get(group.base_name))
            else:
                group_skeleton = character_skeletons.get(group.base_name, target_skeleton)
            
            for anim in group.animation_list:
                folder, asset_path = self.router.get_folder_path(anim, category, character_name=character_name)
                anim.ue_path = asset_path
                if not dry_run:
                    task = unreal.AssetImportTask()
                    task.filename = anim.source_path
                    task.destination_path =folder
                    task.destination_name = anim.ue_path.split("/")[-1]
                    task.automated =  True
                    task.save = True
                    task.options = get_animation_setting(skeleton=group_skeleton)
                    anim_task_pairs.append((anim, task))
        
        if not dry_run and anim_task_pairs:
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t for a,t in anim_task_pairs])
            for asset , task in anim_task_pairs:
                for obj in (task.get_objects() or []):
                    current_path = obj.get_package().get_name()
                    if current_path != asset.ue_path:
                        unreal.EditorAssetLibrary.rename_asset(current_path, asset.ue_path)
                        
        task_pairs = task_pairs + anim_task_pairs
        
        report.groups_found = len(group_asset) + len(atlas_groups)
        report.atlas_group_found = len(atlas_groups)
        report.atlas_meshes_imported = sum(g.mesh_count for g in atlas_groups)
        if dry_run:
            report.asset_import = len(detect_group)
            report.lods_imported = len(lod_pairs) if self.config.auto_import_lods else 0
            report.animations_imported = sum(len(g.animation_list) for g in group_asset)
            if auto_retarget and target_retarget_mesh:
                report.animations_retargeted = report.animations_imported
            if self.config.auto_create_mi:
                report.mis_created = len(group_asset) + len(atlas_groups)
                report.mis_linked = sum(1 for g in group_asset if g.mesh is not None)
        
            return all_group, report    
            
        lod_steps = len(lod_pairs) if self.config.auto_import_lods else 0
        total_steps = len(task_pairs) + lod_steps + (len(all_group) if self.config.auto_create_mi else 0)
        
        with unreal.ScopedSlowTask(total_steps, "Processing Imported assets...") as slow_task:
            slow_task.make_dialog(True)

            if self.config.auto_import_lods:
                for mesh_asset, lod_asset in lod_pairs:
                    if slow_task.should_cancel():
                        break
                    slow_task.enter_progress_frame(
                        1,
                        f"Importing LOD{lod_asset.lod_index}: {mesh_asset.base_name}",
                    ) 
                    success = self._import_static_mesh_lod(mesh_asset, lod_asset, report)
                    if not success:
                        report.warnings.append(f"LOD import failed for {mesh_asset.base_name}, skipping remaining LODs.")
                        break

            for asset, task in task_pairs:
                if slow_task.should_cancel():
                    break
                
                label = f"Configuring texture: {asset.base_name}" if asset.asset_type == AssetType.TEXTURE else f"Processing {asset.base_name}"
                slow_task.enter_progress_frame(1, label)
                if asset.asset_type == AssetType.TEXTURE:
                    imported_object = task.get_objects()
                    if not imported_object:
                        continue
                    for obj in imported_object:
                        texture_settings(obj, asset.texture_slot)
                        
                        if asset.texture_slot == TextureSlot.BASE_COLOUR:
                            asset.has_alpha = check_source_has_alpha(asset.source_path)
                            unreal.log(f"AssetPort: BaseColour {asset.base_name} has_alpha -> {asset.has_alpha}")
                
                if asset.asset_type == AssetType.ANIMATION:
                    created_anims = [obj for obj in (task.get_objects() or []) if isinstance(obj, unreal.AnimSequence)]
                    if created_anims:
                        report.animations_imported += 1
                        if asset.is_root_motion:
                            for obj in created_anims:
                                obj.set_editor_property("enable_root_motion", True)
                                unreal.EditorAssetLibrary.save_loaded_asset(obj)
                                unreal.log(f"AssetPort: Enable root motion for {asset.base_name}")
                                    
                    else:
                        report.asset_failed += 1
                        report.errors.append(f"Animation {asset.base_name} rejected: Incompatible bone tracks for target skeleton.")
                    
                                
            if not dry_run and auto_retarget and target_retarget_mesh:
                target_ik_rig = get_or_create_ik_rig(target_retarget_mesh)
                if not auto_characterize_ik_rig(target_ik_rig, target_retarget_mesh):
                    report.warnings.append(f"AssetPort: Auto-retarget aborted, could not characterize target {target_retarget_mesh.get_name()}")
                else:
                    for group in group_asset:
                        if not group.animation_list:
                            continue
                        
                        source_mesh = character_meshs.get(group.base_name)
                        if not  source_mesh or source_mesh == target_retarget_mesh:
                            continue
                        
                        source_ik_rig = get_or_create_ik_rig(source_mesh)
                        if not auto_characterize_ik_rig(source_ik_rig, source_mesh):
                            report.warnings.append(f"AssetPort: Auto-retarget skipped for {group.base_name} -characterization failed.")
                            continue
                        
                        retargeter = get_or_create_retargeter(source_mesh, target_retarget_mesh)
                        if not setup_retargeter(retargeter, source_ik_rig, target_ik_rig, source_mesh, target_retarget_mesh):
                            report.warnings.append(f"AssetPort: Auto-retarget skipped for {group.base_name} — retargeter setup failed.")
                            continue
                        group_anim_objects = []
                        
                        for anim_asset, task in anim_task_pairs:
                            if anim_asset in group.animation_list:
                                for obj in (task.get_objects() or []):
                                    if isinstance(obj, unreal.AnimSequence):
                                        group_anim_objects.append(obj)
                                        
                        pack_name = ""
                        if group.animation_list:
                            first = group.animation_list[0]
                            pack_name = Path(first.source_path).parent.name if first.source_path else ""
                            if pack_name ==".":
                                pack_name = ""
                                        
                        if group_anim_objects:
                            retargeted = batch_retarget_animation(retargeter,source_mesh, target_retarget_mesh, group_anim_objects) 
                            report.animations_retargeted += len(retargeted)
                            char_folder = get_character_folder(target_retarget_mesh)
                            subfolder = pack_name if (pack_name and pack_name.lower() != group.base_name.lower()) else group.base_name
                            dest_folder = f"{char_folder}/Animations/{subfolder}"
                            unreal.EditorAssetLibrary.make_directory(dest_folder)
                            for asset_dat in retargeted:
                                obj = asset_dat.get_asset()
                                if obj:
                                    unreal.EditorAssetLibrary.save_loaded_asset(obj)
                                    clean_name = str(asset_dat.asset_name).replace("RTG_TMP_", "")
                                    dest_path = f"{dest_folder}/{clean_name}"
                                    if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
                                        unreal.EditorAssetLibrary.delete_asset(dest_path)
                                    if unreal.EditorAssetLibrary.rename_asset(str(asset_dat.package_name), dest_path):
                                        unreal.EditorAssetLibrary.save_asset(dest_path)
                                
                            
        successful_imports = 0
        for asset, task in task_pairs:
            if len(task.get_objects()) >0:
                successful_imports += 1
                
            if len(task.get_objects()) ==0:
                report.asset_failed += 1
        
        report.asset_import = successful_imports + report.lods_imported
        
        return all_group, report
