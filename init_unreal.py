import unreal

def register_asset_port():
    menus = unreal.ToolMenus.get()
    
    toolbar = menus.extend_menu("ContentBrowser.ToolBar")
    if toolbar:
        entry = unreal.ToolMenuEntry(
            name="AssetPortImportButton",
            type=unreal.MultiBlockType.TOOL_BAR_BUTTON
        )
        entry.set_label("AssetPort")
        entry.set_tool_tip("Import Folder using AssetPort automated pipeline")
        entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            "AssetPort",
            "import asset_port.gui_helper; asset_port.gui_helper.run_importer()"
        )
        try:
            entry.insert_position = unreal.ToolMenuInsert("OpenFabWindow", unreal.ToolMenuInsertType.AFTER)
        except Exception:
            pass
        toolbar.add_menu_entry("Save", entry)

    context_menu = menus.extend_menu("ContentBrowser.AddNewContextMenu")
    if context_menu:
        entry = unreal.ToolMenuEntry(
            name="AssetPortContextMenu",
            type=unreal.MultiBlockType.MENU_ENTRY
        )
        entry.set_label("AssetPort")
        entry.set_tool_tip("Import Folder using AssetPort automated pipeline")
        entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            "AssetPort",
            "import asset_port.gui_helper; asset_port.gui_helper.run_importer()"
        )
        try:
            entry.insert_position = unreal.ToolMenuInsert("OpenFabWindow", unreal.ToolMenuInsertType.AFTER)
        except Exception:
            pass
        context_menu.add_menu_entry("ContentBrowserGetContent", entry)

    menus.refresh_all_widgets()
    
tick_handle = None

def on_tick(delta_time):
    global tick_handle
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    register_asset_port()

tick_handle = unreal.register_slate_post_tick_callback(on_tick)