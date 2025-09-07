# ui/chat/renderers/__init__.py
"""
Language-specific code renderers for chat display
"""
from .base_renderer import BaseCodeRenderer
from .python_renderer import PythonRenderer
from .javascript_renderer import JavaScriptRenderer
from .typescript_renderer import TypeScriptRenderer
from .cpp_renderer import CppRenderer
from .java_renderer import JavaRenderer
from .csharp_renderer import CSharpRenderer
from .html_renderer import HtmlRenderer
from .css_renderer import CssRenderer
from .sql_renderer import SqlRenderer
from .markdown_renderer import MarkdownCodeRenderer

# Registry of available renderers
RENDERER_REGISTRY = {
    'python': PythonRenderer,
    'py': PythonRenderer,
    'python3': PythonRenderer,
    'javascript': JavaScriptRenderer,
    'js': JavaScriptRenderer,
    'typescript': TypeScriptRenderer,
    'ts': TypeScriptRenderer,
    'cpp': CppRenderer,
    'c++': CppRenderer,
    'c': CppRenderer,
    'java': JavaRenderer,
    'csharp': CSharpRenderer,
    'cs': CSharpRenderer,
    'c#': CSharpRenderer,
    'html': HtmlRenderer,
    'xml': HtmlRenderer,
    'css': CssRenderer,
    'scss': CssRenderer,
    'sass': CssRenderer,
    'sql': SqlRenderer,
    'mysql': SqlRenderer,
    'postgresql': SqlRenderer,
    'markdown': MarkdownCodeRenderer,
    'md': MarkdownCodeRenderer,
}

def get_renderer(language: str):
    """Get appropriate renderer for the given language"""
    language = language.lower() if language else ''
    renderer_class = RENDERER_REGISTRY.get(language, BaseCodeRenderer)
    return renderer_class()

__all__ = [
    'BaseCodeRenderer',
    'PythonRenderer',
    'JavaScriptRenderer',
    'TypeScriptRenderer',
    'CppRenderer',
    'JavaRenderer',
    'CSharpRenderer',
    'HtmlRenderer',
    'CssRenderer',
    'SqlRenderer',
    'MarkdownCodeRenderer',
    'get_renderer',
    'RENDERER_REGISTRY'
]
