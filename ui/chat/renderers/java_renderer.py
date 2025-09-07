# ui/chat/renderers/java_renderer.py
"""
Java code renderer
"""
from .base_renderer import BaseCodeRenderer


class JavaRenderer(BaseCodeRenderer):
    """Java code renderer"""
    
    def get_keywords(self):
        """Java keywords"""
        return [
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch',
            'char', 'class', 'const', 'continue', 'default', 'do', 'double',
            'else', 'enum', 'extends', 'final', 'finally', 'float', 'for',
            'goto', 'if', 'implements', 'import', 'instanceof', 'int',
            'interface', 'long', 'native', 'new', 'package', 'private',
            'protected', 'public', 'return', 'short', 'static', 'strictfp',
            'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
            'transient', 'try', 'void', 'volatile', 'while', 'var', 'yield',
            'record', 'sealed', 'non-sealed', 'permits'
        ]
    
    def get_builtin_functions(self):
        """Java standard library classes and methods"""
        return [
            'System', 'String', 'StringBuilder', 'StringBuffer', 'Integer',
            'Double', 'Float', 'Long', 'Short', 'Byte', 'Character', 'Boolean',
            'Object', 'Class', 'Math', 'Thread', 'Runnable', 'Exception',
            'RuntimeException', 'ArrayList', 'LinkedList', 'HashMap', 'HashSet',
            'TreeMap', 'TreeSet', 'Arrays', 'Collections', 'List', 'Set', 'Map',
            'Queue', 'Stack', 'Vector', 'Iterator', 'Comparator', 'Comparable',
            'File', 'FileReader', 'FileWriter', 'BufferedReader', 'BufferedWriter',
            'IOException', 'FileNotFoundException', 'Scanner', 'PrintWriter',
            'Random', 'Date', 'Calendar', 'SimpleDateFormat', 'LocalDate',
            'LocalTime', 'LocalDateTime', 'Duration', 'Period', 'Instant'
        ]
    
    def get_builtin_values(self):
        """Java built-in values"""
        return ['true', 'false', 'null']
    
    def get_comment_pattern(self):
        """Java comment pattern"""
        return '//'
