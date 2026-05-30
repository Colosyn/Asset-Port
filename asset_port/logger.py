import unreal
from pathlib import Path
from asset_port.models import PipelineReport



def log_pipeline_report(report: PipelineReport, selected_path :str):
    
    unreal.log("===================================================")
    unreal.log(f"Scanned: {report.total_scanned} | Imported: {report.asset_import}")
    unreal.log(f"MIs Created: {report.mis_created} | MIs Linked: {report.mis_linked}")
    unreal.log("===================================================")
    if report.warnings:
        for warning in report.warnings:
            unreal.log_warning(f"Warning: {warning}")
        
    if report.errors:
        for error in report.errors:
            unreal.log_error(f"Errors : {error}")
            
            
    report_file_path = Path(selected_path) /  "assetport_report.txt"
    with open(report_file_path, "w") as f:
        f.write("AssetPort Import report\n")
        f.write(f"Scanned: {report.total_scanned}\n")
        f.write(f"Imported: {report.asset_import}\n")
        
        if report.warnings:
            for warning in report.warnings:
                f.write(f"Warnings: {warning}\n")
            
        if report.errors:
            for error in report.errors:
                f.write(f"Errors: {error}\n")
        
        