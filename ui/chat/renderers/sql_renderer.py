# ui/chat/renderers/sql_renderer.py
"""
SQL code renderer
"""
from .base_renderer import BaseCodeRenderer


class SqlRenderer(BaseCodeRenderer):
    """SQL code renderer"""
    
    def get_keywords(self):
        """SQL keywords"""
        return [
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT',
            'OUTER', 'FULL', 'ON', 'AS', 'INSERT', 'INTO', 'VALUES',
            'UPDATE', 'SET', 'DELETE', 'CREATE', 'TABLE', 'DATABASE',
            'DROP', 'ALTER', 'ADD', 'COLUMN', 'PRIMARY', 'KEY', 'FOREIGN',
            'REFERENCES', 'INDEX', 'UNIQUE', 'NOT', 'NULL', 'DEFAULT',
            'AUTO_INCREMENT', 'ORDER', 'BY', 'GROUP', 'HAVING', 'ASC',
            'DESC', 'LIMIT', 'OFFSET', 'UNION', 'ALL', 'DISTINCT', 'AND',
            'OR', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS', 'CASE', 'WHEN',
            'THEN', 'ELSE', 'END', 'CAST', 'CONVERT', 'IF', 'IFNULL',
            'COALESCE', 'NULLIF', 'BEGIN', 'COMMIT', 'ROLLBACK', 'TRANSACTION',
            'TRIGGER', 'PROCEDURE', 'FUNCTION', 'VIEW', 'WITH', 'RECURSIVE',
            'PARTITION', 'OVER', 'ROW_NUMBER', 'RANK', 'DENSE_RANK'
        ]
    
    def get_builtin_functions(self):
        """SQL functions"""
        return [
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'FLOOR', 'CEIL',
            'ABS', 'SQRT', 'POWER', 'LENGTH', 'CHAR_LENGTH', 'UPPER', 'LOWER',
            'TRIM', 'LTRIM', 'RTRIM', 'REPLACE', 'SUBSTRING', 'SUBSTR',
            'CONCAT', 'CONCAT_WS', 'DATE', 'TIME', 'DATETIME', 'TIMESTAMP',
            'YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'SECOND', 'NOW',
            'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP', 'DATE_ADD',
            'DATE_SUB', 'DATEDIFF', 'DATE_FORMAT', 'STR_TO_DATE', 'RAND',
            'UUID', 'MD5', 'SHA1', 'SHA2', 'HEX', 'UNHEX', 'ENCRYPT',
            'DECRYPT', 'COMPRESS', 'UNCOMPRESS', 'JSON_EXTRACT', 'JSON_SET',
            'JSON_OBJECT', 'JSON_ARRAY', 'JSON_VALID'
        ]
    
    def get_builtin_values(self):
        """SQL values"""
        return ['TRUE', 'FALSE', 'NULL']
    
    def get_comment_pattern(self):
        """SQL comment pattern"""
        return '--'
    
    def render_line(self, cursor, line, line_number=0):
        """Enhanced SQL rendering (case-insensitive)"""
        # Preserve indentation
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0:
            cursor.insertText(' ' * leading_spaces, self.code_format)
            line = line.lstrip()
        
        # Check for comments
        if '--' in line:
            comment_pos = line.index('--')
            self.render_sql_tokens(cursor, line[:comment_pos])
            cursor.insertText(line[comment_pos:], self.comment_format)
        else:
            self.render_sql_tokens(cursor, line)
    
    def render_sql_tokens(self, cursor, text):
        """Render SQL tokens with case-insensitive keyword matching"""
        if not text:
            return
        
        keywords = self.get_keywords()
        functions = self.get_builtin_functions()
        values = self.get_builtin_values()
        
        # Tokenize
        import re
        tokens = re.findall(r"('[^']*'|\b\w+\b|\S)", text)
        
        for token in tokens:
            upper_token = token.upper()
            if token.startswith("'") and token.endswith("'"):
                # String literal
                cursor.insertText(token, self.string_format)
            elif upper_token in keywords:
                # Keyword (case-insensitive)
                cursor.insertText(token, self.keyword_format)
            elif upper_token in functions:
                # Function (case-insensitive)
                cursor.insertText(token, self.builtin_format)
            elif upper_token in values:
                # Value (case-insensitive)
                cursor.insertText(token, self.builtin_format)
            elif token.isdigit() or re.match(r'^\d+\.\d*$', token):
                # Number
                cursor.insertText(token, self.number_format)
            else:
                # Default (table names, column names, etc.)
                cursor.insertText(token, self.code_format)
