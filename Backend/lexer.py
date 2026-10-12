import os
import sys

import ply.lex as lex
from collections import Counter


# ============================================================
# C KEYWORDS
# ============================================================

reserved = {
    'auto': 'AUTO',
    'break': 'BREAK',
    'case': 'CASE',
    'char': 'CHAR',
    'const': 'CONST',
    'continue': 'CONTINUE',
    'default': 'DEFAULT',
    'do': 'DO',
    'double': 'DOUBLE',
    'else': 'ELSE',
    'enum': 'ENUM',
    'extern': 'EXTERN',
    'float': 'FLOAT',
    'for': 'FOR',
    'goto': 'GOTO',
    'if': 'IF',
    'inline': 'INLINE',
    'int': 'INT',
    'long': 'LONG',
    'register': 'REGISTER',
    'restrict': 'RESTRICT',
    'return': 'RETURN',
    'short': 'SHORT',
    'signed': 'SIGNED',
    'sizeof': 'SIZEOF',
    'static': 'STATIC',
    'struct': 'STRUCT',
    'switch': 'SWITCH',
    'typedef': 'TYPEDEF',
    'union': 'UNION',
    'unsigned': 'UNSIGNED',
    'void': 'VOID',
    'volatile': 'VOLATILE',
    'while': 'WHILE'
}


# ============================================================
# TOKEN LIST
# ============================================================

tokens = [
    # Identifiers and constants
    'IDENTIFIER',
    'INTEGER',
    'FLOATING',
    'CHARACTER',
    'STRING',
    'PREPROCESSOR',

    # Operators
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'MOD',

    'ASSIGN',

    'EQUAL',
    'NOT_EQUAL',
    'LESS',
    'GREATER',
    'LESS_EQUAL',
    'GREATER_EQUAL',

    'AND',
    'OR',
    'NOT',

    'BIT_AND',
    'BIT_OR',
    'BIT_XOR',
    'BIT_NOT',

    'LEFT_SHIFT',
    'RIGHT_SHIFT',

    'INCREMENT',
    'DECREMENT',

    'PLUS_ASSIGN',
    'MINUS_ASSIGN',
    'TIMES_ASSIGN',
    'DIVIDE_ASSIGN',
    'MOD_ASSIGN',

    'AND_ASSIGN',
    'OR_ASSIGN',
    'XOR_ASSIGN',

    'ARROW',

    # Delimiters
    'LPAREN',
    'RPAREN',
    'LBRACE',
    'RBRACE',
    'LBRACKET',
    'RBRACKET',

    'COMMA',
    'SEMICOLON',
    'COLON',
    'DOT'
]

tokens += list(reserved.values())


# ============================================================
# TOKEN REGULAR EXPRESSIONS
#
# IMPORTANT:
# Multi-character operators are defined before their
# single-character versions.
# ============================================================

t_INCREMENT = r'\+\+'
t_DECREMENT = r'--'

t_PLUS_ASSIGN = r'\+='
t_MINUS_ASSIGN = r'-='
t_TIMES_ASSIGN = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_MOD_ASSIGN = r'%='

t_EQUAL = r'=='
t_NOT_EQUAL = r'!='
t_LESS_EQUAL = r'<='
t_GREATER_EQUAL = r'>='

t_AND = r'&&'
t_OR = r'\|\|'

t_LEFT_SHIFT = r'<<'
t_RIGHT_SHIFT = r'>>'

t_AND_ASSIGN = r'&='
t_OR_ASSIGN = r'\|='
t_XOR_ASSIGN = r'\^='

t_ARROW = r'->'


# ============================================================
# SINGLE CHARACTER OPERATORS
# ============================================================

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'

t_ASSIGN = r'='

t_LESS = r'<'
t_GREATER = r'>'

t_NOT = r'!'

t_BIT_AND = r'&'
t_BIT_OR = r'\|'
t_BIT_XOR = r'\^'
t_BIT_NOT = r'~'


# ============================================================
# DELIMITERS
# ============================================================

t_LPAREN = r'\('
t_RPAREN = r'\)'

t_LBRACE = r'\{'
t_RBRACE = r'\}'

t_LBRACKET = r'\['
t_RBRACKET = r'\]'

t_COMMA = r','
t_SEMICOLON = r';'
t_COLON = r':'
t_DOT = r'\.'


# ============================================================
# FLOATING POINT NUMBERS
# ============================================================

def t_FLOATING(t):
    r'((\d+\.\d*)|(\.\d+))([eE][+-]?\d+)?[fFlL]?|\d+[eE][+-]?\d+[fFlL]?'
    return t


# ============================================================
# INTEGER NUMBERS
# ============================================================

def t_INTEGER(t):
    r'0[xX][0-9a-fA-F]+|0[bB][01]+|0[0-7]*|\d+'
    return t


# ============================================================
# CHARACTER CONSTANT
# ============================================================

def t_CHARACTER(t):
    r"""'(\\.|[^\\'])'"""
    return t


# ============================================================
# STRING LITERAL
# ============================================================

def t_STRING(t):
    r'''"(\\.|[^\\"])*"'''
    return t


# ============================================================
# SINGLE LINE COMMENT
# ============================================================

def t_COMMENT_SINGLE(t):
    r'//[^\n]*'
    pass


# ============================================================
# MULTI LINE COMMENT
# ============================================================

def t_COMMENT_MULTI(t):
    r'/\*([^*]|\*+[^*/])*\*+/'
    t.lexer.lineno += t.value.count('\n')
    pass


# ============================================================
# PREPROCESSOR DIRECTIVE
# ============================================================

def t_PREPROCESSOR(t):
    r'\#include[^\n]*'
    return t


# ============================================================
# IDENTIFIER / KEYWORD
# ============================================================

def t_IDENTIFIER(t):
    r'[A-Za-z_][A-Za-z0-9_]*'

    if t.value in reserved:
        t.type = reserved[t.value]

    return t


# ============================================================
# NEWLINE
# ============================================================

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


# ============================================================
# IGNORE WHITESPACE
# ============================================================

t_ignore = ' \t\r'


# ============================================================
# ERROR HANDLER
# ============================================================

lexical_errors = []


def t_error(t):

    error = (
        f"Line {t.lexer.lineno}: "
        f"Invalid character '{t.value[0]}'"
    )

    lexical_errors.append(error)

    t.lexer.skip(1)


# ============================================================
# BUILD LEXER
# ============================================================

lexer = lex.lex()


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_header(input_file="input.c"):

    display_name = os.path.basename(input_file)

    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " C LEXICAL   ANALYZER - PLY".center(78) + "║")
    print("║" + " Dynamic Token Analysis".center(78) + "║")
    print("╠" + "═" * 78 + "╣")
    print("║" + f" Input File : {display_name}".ljust(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()


def print_tokens(token_list):

    if not token_list:
        print("No tokens found.")
        return

    # Convert everything to strings
    rows = []

    for index, token in enumerate(token_list, start=1):

        rows.append([
            str(index),
            str(token.lineno),
            token.type,
            str(token.value)
        ])

    headers = [
        "No.",
        "Line",
        "Token Type",
        "Lexeme"
    ]

    # Dynamic column width
    widths = []

    for i in range(len(headers)):

        maximum = len(headers[i])

        for row in rows:
            maximum = max(maximum, len(row[i]))

        widths.append(maximum + 2)

    total_width = sum(widths) + len(widths) + 1

    print("┌" + "─" * total_width + "┐")

    # Header
    header_line = "│"

    for i, header in enumerate(headers):

        header_line += (
            f" {header:<{widths[i] - 1}}│"
        )

    print(header_line)

    print(
        "├" +
        "─" * total_width +
        "┤"
    )

    # Rows
    for row in rows:

        line = "│"

        for i, value in enumerate(row):

            line += (
                f" {value:<{widths[i] - 1}}│"
            )

        print(line)

    print(
        "└" +
        "─" * total_width +
        "┘"
    )


# ============================================================
# TOKEN CATEGORY
# ============================================================

def get_category(token_type):

    if token_type in reserved.values():
        return "Keyword"

    if token_type == "ID":
        return "Identifier"

    if token_type in {
        "INTEGER",
        "FLOATING",
        "CHARACTER",
        "STRING"
    }:
        return "Constant"

    if token_type in {
        "PLUS",
        "MINUS",
        "TIMES",
        "DIVIDE",
        "MOD",
        "ASSIGN",
        "EQUAL",
        "NOT_EQUAL",
        "LESS",
        "GREATER",
        "LESS_EQUAL",
        "GREATER_EQUAL",
        "AND",
        "OR",
        "NOT",
        "BIT_AND",
        "BIT_OR",
        "BIT_XOR",
        "BIT_NOT",
        "LEFT_SHIFT",
        "RIGHT_SHIFT",
        "INCREMENT",
        "DECREMENT",
        "PLUS_ASSIGN",
        "MINUS_ASSIGN",
        "TIMES_ASSIGN",
        "DIVIDE_ASSIGN",
        "MOD_ASSIGN",
        "AND_ASSIGN",
        "OR_ASSIGN",
        "XOR_ASSIGN",
        "ARROW"
    }:
        return "Operator"

    if token_type == "PREPROCESSOR":
        return "Preprocessor"

    return "Delimiter"


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(token_list):

    categories = Counter()

    for token in token_list:

        category = get_category(token.type)

        categories[category] += 1

    print()
    print("╔" + "═" * 45 + "╗")
    print("║" + " LEXICAL ANALYSIS SUMMARY".center(45) + "║")
    print("╠" + "═" * 45 + "╣")

    print(
        f"║  Total Tokens       : "
        f"{len(token_list):<20}║"
    )

    print(
        f"║  Keywords           : "
        f"{categories['Keyword']:<20}║"
    )

    print(
        f"║  Identifiers        : "
        f"{categories['Identifier']:<20}║"
    )

    print(
        f"║  Constants          : "
        f"{categories['Constant']:<20}║"
    )

    print(
        f"║  Operators          : "
        f"{categories['Operator']:<20}║"
    )

    print(
        f"║  Delimiters         : "
        f"{categories['Delimiter']:<20}║"
    )

    print(
        f"║  Preprocessor       : "
        f"{categories['Preprocessor']:<20}║"
    )

    print(
        f"║  Lexical Errors     : "
        f"{len(lexical_errors):<20}║"
    )

    print("╚" + "═" * 45 + "╝")


# ============================================================
# ERROR DISPLAY
# ============================================================

def print_errors():

    if not lexical_errors:

        print()
        print("✓ No lexical errors found.")

        return

    print()
    print("╔" + "═" * 70 + "╗")
    print("║" + " LEXICAL ERRORS".center(70) + "║")
    print("╠" + "═" * 70 + "╣")

    for error in lexical_errors:

        print("║ " + error.ljust(68) + "║")

    print("╚" + "═" * 70 + "╝")


# ============================================================
# MAIN
# ============================================================

def _configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main():

    _configure_stdio()

    lexer_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(lexer_dir, "input.c")

    if len(sys.argv) >= 2:
        filename = os.path.abspath(sys.argv[1])
    else:
        filename = default_input

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            source_code = file.read()

    except FileNotFoundError:

        print()
        print(f"ERROR: {os.path.basename(filename)} was not found.")
        print()
        print(f"Looked for: {filename}")

        return

    except OSError as exc:

        print()
        print(f"ERROR: Could not read {filename}")
        print(str(exc))

        return

    # Reset lexer state
    lexer.lineno = 1

    # Clear previous errors
    lexical_errors.clear()

    # Give source code to PLY
    lexer.input(source_code)

    # Collect tokens dynamically
    token_list = []

    while True:

        token = lexer.token()

        if token is None:
            break

        token_list.append(token)

    # Display
    print_header(filename)

    print_tokens(token_list)

    print_statistics(token_list)

    print_errors()

    print()
    print("✓ Lexical analysis completed.")


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    main()