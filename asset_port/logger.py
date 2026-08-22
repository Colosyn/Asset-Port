import unreal
from pathlib import Path
from asset_port.models import PipelineReport



def log_pipeline_report(report: PipelineReport, selected_path :str, dry_run = False):
    if dry_run:
        unreal.log("===================================================")
        unreal.log(f"Scanned: {report.total_scanned}")
        unreal.log(f"would create MIs : {report.mis_created}")
        unreal.log(f"Atlas Groups: {report.atlas_group_found}")
        unreal.log("===================================================")
        if report.warnings:
            for warning in report.warnings:
                unreal.log_warning(f"Warning: {warning}")
        
        if report.errors:
            for error in report.errors:
                unreal.log_error(f"Errors : {error}")  
    else:
        unreal.log("===================================================")
        unreal.log(f"Scanned: {report.total_scanned} | Imported: {report.asset_import}")
        unreal.log(f"MIs Created: {report.mis_created} | MIs Linked: {report.mis_linked}")
        unreal.log(f"Atlas Groups: {report.atlas_group_found}")
        unreal.log("===================================================")
        if report.warnings:
            for warning in report.warnings:
                unreal.log_warning(f"Warning: {warning}")
        
        if report.errors:
            for error in report.errors:
                unreal.log_error(f"Errors : {error}")
            
    if dry_run:
        preview_file_path = Path(selected_path) / "assetport_preview_report.txt"
        with open(preview_file_path, "w") as f:
            f.write("AssetPort Preview Report\n")
            f.write(f"Scanned: {report.total_scanned}\n")
            
            if report.warnings:
                for warning in report.warnings:
                    f.write(f"Warnigns: {warning}\n")
                    
            if report.errors:
                for error in report.errors:
                    f.write(f"Error: {error}\n")
        
    else:        
        report_file_path = Path(selected_path) /  "assetport_report.txt"
        with open(report_file_path, "w") as f:
            f.write("AssetPort Import report\n")
            f.write(f"Scanned: {report.total_scanned}\n")
            f.write(f"Imported: {report.asset_import}\n")
            f.write(f"Atlas Meshes imported: {report.atlas_meshes_imported}\n")
        
            if report.warnings:
                for warning in report.warnings:
                    f.write(f"Warnings: {warning}\n")
            
            if report.errors:
                for error in report.errors:
                    f.write(f"Errors: {error}\n")
        
        