import unittest
from asset_port.router import AssetRouter
from asset_port.models import DetectedAsset, AssetType, TextureSlot

class RouterTests(unittest.TestCase):
    def setUp(self):
        self.router = AssetRouter()
        
    def test_animation_and_retarget_routing(self):
        anim = DetectedAsset(
            filename="ginga.fbx",
             source_path="D:/Capoeira/ginga.fbx",
            prefix="",
            base_name="ginga",
            suffix="",
            asset_type=AssetType.ANIMATION,
            texture_slot=None,
            extension=".fbx",
        )
        folder, path = self.router.get_folder_path(anim)
        self.assertEqual(folder, "/Game/Animations/Capoeira")
        self.assertTrue(path.endswith("A_ginga"))
        
        char_folder, _ = self.router.get_folder_path(anim, character_name="Ninja")
        self.assertEqual(char_folder, "/Game/Characters/Ninja/Animations")
        
        retarget_folder, _ = self.router.get_folder_path(
            anim, character_name="Mannequin", is_retargeted=True
        )
        self.assertEqual(retarget_folder, "/Game/Characters/Mannequin/Animations/Capoeira")
    def test_canonical_prefixes_for_prefixless_assets(self):
        mesh = DetectedAsset(
            filename="Rock.fbx",
            source_path="D:/Props/Rock.fbx",
            prefix="",
            base_name="Rock",
            suffix="",
            asset_type=AssetType.STATIC_MESH,
            texture_slot=None,
            extension=".fbx",
            category="Environment",
        )
        _, path = self.router.get_folder_path(mesh)
        self.assertTrue(path.endswith("SM_Rock"))
    def test_texture_routes_to_textures_subfolder(self):
        tex = DetectedAsset(
            filename="T_Desk_Wood_BaseColor.png",
            source_path="D:/Desk/T_Desk_Wood_BaseColor.png",
            prefix="t",
            base_name="Desk",
            material_slot_name="Wood",
            suffix="BaseColor",
            asset_type=AssetType.TEXTURE,
            texture_slot=TextureSlot.BASE_COLOUR,
            extension=".png",
            category="Props",
        )
        folder, path = self.router.get_folder_path(tex)
        self.assertEqual(folder, "/Game/Props/Desk/Textures")
        self.assertTrue(path.endswith("T_Desk_Wood_BaseColor"))
    def test_already_prefixed_asset_does_not_duplicate_prefix(self):
        mesh = DetectedAsset(
            filename="SM_Chair.fbx",
            source_path="D:/SM_Chair.fbx",
            prefix="sm",
            base_name="Chair",
            suffix="",
            asset_type=AssetType.STATIC_MESH,
            texture_slot=None,
            extension=".fbx",
            category="Props",
        )
        _, path = self.router.get_folder_path(mesh)
        self.assertTrue(path.endswith("SM_Chair"))
        self.assertFalse("SM_SM_" in path)
        

if __name__ == "__main__":
    unittest.main()