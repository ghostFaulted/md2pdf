import shutil
import subprocess
from typing import Dict, Tuple

def check_dependencies() -> Tuple[bool, Dict[str, bool], str]:
    dependencies = {
        "pandoc": False,
        "xelatex": False
    }
    
    for tool in dependencies.keys():
        if shutil.which(tool) is not None:
            dependencies[tool] = True

    missing_tools = [tool for tool, installed in dependencies.items() if not installed]
    
    error_msg = ""
    if missing_tools:
        error_msg = f"Missing required system tools: {', '.join(missing_tools)}.\n"
        
        if "pandoc" in missing_tools:
            error_msg += "- Pandoc is missing. Install via: winget install JohnMacFarlane.Pandoc\n"
        if "xelatex" in missing_tools:
            error_msg += "- XeLaTeX is missing. Install MiKTeX via: winget install MiKTeX.MiKTeX\n"
            
    is_ready = len(missing_tools) == 0
    
    if is_ready:
        try:
            result = subprocess.run(
                ["pandoc", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            version_line = result.stdout.split('\n')[0]
            print(f"System Check OK: Found {version_line}")
        except subprocess.SubprocessError:
            return False, dependencies, "Pandoc executable found, but failed to execute. Check system permissions."

    return is_ready, dependencies, error_msg

if __name__ == "__main__":
    ready, status, msg = check_dependencies()
    if not ready:
        print("SYSTEM CHECK FAILED:")
        print(msg)
    else:
        print("SYSTEM CHECK PASSED. All dependencies are available.")