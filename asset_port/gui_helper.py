import unreal
import tkinter as tk 
from tkinter import filedialog
from asset_port.importer import AssetImporter
from asset_port.logger import log_pipeline_report
from asset_port.config import config_loader
active_widget = None
TAB_ID = unreal.Name("/Game/Python/Widgets/EUW_AssetPort.EUW_AssetPort_ActiveTab")
PREIVEW_ID = unreal.Name("/Game/Python/Widgets/EUW_AssetPort_Preview.EUW_AssetPort_Preview_ActiveTab")
def run_importer():
    global active_widget
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    widget_blueprint = unreal.load_asset("/Game/Python/Widgets/EUW_AssetPort")
    
    if widget_blueprint:
        active_widget = subsystem.spawn_and_register_tab(widget_blueprint)
        if active_widget:
            
        
            browse_button = active_widget.get_editor_property("Browse_Button")
            import_button = active_widget.get_editor_property("Import_Button")
            cancel_button = active_widget.get_editor_property("Cancel_Button")
            preview_button = active_widget.get_editor_property("Preview_Button")
            
            browse_button.on_clicked.add_callable(on_browse_clicked)
            import_button.on_clicked.add_callable(on_import_clicked)
            cancel_button.on_clicked.add_callable(on_cancel_clicked)
            preview_button.on_clicked.add_callable(on_preview_clicked)
def on_browse_clicked():
    if not active_widget:
        return
    
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder_path = filedialog.askdirectory(title="Select Import Folder")
    root.destroy()
    
    if folder_path:
        folder_path_field = active_widget.get_editor_property("Folder_Path_Field")
        folder_path_field.set_text(unreal.Text(folder_path))
        
        
def on_import_clicked():
    if not active_widget:
        return
    folder_path_field = active_widget.get_editor_property("Folder_Path_Field")
    folder_path_text = folder_path_field.get_text()
    folder_path = unreal.TextLibrary.conv_text_to_string(folder_path_text)
    
    category_dropdown = active_widget.get_editor_property("Category_Dropdown")
    category_str = category_dropdown.get_selected_option()
    category = None if category_str in ("None", "Auto-Detect") else category_str
    
    if folder_path:
        importer = AssetImporter()
        group, report = importer.import_directory(folder_path, category)
        log_pipeline_report(report, folder_path)
        
    on_cancel_clicked()
    
    
def on_cancel_clicked():
    global active_widget
    if active_widget:
        subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
        subsystem.close_tab_by_id(TAB_ID)
        active_widget = None
    active_widget = None
    
    
def on_preview_clicked():
    preview_widget = None
    config = config_loader()
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    widget_blueprint = unreal.load_asset("/Game/Python/Widgets/EUW_AssetPort_Preview")
    
   
    folder_path_field = active_widget.get_editor_property("Folder_Path_Field")
    folder_path_text = folder_path_field.get_text()
    folder_path = unreal.TextLibrary.conv_text_to_string(folder_path_text)
    
    category_dropdown = active_widget.get_editor_property("Category_Dropdown")
    category_str = category_dropdown.get_selected_option()
    category = None if category_str in ("None", "Auto-Detect") else category_str
    
    import_asset_name =[]
    failed_asset_name =[]
           
    if folder_path:
        importer = AssetImporter()
        groups, report = importer.import_directory(folder_path, category, True)
        
        
        for group in groups:
            if group.mesh is not None:
                import_asset_name.append(f"{group.folder_path}|Mesh : {group.base_name}")
            for texture in group.texture_list:
                import_asset_name.append(f"{group.folder_path}|texture({texture.texture_slot.value}) : {texture.base_name}")
        
            if config.auto_create_mi:
                import_asset_name.append(f"{group.folder_path}|Material : MI_{group.base_name}")   
                
        for warning in report.warnings:
            failed_asset_name.append(warning)
            
        for error in report.errors:
            failed_asset_name.append(error)
           
    if widget_blueprint:
        preview_widget = subsystem.spawn_and_register_tab(widget_blueprint)
        
    if preview_widget:
        preview_widget.set_editor_property("Import_List_Items", import_asset_name)
        preview_widget.set_editor_property("Failed_List_Items", failed_asset_name)
        preview_widget.call_method("RefreshPreviewUI")
        
        on_cancel_clicked()
        
        