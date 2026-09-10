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
    def test_animation_grouped_with_character(self):
        skel = self.detector.detect_file("SK_char_Knight.fbx")
        anim = self.detector.detect_file("A_Knight_Attack_RM.fbx")
        group = self.detector.group_assets([skel,anim])
        self.assertEqual(len(group), 1)
        self.assertEqual(group[0].base_name, "Knight")
        self.assertEqual(len(group[0].animation_list), 1)
        self.assertEqual(group[0].animation_list[0].category, "Characters")
    def test_standalone_animation_pack_from_folder(self):
        anim1 = self.detector.detect_file("Capoeira/A_ginga.fbx")
        anim2 = self.detector.detect_file("Capoeira/A_kick.fbx")
        groups = self.detector.group_assets([anim1, anim2])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].base_name, "Capoeira")
        self.assertIsNone(groups[0].mesh)
        self.assertEqual(len(groups[0].animation_list), 2)
        self.assertEqual(groups[0].category, "Animations")
        