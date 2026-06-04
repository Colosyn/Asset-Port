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
    EMISSIVE = "Emissive"
    OPACITY = "Opacity"
    ORM = "ORM"
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
    
@dataclass
class AssetGroup:
    base_name : str
    mesh : Optional[DetectedAsset] = None
    texture_list : list[DetectedAsset] = field(default_factory=list)
    category : Optional[str] = None
    folder_path : Optional[str] = None
    
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
    warnings : list[str] = field(default_factory=list)
    errors  : list[str] = field(default_factory=list)
    