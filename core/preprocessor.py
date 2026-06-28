import os
import re
from pathlib import Path

class ObsidianPreprocessor:
    VALID_CALLOUTS = {
        "note": "notecolor",
        "info": "infocolor",
        "todo": "notecolor",
        "tip": "tipcolor",
        "hint": "tipcolor",
        "important": "warningcolor",
        "warning": "warningcolor",
        "attention": "warningcolor",
        "caution": "warningcolor",
        "danger": "dangercolor",
        "error": "dangercolor",
        "bug": "dangercolor"
    }

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.vault_root = self._find_vault_root()
        self._vault_files_cache = None

    def process(self, text: str) -> str:
        text = self._normalize_headings(text)
        text = self._process_wikilinks(text)
        text = self._process_image_embeds_robust(text)
        text = self._process_standard_images(text)
        text = self._process_callouts_recursive(text)
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

        return img_name.replace("\\", "/")

    def _normalize_headings(self, text: str) -> str:
        text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
        text = re.sub(r'(^#{1,6}\s.*?[^\n])\n([^\n])', r'\1\n\n\2', text, flags=re.MULTILINE)
        return text

    def _process_wikilinks(self, text: str) -> str:
        text = re.sub(r'\[\[[^\]|#]+(?:#[^\]|]*)?\|([^\]]+)\]\]', r'\1', text)
        text = re.sub(r'\[\[([^\]|#]+)(?:#[^\]|]*)?\]\]', r'\1', text)
        return text

    def _process_image_embeds_robust(self, text: str) -> str:
        def repl(m: re.Match) -> str:
            inner = m.group(1)
            parts = inner.split('|')
            img_name = parts[0].strip()
            resolved_path = self._resolve_image_path(img_name)
            
            alt = img_name
            width = None
            
            for part in parts[1:]:
                part = part.strip()
                if part.isdigit():
                    width = part
                elif re.match(r'^\d+x\d+$', part):
                    width = part.split('x')[0]
                else:
                    alt = part
                    
            if width:
                return f"![{alt}]({resolved_path}){{width={width}px}}"
            return f"![{alt}]({resolved_path})"

        return re.sub(r'!\[\[([^\]]+)\]\]', repl, text)

    def _process_standard_images(self, text: str) -> str:
        def repl(m: re.Match) -> str:
            alt = m.group('alt')
            img_path = m.group('path')
            
            if img_path.startswith(("http://", "https://", "ftp://")):
                return m.group(0)
                
            resolved_path = self._resolve_image_path(img_path)
            return f"![{alt}]({resolved_path})"
            
        return re.sub(r'!\[(?P<alt>.*?)\]\((?P<path>[^)]+)\)', repl, text)

    def _process_callouts_recursive(self, text: str) -> str:
        lines = text.splitlines()
        processed_lines = []
        i = 0
        n = len(lines)
        
        while i < n:
            line = lines[i]
            m_start = re.match(r'^\s{0,3}>\s*\[!(?P<type>[a-zA-Z-]+)\]\s*(?P<title>.*)?', line)
            
            if m_start:
                raw_type = m_start.group('type').lower()
                c_type = self.VALID_CALLOUTS.get(raw_type, "defaultcolor")
                
                title_text = m_start.group('title').strip() if m_start.group('title') else ""
                if not title_text:
                    default_titles = {k: k.capitalize() for k in self.VALID_CALLOUTS.keys()}
                    callout_title = default_titles.get(raw_type, raw_type.capitalize())
                else:
                    callout_title = title_text
                    
                callout_lines = []
                i += 1
                
                while i < n:
                    next_line = lines[i]
                    m_cont = re.match(r'^\s{0,3}>\s?(?P<content>.*)', next_line)
                    
                    if m_cont:
                        callout_lines.append(m_cont.group('content'))
                        i += 1
                    elif next_line.strip() == "":
                        peek_index = i + 1
                        blockquote_continues = False
                        while peek_index < n:
                            peek_line = lines[peek_index]
                            if re.match(r'^\s{0,3}>\s?.*', peek_line):
                                blockquote_continues = True
                                break
                            elif peek_line.strip() == "":
                                peek_index += 1
                            else:
                                break
                        
                        if blockquote_continues:
                            for _ in range(peek_index - i):
                                callout_lines.append("")
                            i = peek_index
                        else:
                            break
                    else:
                        break
                
                cleaned_content = "\n".join(callout_lines)
                processed_content = self._process_callouts_recursive(cleaned_content)
                
                safe_title = callout_title.replace("{", "\\{").replace("}", "\\}")
                
                processed_lines.extend([
                    "",
                    "```{=latex}",
                    f"\\begin{{obscallout}}{{{c_type}}}{{{safe_title}}}",
                    "```",
                    "",
                    processed_content,
                    "",
                    "```{=latex}",
                    "\\end{{obscallout}}",
                    "```",
                    ""
                ])
            else:
                processed_lines.append(line)
                i += 1
                
        return "\n".join(processed_lines)