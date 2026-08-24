import unittest
from asset_port.detector import AssetDetector
from asset_port.models import AssetType, TextureSlot

class CategoryInheritanceTests(unittest.TestCase):
    def setUp(self):
        self.detector = AssetDetector()
        
    def test_group_category_propagated_to_unprefixed_textures(self):
      
        mesh = self.detector.detect_file("SM_env_Chest.fbx")
        tex_d = self.detector.detect_file("T_Chest_BaseColor.png")
        tex_n = self.detector.detect_file("T_Chest_Normal.png")
        groups = self.detector.group_assets([mesh, tex_d, tex_n])
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group.category, "Environment")
        self.assertEqual(group.mesh.category, "Environment")
        
        for tex in group.texture_list:
            self.assertEqual(tex.category, "Environment")
            
    def test_atlas_kit_consensus_category_resolution(self):
       
        mesh1 = self.detector.detect_file("SM_Rock01-RockKit.fbx")
        mesh2 = self.detector.detect_file("SM_prop_Rock02-RockKit.fbx")
        tex = self.detector.detect_file("T_RockKit_D.png")
        atlas_groups, remaining = self.detector.group_atlas_assets([mesh1, mesh2, tex])
        self.assertEqual(len(atlas_groups), 1)
        kit = atlas_groups[0]
        self.assertEqual(kit.category, "Props")
        
        for m in kit.mesh_list:
            self.assertEqual(m.category, "Props")
            
        for t in kit.texture_list:
            self.assertEqual(t.category, "Props")
            
    def test_new_categories_vehicle_and_fx(self):
        
        veh_mesh = self.detector.detect_file("SM_veh_Car.fbx")
        fx_tex = self.detector.detect_file("T_fx_Smoke_D.png")
        self.assertEqual(veh_mesh.category, "Vehicles")
        self.assertEqual(fx_tex.category, "Effects")
        
if __name__ == "__main__":
    unittest.main()