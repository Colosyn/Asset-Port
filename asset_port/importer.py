import unreal
from pathlib import Path
from asset_port.detector import AssetDetector
from asset_port.router import AssetRouter
from asset_port.presets import get_mesh_setting, texture_settings, evaluate_smart_nanite, apply_nanite_settings
from asset_port.models import AssetType, PipelineReport, TextureSlot, AtlasGroup
from asset_port.Validator import asset_validator, group_validator, atlas_group_validator
from asset_port.config import config_loader
from asset_port.materials import create_material_instance,create_atlas_material_instance

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
        
    def import_directory(self, source_dir, category, dry_run = False):
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
            assets_in_group = group.texture_list.copy()
            if group.mesh:
                assets_in_group.append(group.mesh)
                
            for asset in assets_in_group: 
                folder, asset_path = self.router.get_folder_path(asset, category)
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
                    
                    if asset.extension.lower() == ".fbx" or asset.asset_type in (AssetType.STATIC_MESH, AssetType.SKELETAL_MESH):
                        task.options = get_mesh_setting(asset, self.config.auto_import_lods)
                
                    task_pairs.append((asset, task)) 
            
            ref_asset = group.mesh or (group.texture_list[0] if group.texture_list else None)
            if ref_asset and ref_asset.ue_path:
                folder_parts = ref_asset.ue_path.split("/")[:-1]
                if folder_parts and folder_parts[-1] == "Textures":
                    folder_parts = folder_parts[:-1]
                group.folder_path = "/".join(folder_parts)   

                if group.mesh:
                    for lod_asset in sorted(group.lod_meshes, key=lambda item: item.lod_index):
                        lod_asset.ue_path = group.mesh.ue_path
                        lod_pairs.append((group.mesh, lod_asset))
                        
                group_warnings = group_validator(group)
                if group_warnings:
                    report.warnings.extend(group_warnings)
        
        if not dry_run:   
            unreal_tasks = [t for a, t in task_pairs]   
            imported_objects = unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(unreal_tasks)
                            
            for asset, task in task_pairs:
                imported_objs = task.get_objects()
                if not imported_objs:
                    continue
                for obj in imported_objs:
                    current_path = obj.get_package().get_name()
                    if current_path != asset.ue_path:
                        unreal.EditorAssetLibrary.rename_asset(current_path, asset.ue_path)
            
        
        report.groups_found = len(group_asset) + len(atlas_groups)
        report.atlas_group_found = len(atlas_groups)
        report.atlas_meshes_imported = sum(g.mesh_count for g in atlas_groups)
        if dry_run:
            report.asset_import = len(detect_group)
            report.lods_imported = len(lod_pairs) if self.config.auto_import_lods else 0
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
            
                slow_task.enter_progress_frame(1, f"Configuring textures: {asset.base_name}")
                if asset.asset_type == AssetType.TEXTURE:
                    imported_object = task.get_objects()
                    if not imported_object:
                        continue
                    for obj in imported_object:
                        texture_settings(obj, asset.texture_slot)
                        
                        if asset.texture_slot == TextureSlot.BASE_COLOUR:
                            asset.has_alpha = check_source_has_alpha(asset.source_path)
                            unreal.log(f"AssetPort: BaseColour {asset.base_name} has_alpha -> {asset.has_alpha}")
                    
        successful_imports = 0
        for asset, task in task_pairs:
            if len(task.get_objects()) >0:
                successful_imports += 1
                
            if len(task.get_objects()) ==0:
                report.asset_failed += 1
        
        report.asset_import = successful_imports + report.lods_imported
        
        return all_group, report
