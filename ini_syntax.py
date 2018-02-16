# syntax.py

# This is a companion file to gexync.py

# based on https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting

from PyQt4.QtCore import QRegExp
from PyQt4.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter

def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'operator': format('red'),
    'string': format('magenta'),
    'comment': format('#6C8A70', 'italic'),
    'key': format('#008AFF'),
    'numbers': format('brown'),
    'section': format('black', 'bold'),
}

class IniHighlighter (QSyntaxHighlighter):
    # Python braces
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        rules = [
            (r'=', 0, STYLES['operator']),
            (r'\b[YN]\b', 0, STYLES['numbers']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # Numeric literals
            (r'\b[+-]?[0-9]+\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            (r'^\[.+\]', 0, STYLES['section']),

            (r'^[a-zA-Z0-9_-]+\s?=', 0, STYLES['key']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)
