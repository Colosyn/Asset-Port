from pathlib import Path
from asset_port.detector import AssetDetector 
from asset_port.models import DetectedAsset, AssetType, AtlasGroup
from typing import Optional
class AssetRouter():
    
   
    def get_folder_path(self, asset: DetectedAsset, category_override: Optional[str] = None):
        
        if category_override:
            category = category_override
 
        elif asset.category:
            category = asset.category
           
        else:
            file_path = asset.source_path
            
            path_lower = file_path.lower()
            
            if "weapon" in path_lower or "wpn" in path_lower:
                category = "Weapons"
               
            elif "environment" in path_lower or "env" in path_lower:
                category = "Environment"
                
            elif "prop" in path_lower or "prop" in path_lower:
                category = "Props"
                
            elif "character" in path_lower or "char" in path_lower:
                category = "Characters"
                
            elif "vehicle" in path_lower or "veh" in path_lower:
                category = "Vehicles"
                        
            elif "effect" in path_lower or "fx" in path_lower or "vfx" in path_lower:
                category = "Effects"
                
            else:
                category = "_Unsorted"
        
        if asset.prefix == "":
            prefix = asset.prefix
        
        else:
            prefix = f"{asset.prefix.upper()}_" 
                  
        if asset.suffix == "":
            suffix = asset.suffix
            
        else:
            suffix =f"_{asset.suffix}"      
            
        if asset.asset_type == AssetType.TEXTURE and asset.material_slot_name:
            folder_path = f"/Game/{category}/{asset.base_name}/Textures"
            asset_name = f"{prefix}{asset.base_name}_{asset.material_slot_name}{suffix}"
        else:    
            folder_path = f"/Game/{category}/{asset.base_name}"
            asset_name = f"{prefix}{asset.base_name}{suffix}"
            
        asset_path = f"{folder_path}/{asset_name}"        
            
        return folder_path, asset_path
        
    def get_atlas_folder_path(self, asset: DetectedAsset ,atlas_group: AtlasGroup, category_override: Optional[str] = None):
        if category_override:
            category = category_override
          
        elif atlas_group.category:
            category = atlas_group.category
                   
        else:
            file_path =asset.source_path
                    
            path_lower = file_path.lower()
                    
            if "weapon" in path_lower or "wpn" in path_lower:
                category = "Weapons"
                       
            elif "environment" in path_lower or "env" in path_lower:
                category = "Environment"
                        
            elif "prop" in path_lower or "prop" in path_lower:
                category = "Props"
                        
            elif "character" in path_lower or "char" in path_lower:
                category = "Characters"
                
            elif "vehicle" in path_lower or "veh" in path_lower:
                category = "Vehicles"
            
            elif "effect" in path_lower or "fx" in path_lower or "vfx" in path_lower:
                 category = "Effects"
                        
            else:
                category = "_Unsorted"
       
         
        folder_path = f"/Game/{category}/{atlas_group.kit_name}"
        asset_name = ""
        if asset.asset_type in (AssetType.STATIC_MESH, AssetType.SKELETAL_MESH):
            asset_name = asset.ue_asset_name
            
        elif asset.asset_type == AssetType.TEXTURE:
            prefix = f"{asset.prefix.upper()}_" if asset.prefix else ""
            suffix = f"_{asset.suffix}" if asset.suffix else ""
            asset_name = f"{prefix}{asset.base_name}{suffix}"
            
        asset_path = f"{folder_path}/{asset_name}"
        
        return folder_path, asset_path
        
        
            
        
    
            
     