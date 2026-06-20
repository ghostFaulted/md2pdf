import re
from pathlib import Path

class ObsidianPreprocessor:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def process(self, text: str) -> str:
        text = self._normalize_headings(text)
        text = self._process_wikilinks(text)
        text = self._process_image_embeds(text)
        text = self._process_callouts(text)
        return text

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
            if size and size.isdigit():
                return f"![{img_name}]({img_name}){{width={size}px}}"
            return f"![{img_name}]({img_name})"

        return re.sub(r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', repl, text)

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