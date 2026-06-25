import os
import sys
import tempfile
from pathlib import Path
from typing import Tuple, Dict, List, Optional

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

    def prepare(self, input_path: str, output_path: str, options: Dict[str, bool]) -> Tuple[bool, List[str] | str, Optional[str]]:
        input_file = Path(input_path)
        if not input_file.exists():
            return False, f"Error: Input file not found at {input_path}", None

        if not self.template_path.exists():
            return False, f"Error: Template not found at {self.template_path}", None

        work_dir = input_file.parent
        obsidian_mode = options.get("obsidian_mode", True)

        try:
            with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                raw_text = f.read()
            
            if obsidian_mode:
                preprocessor = ObsidianPreprocessor(work_dir)
                processed_text = preprocessor.process(raw_text)
                input_format = "markdown+hard_line_breaks"
            else:
                processed_text = raw_text
                input_format = "markdown"
                
        except Exception as e:
            return False, f"Preprocessing failed: {str(e)}", None

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".md", text=True)
        try:
            with os.fdopen(tmp_fd, 'w', encoding='utf-8') as tmp_file:
                tmp_file.write(processed_text)
                
            cmd = [
                "pandoc",
                "-f", input_format,
                tmp_path,
                "-o", output_path,
                "--pdf-engine=xelatex",
                f"--template={str(self.template_path)}",
                f"--resource-path={str(work_dir)}",
                "--syntax-highlighting=tango"
            ]
            if options.get("toc", False):
                cmd.append("--toc")
            if options.get("mainfont"):
                cmd.extend(["-V", f"mainfont={options['mainfont']}"])
            if options.get("fontsize"):
                cmd.extend(["-V", f"fontsize={options['fontsize']}"])

            return True, cmd, tmp_path

        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False, f"Unexpected preparation error: {str(e)}", None