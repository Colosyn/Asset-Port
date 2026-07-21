import unreal
from pathlib import Path
from asset_port.detector import AssetDetector
from asset_port.router import AssetRouter
from asset_port.presets import get_mesh_setting, texture_settings
from asset_port.models import AssetType, PipelineReport, TextureSlot
from asset_port.Validator import asset_validator, group_validator
from asset_port.config import config_loader
from asset_port.materials import create_material_instance

class AssetImporter():
    
    def __init__(self) -> None:
        self.router = AssetRouter()
        self.detector = AssetDetector()
        self.config = config_loader()
        
    def build_materials(self, group_asset, decisions=None, report= None):
        for group in group_asset:
            mode = decisions.get(group.base_name, "Opaque") if decisions else "Opaque"
            mi_report = create_material_instance(group, self.config, mode)
            if report and mi_report.success:
                report.mis_created += 1
                if mi_report.mesh_linked:
                    report.mis_linked += 1
        
    def import_directory(self, source_dir, category, dry_run = False):
        report = PipelineReport()
        file_path = Path(source_dir)
        tasks = []
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
            
            
            router_asset = self.router.get_folder_path(detected_asset, category)
            folder, asset = router_asset
            
            detected_asset.ue_path = asset
            if  len(errors) > 0 :
                report.errors.extend(errors)
                report.asset_failed += 1
                continue
            
            if len(warnings) > 0:
                report.warnings.extend(warnings)
            
            asset_name = asset.split("/")[-1]
            if not dry_run:
                task = unreal.AssetImportTask()  
                task.filename = detected_asset.source_path
                task.destination_path = folder
                task.destination_name = asset_name
                task.automated = True
                task.save = True
            
                if detected_asset.extension.lower() in (".fbx", ".obj") or detected_asset.asset_type in (AssetType.STATIC_MESH, AssetType.SKELETAL_MESH):
                    task.options = get_mesh_setting(detected_asset)
            
                tasks.append(task) 
            detect_group.append(detected_asset)
        if not dry_run:      
            imported_objects = unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
        
        for asset, task in zip(detect_group, tasks):
            imported_objs = task.get_objects()
            if not imported_objs:
                continue
            for obj in imported_objs:
                current_path = obj.get_package().get_name()
                if current_path != asset.ue_path:
                    unreal.EditorAssetLibrary.rename_asset(current_path, asset.ue_path)
        group_asset = self.detector.group_assets(detect_group)
        
        for group in group_asset:
            ref_asset = group.mesh or (group.texture_list[0] if group.texture_list else None)
            if ref_asset and ref_asset.ue_path:
                group.folder_path = "/".join(ref_asset.ue_path.split("/")[:-1])   
                
                group_warnings = group_validator(group)
                if group_warnings:
                    report.warnings.extend(group_warnings)
                           
        report.groups_found = len(group_asset)
        if dry_run:
            report.asset_import = len(detect_group)
            if self.config.auto_create_mi:
                report.mis_created = len(group_asset)
                report.mis_linked = sum(1 for g in group_asset if g.mesh is not None)
        
            return group_asset, report    
            
        total_steps = len(detect_group) + (len(group_asset) if self.config.auto_create_mi else 0)
        
        with unreal.ScopedSlowTask(total_steps, "Processing Imported assets...") as slow_task:
            slow_task.make_dialog(True)
                
    
            for asset, task in zip(detect_group, tasks):
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
                            try:
                                tex_format = str(obj.get_editor_property("format"))
                                asset.has_alpha = any(fmt in tex_format for fmt in ["DXT5","BC7","RGBA","BGRA", "TFO_BC7","TFO_DXT5"])
                            except Exception:
                                asset.has_alpha = False

                    
           
        successful_imports = 0
        for task in tasks:
            if len(task.get_objects()) >0:
                successful_imports += 1
                
            if len(task.get_objects()) ==0:
                report.asset_failed += 1
        
        report.asset_import = successful_imports
        
        return group_asset, report 