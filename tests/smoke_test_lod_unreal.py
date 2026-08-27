"""Verify the embedded and separate-file Static Mesh LOD APIs in Unreal."""

import sys
from pathlib import Path

import unreal


repository_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repository_root))
for module_name in tuple(sys.modules):
    if module_name == "asset_port" or module_name.startswith("asset_port."):
        del sys.modules[module_name]

from asset_port.detector import AssetDetector  # noqa: E402
from asset_port.presets import get_mesh_setting  # noqa: E402


asset = AssetDetector().detect_file("SM_Test_LOD0.fbx")
fbx = get_mesh_setting(asset)
assert bool(fbx.static_mesh_import_data.import_mesh_lods) is True
fbx_without_lods = get_mesh_setting(asset, import_lods=False)
assert bool(fbx_without_lods.static_mesh_import_data.import_mesh_lods) is False

subsystem_class = getattr(unreal, "StaticMeshEditorSubsystem", None)
subsystem = unreal.get_editor_subsystem(subsystem_class) if subsystem_class else None
legacy = getattr(unreal, "EditorStaticMeshLibrary", None)
assert (subsystem and hasattr(subsystem, "import_lod")) or (
    legacy and hasattr(legacy, "import_lod")
)

unreal.log("AssetPort Static Mesh LOD API smoke test passed.")
