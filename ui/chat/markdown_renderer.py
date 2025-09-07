# ui/chat/markdown_renderer.py
"""
Markdown Renderer for Chat Widget
Converts markdown text to HTML with syntax highlighting
"""
import re
from typing import Optional
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter


class MarkdownRenderer:
    """Custom markdown renderer with syntax highlighting"""
    
    def __init__(self):
        # Initialize markdown with extensions
        self.md = markdown.Markdown(
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
                'markdown.extensions.tables',
                'markdown.extensions.toc',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
                'markdown.extensions.smarty',
                'markdown.extensions.attr_list',
                'markdown.extensions.def_list',
                'markdown.extensions.footnotes',
                'markdown.extensions.abbr',
                'markdown.extensions.md_in_html'
            ],
            extension_configs={
                'markdown.extensions.codehilite': {
                    'css_class': 'highlight',
                    'linenums': False,
                    'guess_lang': True
                }
            }
        )
        
        # Code formatter for syntax highlighting
        self.formatter = HtmlFormatter(
            style='monokai',
            cssclass='highlight',
            noclasses=False
        )
        
        # Pre-compile regex patterns for better performance
        self.code_block_pattern = re.compile(
            r'```(\w+)?\n(.*?)```', 
            re.DOTALL
        )
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
        
    def render(self, text: str) -> str:
        """
        Render markdown text to HTML
        
        Args:
            text: Markdown formatted text
            
        Returns:
            HTML string with proper formatting
        """
        if not text:
            return ""
            
        # Pre-process code blocks for better syntax highlighting
        text = self._process_code_blocks(text)
        
        # Convert markdown to HTML
        html = self.md.convert(text)
        
        # Reset markdown instance for next use
        self.md.reset()
        
        # Wrap in container div with styling
        return self._wrap_html(html)
    
    def _process_code_blocks(self, text: str) -> str:
        """
        Process code blocks for syntax highlighting
        
        Args:
            text: Markdown text with code blocks
            
        Returns:
            Processed text with highlighted code blocks
        """
        def replace_code_block(match):
            language = match.group(1) or 'text'
            code = match.group(2)
            
            try:
                # Get appropriate lexer
                if language == 'text':
                    lexer = get_lexer_by_name('text')
                else:
                    lexer = get_lexer_by_name(language, stripall=True)
                
                # Highlight code
                highlighted = highlight(code, lexer, self.formatter)
                
                # Return as HTML block
                return f'\n<div class="code-block">{highlighted}</div>\n'
                
            except Exception:
                # Fallback to plain code block
                escaped_code = self._escape_html(code)
                return f'\n<pre><code class="language-{language}">{escaped_code}</code></pre>\n'
        
        return self.code_block_pattern.sub(replace_code_block, text)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (
            text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;')
        )
    
    def _wrap_html(self, html: str) -> str:
        """
        Wrap HTML in container with styling
        
        Args:
            html: Raw HTML content
            
        Returns:
            Wrapped HTML with CSS
        """
        css = self.get_css()
        
        return f"""
        <div class="markdown-body">
            <style>{css}</style>
            {html}
        </div>
        """
    
    def get_css(self) -> str:
        """
        Get CSS styles for markdown rendering
        
        Returns:
            CSS string
        """
        # Get syntax highlighting CSS
        highlight_css = self.formatter.get_style_defs('.highlight')
        
        # Custom markdown styles
        markdown_css = """
        .markdown-body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            word-wrap: break-word;
        }
        
        .markdown-body h1 {
            font-size: 2em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        
        .markdown-body h2 {
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        
        .markdown-body h3 {
            font-size: 1.25em;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        
        .markdown-body h4 {
            font-size: 1em;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        
        .markdown-body p {
            margin-top: 0;
            margin-bottom: 16px;
        }
        
        .markdown-body ul, .markdown-body ol {
            padding-left: 2em;
            margin-top: 0;
            margin-bottom: 16px;
        }
        
        .markdown-body li {
            margin-bottom: 0.25em;
        }
        
        .markdown-body blockquote {
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 0 0 16px 0;
        }
        
        .markdown-body code {
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }
        
        .markdown-body pre {
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 6px;
            margin-top: 0;
            margin-bottom: 16px;
        }
        
        .markdown-body pre code {
            padding: 0;
            margin: 0;
            background-color: transparent;
            border: 0;
        }
        
        .markdown-body .code-block {
            margin-bottom: 16px;
            border-radius: 6px;
            overflow: hidden;
        }
        
        .markdown-body .highlight {
            background: #272822;
            color: #f8f8f2;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }
        
        .markdown-body .highlight pre {
            margin: 0;
            padding: 0;
            background: transparent;
        }
        
        .markdown-body table {
            display: block;
            width: 100%;
            overflow: auto;
            border-spacing: 0;
            border-collapse: collapse;
            margin-bottom: 16px;
        }
        
        .markdown-body table th {
            font-weight: 600;
            padding: 6px 13px;
            border: 1px solid #dfe2e5;
            background-color: #f6f8fa;
        }
        
        .markdown-body table td {
            padding: 6px 13px;
            border: 1px solid #dfe2e5;
        }
        
        .markdown-body table tr {
            background-color: #fff;
            border-top: 1px solid #c6cbd1;
        }
        
        .markdown-body table tr:nth-child(2n) {
            background-color: #f6f8fa;
        }
        
        .markdown-body hr {
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: #e1e4e8;
            border: 0;
        }
        
        .markdown-body a {
            color: #0366d6;
            text-decoration: none;
        }
        
        .markdown-body a:hover {
            text-decoration: underline;
        }
        
        .markdown-body strong {
            font-weight: 600;
        }
        
        .markdown-body em {
            font-style: italic;
        }
        
        .markdown-body del {
            text-decoration: line-through;
        }
        """
        
        return highlight_css + markdown_css
    
    def render_plain_text(self, text: str) -> str:
        """
        Render plain text (escape HTML but preserve line breaks)
        
        Args:
            text: Plain text
            
        Returns:
            HTML-safe text with preserved formatting
        """
        if not text:
            return ""
            
        # Escape HTML
        text = self._escape_html(text)
        
        # Convert line breaks to <br>
        text = text.replace('\n', '<br>')
        
        return f'<div class="plain-text">{text}</div>'
