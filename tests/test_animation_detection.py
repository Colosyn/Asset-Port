import unittest

from asset_port.detector import AssetDetector
from asset_port.models import AssetType


class AnimationDetectionTests(unittest.TestCase):
    def setUp(self):
        self.detector = AssetDetector()
        
    def test_root_motion_and_loop_tokens(self):
        asset = self.detector.detect_file("A_Warrior_Run_RM_Loop.fbx")
        self.assertTrue(asset.is_root_motion)
        self.assertTrue(asset.is_loop)
        self.assertFalse(asset.is_in_place)
        self.assertEqual(asset.base_name, "Warrior_Run")
        self.assertEqual(asset.asset_type, AssetType.ANIMATION)   
    def test_in_place_full_word_alias(self):
        asset = self.detector.detect_file("Capoeira_Ginga_InPlace.fbx")
        self.assertTrue(asset.is_in_place)
        self.assertFalse(asset.is_root_motion)
        self.assertEqual(asset.base_name, "Capoeira_Ginga")
    def test_word_collision_does_not_trigger_tokens(self):
        asset = self.detector.detect_file("SM_Ship_Deck.fbx")
        self.assertFalse(asset.is_in_place)
        self.assertFalse(asset.is_root_motion)
        self.assertEqual(asset.base_name, "Ship_Deck")