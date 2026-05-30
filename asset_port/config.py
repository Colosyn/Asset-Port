from dataclasses import dataclass, asdict
import json 
from pathlib import Path
@dataclass

class ImporterSettings():
    parent_material : str ="/Game/Python/M_Master"
    auto_create_mi : bool = True
    auto_assign_to_mesh : bool = True
    replace_existing : bool = False
    organize_asset : bool = True

def config_loader():
    
    settings = ImporterSettings()
    
    
    config_file = Path(__file__).parent.parent / "importer_config.json"
    
    if not config_file.exists():
        with open(config_file,"w") as file:
            json.dump(asdict(settings), file, indent=4)
            
            
    with open(config_file, "r") as file:
        data = json.load(file)
        
    
    settings = ImporterSettings(**data)
    
    return settings