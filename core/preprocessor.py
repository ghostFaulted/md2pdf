import os
import re
from pathlib import Path

class ObsidianPreprocessor:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.vault_root = self._find_vault_root()
        self._vault_files_cache = None

    def process(self, text: str) -> str:
        text = self._normalize_headings(text)
        text = self._process_wikilinks(text)
        text = self._process_image_embeds(text)
        text = self._process_standard_images(text)
        text = self._process_callouts(text)
        return text

    def _find_vault_root(self) -> Path | None:
        curr = self.base_dir.resolve()
        for parent in [curr] + list(curr.parents):
            if (parent / ".obsidian").is_dir():
                return parent
        return None

    def _get_vault_files(self) -> dict[str, Path]:
        if self._vault_files_cache is not None:
            return self._vault_files_cache
        
        self._vault_files_cache = {}
        if self.vault_root:
            try:
                for root, dirs, files in os.walk(self.vault_root):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for file in files:
                        self._vault_files_cache[file.lower()] = Path(root) / file
            except Exception:
                pass
        return self._vault_files_cache

    def _resolve_image_path(self, img_name: str) -> str:
        local_path = self.base_dir / img_name
        if local_path.is_file():
            return local_path.resolve().as_posix()

        if self.vault_root:
            files_map = self._get_vault_files()
            lookup_name = img_name.lower()
            if lookup_name in files_map:
                return files_map[lookup_name].resolve().as_posix()

        return img_name

    def _normalize_headings(self, text: str) -> str:
        text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
        text = re.sub(r'(^#{1,6}\s.*?[^\n])\n([^\n])', r'\1\n\n\2', text, flags=re.MULTILINE)
        return text

    def _process_wikilinks(self, text: str) -> str:
        text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
        text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
        return text

    def _process_image_embeds(self, text: str) -> str:
        def repl(m: re.Match) -> str:
            img_name = m.group(1)
            size = m.group(2)
            resolved_path = self._resolve_image_path(img_name)
            if size and size.isdigit():
                return f"![{img_name}]({resolved_path}){{width={size}px}}"
            return f"![{img_name}]({resolved_path})"

        return re.sub(r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', repl, text)

    def _process_standard_images(self, text: str) -> str:
        def repl(m: re.Match) -> str:
            alt = m.group('alt')
            img_path = m.group('path')
            
            if img_path.startswith(("http://", "https://", "ftp://")):
                return m.group(0)
                
            resolved_path = self._resolve_image_path(img_path)
            return f"![{alt}]({resolved_path})"
            
        return re.sub(r'!\[(?P<alt>.*?)\]\((?P<path>[^)]+)\)', repl, text)

    def _process_callouts(self, text: str) -> str:
        pattern = re.compile(
            r'^>\s*\[!(?P<type>[a-zA-Z-]+)\]\s*(?P<title>.*)?\n(?P<content>(?:^>.*\n?)*)',
            re.MULTILINE
        )
        
        def repl(m: re.Match) -> str:
            c_type = m.group('type').lower().strip()
            title = m.group('title').strip() if m.group('title') else c_type.capitalize()
            content = m.group('content')
            clean_content = re.sub(r'^>\s?', '', content, flags=re.MULTILINE)
            
            return (
                f"\n```{{=latex}}\n"
                f"\\begin{{obscallout}}{{{c_type}}}{{{title}}}\n"
                f"```\n\n"
                f"{clean_content.strip()}\n\n"
                f"```{{=latex}}\n"
                f"\\end{{obscallout}}\n"
                f"```\n"
            )

        return pattern.sub(repl, text)