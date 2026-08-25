from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class AssetType(Enum):
    STATIC_MESH = "StaticMesh"
    SKELETAL_MESH = "SkeletalMesh"
    TEXTURE = "Texture"
    ANIMATION = "Animation"
    UNKNOWN = "Unknown"
    
    
class TextureSlot(Enum):
    BASE_COLOUR = "BaseColour"
    NORMAL = "Normal"
    ROUGHNESS = "Roughness"
    METALLIC = "Metallic"
    AO = "AmbientOcclusion"
    CAVITY = "Cavity"
    EMISSIVE = "Emissive"
    SPECULAR = "Specular"
    GLOSS = "Gloss"
    TRANSLUCENCY = "Translucency"
    OPACITY = "Opacity"
    OPACITY_MASK = "OpacityMask"
    ORM = "ORM"
    RMA = "RMA"
    HEIGHT = "Height"
    UNKNOWN = "Unknown"
    

@dataclass
class DetectedAsset:
    filename : str
    source_path : str
    prefix : str
    base_name : str
    suffix : Optional[str]
    asset_type : AssetType
    texture_slot : Optional[TextureSlot] 
    extension : str
    category : Optional[str] = None
    ue_path : Optional[str]= None
    has_alpha : bool = False
    material_slot_name : Optional[str] = None
    udim_tile : Optional[str] = None
    tile_count : int = 1
    kit_name: Optional[str] = None
    ue_asset_name: Optional[str] = None
    lod_index: Optional[int] = None
    @property
    def is_udim(self) -> bool:
        return self.udim_tile is not None
    
    @property
    def is_udim_primary(self) -> bool:
        return self.udim_tile == "1001"
    
@dataclass
class AssetGroup:
    base_name : str
    mesh : Optional[DetectedAsset] = None
    texture_list : list[DetectedAsset] = field(default_factory=list)
    material_slots : dict[str, list[DetectedAsset]] = field(default_factory=dict)
    category : Optional[str] = None
    folder_path : Optional[str] = None
    lod_meshes : list[DetectedAsset] = field(default_factory=list)
    @property
    def is_multi_material(self) -> bool:
        return len(self.material_slots) > 1
 
@dataclass
class AtlasGroup:
    kit_name: str
    mesh_list: list[DetectedAsset] = field(default_factory=list)
    texture_list: list[DetectedAsset] = field(default_factory=list)
    category : Optional[str] = None
    folder_path: Optional[str] = None   
    lod_meshes: dict[str, list[DetectedAsset]] = field(default_factory=dict)
    
    @property
    def mesh_count(self) -> int:
        return len(self.mesh_list)
    
        
@dataclass
class ImportResult:
    asset : DetectedAsset
    success : bool
    ue_path : Optional[str] = None
    error : Optional[str] = None
    
@dataclass
class MaterialBuildResult:
    base_name : str   
    mi_path : Optional[str] = None
    texture_assigned : dict[str, str] = field(default_factory=dict)
    mesh_linked : Optional[str] = None
    success : bool = False
    errors : list[str] = field(default_factory=list)
    
@dataclass
class PipelineReport:
    total_scanned : int = 0
    groups_found : int = 0
    asset_import : int = 0
    asset_failed : int =0
    mis_created : int =0
    mis_linked : int = 0
    atlas_group_found : int =0
    atlas_meshes_imported : int =0
    lods_imported : int = 0
    warnings : list[str] = field(default_factory=list)
    errors  : list[str] = field(default_factory=list)
