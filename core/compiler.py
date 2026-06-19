import os
import sys
import tempfile
import subprocess
import traceback
from pathlib import Path
from typing import Tuple, Dict

from .preprocessor import ObsidianPreprocessor

class MarkdownCompiler:
    def __init__(self):
        try:
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                self.base_dir = Path(sys._MEIPASS)
            else:
                self.base_dir = Path(__file__).resolve().parent.parent
        except Exception:
            self.base_dir = Path(os.getcwd())
            
        self.template_path = self.base_dir / "templates" / "academic.tex"

    def compile(self, input_path: str, output_path: str, options: Dict[str, bool]) -> Tuple[bool, str]:
        input_file = Path(input_path)
        if not input_file.exists():
            return False, f"Error: Input file not found at {input_path}"

        if not self.template_path.exists():
            return False, f"Error: Template not found at {self.template_path}"

        work_dir = input_file.parent
        preprocessor = ObsidianPreprocessor(work_dir)

        try:
            with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                raw_text = f.read()
            processed_text = preprocessor.process(raw_text)
        except Exception as e:
            return False, f"Preprocessing failed: {str(e)}"

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".md", text=True)
        try:
            with os.fdopen(tmp_fd, 'w', encoding='utf-8') as tmp_file:
                tmp_file.write(processed_text)
                
            cmd = [
                "pandoc",
                tmp_path,
                "-o", output_path,
                "--pdf-engine=xelatex",
                f"--template={str(self.template_path)}",
                f"--resource-path={str(work_dir)}",
                "--highlight-style=tango",
                "-V", "lang=english"
            ]
            if options.get("toc", False):
                cmd.append("--toc")

            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                creationflags=creationflags
            )
            
            out = result.stdout.decode('utf-8', errors='replace')
            err = result.stderr.decode('utf-8', errors='replace')
            return True, f"{out}\n{err}".strip()

        except subprocess.CalledProcessError as e:
            err = e.stderr.decode('utf-8', errors='replace') if e.stderr else "No stderr output"
            error_msg = f"Pandoc/XeLaTeX Compilation Failed (Exit code {e.returncode}):\n{err}"
            return False, error_msg
        except Exception as e:
            return False, f"Unexpected compilation error:\n{traceback.format_exc()}"
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass