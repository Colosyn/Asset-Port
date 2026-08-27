import unittest

from asset_port.detector import AssetDetector


class LodGroupingTests(unittest.TestCase):
    def setUp(self):
        self.detector = AssetDetector()

    def test_separate_lod_files_share_one_asset_group(self):
        base = self.detector.detect_file("SM_env_Rock_LOD0.fbx")
        lod1 = self.detector.detect_file("SM_Rock_LOD1.fbx")
        lod2 = self.detector.detect_file("SM_Rock_LOD2.fbx")

        groups = self.detector.group_assets([base, lod2, lod1])

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].mesh.lod_index, 0)
        self.assertEqual([item.lod_index for item in groups[0].lod_meshes], [2, 1])
        self.assertTrue(all(item.category == "Environment" for item in groups[0].lod_meshes))

    def test_unsuffixed_mesh_is_preferred_over_lod_zero(self):
        lod0 = self.detector.detect_file("SM_Rock_LOD0.fbx")
        base = self.detector.detect_file("SM_Rock.fbx")

        group = self.detector.group_assets([lod0, base])[0]

        self.assertIsNone(group.mesh.lod_index)

    def test_atlas_lods_are_keyed_by_clean_mesh_name(self):
        base = self.detector.detect_file("SM_env_Rock01-RockKit.fbx")
        lod1 = self.detector.detect_file("SM_Rock01-RockKit_LOD1.fbx")
        texture = self.detector.detect_file("T_RockKit_D.png")

        groups, remaining = self.detector.group_atlas_assets([base, lod1, texture])

        self.assertEqual(remaining, [])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].lod_meshes["SM_Rock01"][0].lod_index, 1)
        self.assertEqual(groups[0].lod_meshes["SM_Rock01"][0].category, "Environment")

    def test_lod_marker_is_only_removed_from_fbx_files(self):
        texture = self.detector.detect_file("T_Rock_LOD1.png")

        self.assertIsNone(texture.lod_index)


if __name__ == "__main__":
    unittest.main()
