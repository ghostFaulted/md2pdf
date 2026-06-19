import os
import tempfile
import subprocess
from pathlib import Path
from typing import Tuple, Dict
from .preprocessor import ObsidianPreprocessor

class MarkdownCompiler:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
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
            with open(input_file, 'r', encoding='utf-8') as f:
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
                "--highlight-style=tango"
            ]

            if options.get("toc", False):
                cmd.append("--toc")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            
            log_output = result.stdout + "\n" + result.stderr
            return True, log_output.strip()

        except subprocess.CalledProcessError as e:
            error_msg = f"Pandoc/XeLaTeX Compilation Failed (Exit code {e.returncode}):\n{e.stderr}"
            return False, error_msg
        except Exception as e:
            return False, f"Unexpected compilation error: {str(e)}"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m core.compiler <input.md> <output.pdf>")
    else:
        compiler = MarkdownCompiler()
        success, log = compiler.compile(sys.argv[1], sys.argv[2], {"toc": True})
        if success:
            print("SUCCESS:\n", log)
        else:
            print("ERROR:\n", log)