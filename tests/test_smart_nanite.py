import sys
import unittest
from unittest.mock import MagicMock
# Allow running tests headlessly outside of Unreal Engine:
if "unreal" not in sys.modules:
    mock_unreal = MagicMock()
    class MockStaticMesh:
        def __init__(self, triangles=3000, num_lods=1):
            self._triangles = triangles
            self._num_lods = num_lods
            
        def get_num_triangles(self, lod_index=0):
            return self._triangles
            
        def get_num_lods(self):
            return self._num_lods
    mock_unreal.StaticMesh = MockStaticMesh
    sys.modules["unreal"] = mock_unreal
import unreal
from asset_port.presets import evaluate_smart_nanite
from asset_port.models import AssetGroup, DetectedAsset, AssetType
from asset_port.config import ImporterSettings

class SmartNaniteTests(unittest.TestCase):
    def setUp(self):
        self.config = ImporterSettings(smart_nanite=True, nanite_min_triangles=2500)
    def test_dense_opaque_mesh_enables_nanite(self):
        mesh = unreal.StaticMesh(triangles=3000)
        group = AssetGroup(base_name="SM_Rock")
        self.assertTrue(evaluate_smart_nanite(mesh, group, self.config, "Opaque"))
    def test_low_poly_mesh_disables_nanite(self):
        mesh = unreal.StaticMesh(triangles=500)
        group = AssetGroup(base_name="SM_Box")
        self.assertFalse(evaluate_smart_nanite(mesh, group, self.config, "Opaque"))
    def test_embedded_fbx_lods_disables_nanite(self):
        mesh = unreal.StaticMesh(triangles=5000, num_lods=4)
        group = AssetGroup(base_name="SM_Tree")
        self.assertFalse(evaluate_smart_nanite(mesh, group, self.config, "Opaque"))
    def test_transparent_or_masked_disables_nanite(self):
        mesh = unreal.StaticMesh(triangles=5000)
        group = AssetGroup(base_name="SM_Glass")
        self.assertFalse(evaluate_smart_nanite(mesh, group, self.config, "Masked"))
        self.assertFalse(evaluate_smart_nanite(mesh, group, self.config, "Translucent"))
if __name__ == "__main__":
    unittest.main()