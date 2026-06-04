from pathlib import Path
from asset_port.detector import AssetDetector
from asset_port.models import DetectedAsset
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
                category = "Weapon"
               
            elif "environment" in path_lower or "env" in path_lower:
                category = "Environment"
                
            elif "props" in path_lower or "prop" in path_lower:
                category = "Props"
                
            elif "character" in path_lower or "char" in path_lower:
                category = "Character"
                
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
            
        folder_path = f"/Game/{category}/{asset.base_name}"
        
        asset_path = f"/Game/{category}/{asset.base_name}/{prefix}{asset.base_name}{suffix}"        
            
        return folder_path, asset_path
        
    
            
     