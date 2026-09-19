import unittest
from asset_port.detector import AssetDetector

class SanitizerTests(unittest.TestCase):
    def setUp(self):
        self.detector = AssetDetector()
        
    def test_sanitize_spaces_in_filename(self):
        asset = self.detector.detect_file("ginga forward.fbx")
        self.assertEqual(asset.base_name, "ginga_forward")
    def test_sanitize_parentheses_number_padding(self):
        asset = self.detector.detect_file("capoeira (2).fbx")
        self.assertEqual(asset.base_name, "capoeira_02")
    def test_sanitize_preserves_hyphen_for_atlas_kits(self):
        asset = self.detector.detect_file("SM_env_Rock01-RockKit.fbx")
        self.assertEqual(asset.kit_name, "RockKit")
        self.assertEqual(asset.ue_asset_name, "SM_Rock01")
        

if __name__ == "__main__":
    unittest.main()