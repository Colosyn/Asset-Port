import unreal
import tkinter as tk 
from tkinter import filedialog
from asset_port.importer import AssetImporter
from asset_port.logger import log_pipeline_report
from asset_port.config import config_loader
from asset_port.models import TextureSlot, AtlasGroup, AssetGroup
active_widget = None
preview_widget = None
last_folder_path = ""
last_category = None
last_auto_retarget = False
last_target_mesh = None
transparency_widget = None  
confirm_callback = None
cancel_callback = None     
skeleton_widget = None
TAB_ID = unreal.Name("/Game/Python/Widgets/EUW_AssetPort.EUW_AssetPort_ActiveTab")
PREIVEW_ID = unreal.Name("/Game/Python/Widgets/EUW_AssetPort_Preview.EUW_AssetPort_Preview_ActiveTab")
TRANSPARENCY_ID = unreal.Name("/Game/Python/Widgets/EUW_TransparencySetup.EUW_TransparencySetup_ActiveTab")
SKELETON_ID = unreal.Name("/Game/Python/Widgets/EUW_SkeletonSetup.EUW_SkeletonSetup_ActiveTab")

def safe_close_tab(tab_id):
    global active_widget, preview_widget, transparency_widget, skeleton_widget
    if tab_id == TAB_ID:
        active_widget = None
    elif tab_id == PREIVEW_ID:
        preview_widget = None
    elif tab_id == TRANSPARENCY_ID:
        transparency_widget = None
    elif tab_id == SKELETON_ID:
        skeleton_widget = None
        
    def _tick(delta_time):
        unreal.unregister_slate_post_tick_callback(handle)
        subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
        if subsystem and subsystem.does_tab_exist(tab_id):
            subsystem.close_tab_by_id(tab_id)
    handle = unreal.register_slate_post_tick_callback(_tick)
    
def _get_retarget_settings():
    try:
        box = active_widget.get_editor_property("Checkbox_AutoRetarget")
        mesh =active_widget.get_editor_property("Target_Mesh_Picker")
        return (box.is_checked() if box else False), mesh
    except Exception:
        return False, None
    
def scan_for_standalone_packs(groups):
    return [ g.base_name for g in groups if isinstance(g, AssetGroup) and g.mesh is None and getattr(g, "animation_list", None)]

def scan_for_transparency(groups):
    items = []
    for group in groups:
        if isinstance(group, AssetGroup) and group.is_multi_material:
            slot_to_scan = {f"MI_{group.base_name}_{slot}": texs for slot, texs in group.material_slots.items()}
        elif isinstance(group, AtlasGroup):
            slot_to_scan = {f"MI_{group.kit_name}" : group.texture_list}
        else:
            slot_to_scan = {f"MI_{group.base_name}": group.texture_list}
            
        for mi_name, textures in slot_to_scan.items():
            
            has_mask = any(t.texture_slot == TextureSlot.OPACITY_MASK for t in textures)
        
            has_opacity = any(t.texture_slot == TextureSlot.OPACITY for t in textures)
        
            base_colour = next((t for t in textures if t.texture_slot == TextureSlot.BASE_COLOUR), None)
            has_alpha = base_colour.has_alpha if base_colour else False
        
            if has_mask:
                items.append((mi_name, "Masked"))
            elif has_opacity:
                items.append((mi_name, "Translucent"))
            elif has_alpha:
                items.append((mi_name,"Masked"))
            
    return items
    
def show_transparency_popup(items, on_confirm_callback):
    global transparency_widget, confirm_callback, cancel_callback
    
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    widget_asset = unreal.load_asset("/Game/Python/Widgets/EUW_TransparencySetup")
    
    if not widget_asset:
        on_confirm_callback([])
        return
    
    transparency_widget = subsystem.spawn_and_register_tab(widget_asset)
    if transparency_widget:
        name = [item[0] for item in items]
        default = [item[1] for item in items]
        
        transparency_widget.set_editor_property("MaterialNames", name)
        transparency_widget.set_editor_property("DefaultModes", default)
        transparency_widget.call_method("PopulateTransparencyList")
        
        confirm_btn = transparency_widget.get_editor_property("Confirm_Button")
        cancel_btn = transparency_widget.get_editor_property("Cancel_Button")
        
        confirm_callback = lambda: on_popup_confirm(items, on_confirm_callback)
        cancel_callback = lambda: on_popup_cancel(on_confirm_callback)
        
        confirm_btn.on_clicked.add_callable(confirm_callback)
        cancel_btn.on_clicked.add_callable(cancel_callback)

def show_skeleton_popup(pack_names, on_confirm_callback):
    global skeleton_widget
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    widget_asset = unreal.load_asset("/Game/Python/Widgets/EUW_SkeletonSetup")
    
    if not widget_asset:
        on_confirm_callback({})
        return
    
    skeleton_widget = subsystem.spawn_and_register_tab(widget_asset)
    if skeleton_widget:
        
        skeleton_widget.set_editor_property("PackNames", pack_names)
        skeleton_widget.call_method("PopulatePackList")
        
        confirm_btn = skeleton_widget.get_editor_property("Confirm_Button")
        cancel_btn = skeleton_widget.get_editor_property("Cancel_Button")
        
        confirm_btn.on_clicked.add_callable(lambda: on_skeleton_confirm(pack_names, on_confirm_callback))
        cancel_btn.on_clicked.add_callable(lambda: on_skeleton_cancel(on_confirm_callback))
        
def on_skeleton_confirm(pack_names, on_confirm_callback):
    global skeleton_widget
    decisions = {}
    try:
        if skeleton_widget:
            scroll_box = skeleton_widget.get_editor_property("Pack_ScrollBox")
            rows = [scroll_box.get_child_at(i) for i in range(scroll_box.get_children_count())]
            for pack_name, row in zip(pack_names, rows):
                try:
                    picker = row.get_editor_property("Skeleton_Picker")
                    if picker:
                        decisions[pack_name] = picker
                except Exception as e:
                    unreal.log_error(f"AssetPort: Error reading skeleton for {pack_name}: {e}")
    finally:
        safe_close_tab(SKELETON_ID)
        on_confirm_callback(decisions)
        
def on_skeleton_cancel(on_confirm_callback):
    safe_close_tab(SKELETON_ID)
    on_confirm_callback({})      
        
def on_popup_confirm(items, on_confirm_callback):
    global transparency_widget
    decisions = {}
    
    try:
        if transparency_widget:
        
            scroll_box = transparency_widget.get_editor_property("Transparency_ScrollBox")
            count = scroll_box.get_children_count()
            rows = [scroll_box.get_child_at(i) for i in range(count)]
            
            for (mi_name,_), row in zip(items, rows):
                
                try:
                    combo = row.get_editor_property("ComboBox_BlendMode")
                    if combo:
                        selected_mode = combo.get_selected_option()
                        decisions[mi_name] =  selected_mode
                        unreal.log(f"AssetPort: Set {mi_name} blend mode -> {selected_mode}")
                    else:
                        unreal.log_warning(f"AssetPort: Could not find ComboBox on row for {mi_name}")
                        
                except Exception as err_row:
                    unreal.log_error(f"AssetPort: Error reading row for {mi_name}: {err_row}")
                
                   
    except Exception as err_main:
        unreal.log_error(f"AssetPort: Popup confirm error: {err_main}")
        
    finally:
                
        safe_close_tab(TRANSPARENCY_ID)
        on_confirm_callback(decisions)
            
def on_popup_cancel(on_confirm_callback):
    safe_close_tab(TRANSPARENCY_ID)
    on_confirm_callback({})
                          
def execute_import_pipeline(folder_path, category, target_skeleton=None, auto_retarget=False, target_retarget_mesh=None):
    importer = AssetImporter()
    
    groups_preview , _ = importer.import_directory(folder_path, category, dry_run=True,)
    standalone_packs = scan_for_standalone_packs(groups_preview)
    
    def start_live_import(skeleton_decisions):
        final_skeletons = skeleton_decisions if skeleton_decisions else target_skeleton
        groups, report = importer.import_directory(folder_path, category, dry_run=False,target_skeleton=final_skeletons,auto_retarget=auto_retarget, target_retarget_mesh=target_retarget_mesh,) 
        
        items = scan_for_transparency(groups)
    
        def complete_build(decisions):
            importer.build_materials(groups,decisions, report)
            log_pipeline_report(report, folder_path)
        
        if items:
            show_transparency_popup(items, complete_build)
        
        else:
            complete_build({})
        
    if standalone_packs and not target_skeleton:
        show_skeleton_popup(standalone_packs, start_live_import)
    else:
        start_live_import({})

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
    
    auto_retarget, target_mesh = _get_retarget_settings()
    
    folder_path_field = active_widget.get_editor_property("Folder_Path_Field")
    folder_path_text = folder_path_field.get_text()
    folder_path = unreal.TextLibrary.conv_text_to_string(folder_path_text)
    
    if not folder_path:
        unreal.EditorDialog.show_message(
            "Select Directory","Please select a valid import directory before importing",
            unreal.AppMsgType.OK
            )
        return
        
    if auto_retarget and not target_mesh:
        unreal.EditorDialog.show_message(
            "Target Mesh Required",
            "Auto Retarget is enabled. Please select a Target Skeletal Mesh before continuing.",
            unreal.AppMsgType.OK
            )
        return
    
    category_dropdown = active_widget.get_editor_property("Category_Dropdown")
    category_str = category_dropdown.get_selected_option()
    category = None if category_str in ("None", "Auto-Detect") else category_str
     
    if folder_path:
        execute_import_pipeline(folder_path, category, auto_retarget=auto_retarget, target_retarget_mesh=target_mesh)
        
        safe_close_tab(TAB_ID)
       
def on_cancel_clicked():
    safe_close_tab(TAB_ID)
    
def on_preview_clicked():
    
    global active_widget,  preview_widget, last_folder_path, last_category, last_target_mesh, last_auto_retarget
    config = config_loader()
    subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    widget_blueprint = unreal.load_asset("/Game/Python/Widgets/EUW_AssetPort_Preview")
    
    auto_retarget, target_mesh = _get_retarget_settings()
   
    folder_path_field = active_widget.get_editor_property("Folder_Path_Field")
    folder_path_text = folder_path_field.get_text()
    folder_path = unreal.TextLibrary.conv_text_to_string(folder_path_text)
    
    if not folder_path:
        unreal.EditorDialog.show_message(
            "Select Directory",
            "Please select a valid import directory before launching the preview.",
            unreal.AppMsgType.OK
        )
        return
    
    if auto_retarget and not target_mesh:
        unreal.EditorDialog.show_message(
            "Target Mesh Required",
            "Auto Retarget is enabled. Please select a Target Skeletal Mesh before continuing.",
            unreal.AppMsgType.OK
            )
        return
        
    category_dropdown = active_widget.get_editor_property("Category_Dropdown")
    category_str = category_dropdown.get_selected_option()
    category = None if category_str in ("None", "Auto-Detect") else category_str
    
    import_asset_name =[]
    failed_asset_name =[]
           
    if folder_path:
        last_folder_path = folder_path
        last_category = category
        last_auto_retarget = auto_retarget
        last_target_mesh = target_mesh
        
        importer = AssetImporter()
        groups, report = importer.import_directory(folder_path, category, True, auto_retarget=auto_retarget, target_retarget_mesh=target_mesh)
        log_pipeline_report(report, folder_path, True)
        
        max_udim_name_len = 0
        for group in groups:
            for texture in group.texture_list:
                if texture.is_udim:
                    name = texture.ue_path.split("/")[-1]
                    max_udim_name_len = max(max_udim_name_len, len(name))
        
        pad_width = max_udim_name_len + 10
        for group in groups:  
            display_folder = group.folder_path or "/Game/Animations"
            if display_folder.startswith("/Game/"):
                display_folder = display_folder[6:]
            if isinstance(group, AtlasGroup):
                display_folder = f"{display_folder}  [Atlas: {group.mesh_count} Meshes]"  
            if isinstance(group, AssetGroup) and  group.mesh is not None:
                mesh_name = group.mesh.ue_path.split("/")[-1]
                import_asset_name.append(f"{display_folder}|{mesh_name}")
            elif isinstance(group, AtlasGroup):
                for mesh in group.mesh_list:
                    mesh_name = mesh.ue_path.split("/")[-1]
                    import_asset_name.append(f"{display_folder}|{mesh_name}")
            for texture in group.texture_list:
                texture_name = texture.ue_path.split("/")[-1]
                if texture.is_udim:
                    padded_name= texture_name.ljust(pad_width)
                    texture_name = f"{padded_name}[UDIM: {texture.tile_count} Tiles]"
                if isinstance(group, AssetGroup) and group.is_multi_material:
                    import_asset_name.append(f"{display_folder}|Textures/{texture_name}")
                else:
                    import_asset_name.append(f"{display_folder}|{texture_name}")
            for anim in getattr(group, "animation_list", []):
                anim_name = anim.ue_path.split("/")[-1] if anim.ue_path else anim.base_name
                sub_path = f"Animations/{anim_name}" if group.mesh else anim_name
                import_asset_name.append(f"{display_folder}|{sub_path}")
        
            if config.auto_create_mi and(group.mesh or group.texture_list):
                if isinstance(group, AssetGroup) and group.is_multi_material:
                    for slot_name in group.material_slots.keys():
                        import_asset_name.append(f"{display_folder}|Materials/MI_{group.base_name}_{slot_name}")
                elif isinstance(group, AtlasGroup):
                    import_asset_name.append(f"{display_folder}|MI_{group.kit_name}")
                else:
                    import_asset_name.append(f"{display_folder}|MI_{group.base_name}")   
                
        for warning in report.warnings:
            failed_asset_name.append(warning)
            
        for error in report.errors:
            failed_asset_name.append(error)
           
    if widget_blueprint:
        preview_widget = subsystem.spawn_and_register_tab(widget_blueprint)
        
        
    if preview_widget:
        preview_import = preview_widget.get_editor_property("Confirm_Import")
        preview_cancel = preview_widget.get_editor_property("Cancel_preview")
        
        preview_import.on_clicked.add_callable(on_preview_import_clicked)
        preview_cancel.on_clicked.add_callable(on_preview_cancel_clicked)
        
        preview_widget.set_editor_property("Import_List_Items", import_asset_name)
        preview_widget.set_editor_property("Failed_List_Items", failed_asset_name)
        preview_widget.call_method("RefreshPreviewUI")
        
        safe_close_tab(TAB_ID)
               
def  on_preview_import_clicked():
    global last_folder_path, last_category, last_target_mesh, last_auto_retarget
   
    if last_folder_path:
        execute_import_pipeline(last_folder_path,last_category,auto_retarget=last_auto_retarget, target_retarget_mesh= last_target_mesh )
    safe_close_tab(PREIVEW_ID)
    
def on_preview_cancel_clicked():
    safe_close_tab(PREIVEW_ID)