import ply.lex as lex
import ply.yacc as yacc
import unicodedata

# ============================================================
# AST nodes (ETOL)
# ============================================================

class Expr:
    def __init__(self):
        self.satisfying_states = set()
        self.constraints = None

class Unary(Expr):
    def __init__(self, op: str, operand: Expr):
        super().__init__()
        self.op = op
        self.operand = operand
    def __repr__(self):
        return f"{self.op}({self.operand})"

class Binary(Expr):
    def __init__(self, op: str, left: Expr, right: Expr):
        super().__init__()
        self.op = op  # '&' '|' '->' 'U' 'R'
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class AtomicProp(Expr):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name

class Freeze(Expr):
    """Freeze operator: j . phi"""
    def __init__(self, clock_name: str, formula: Expr):
        super().__init__()
        self.clock_name = clock_name
        self.formula = formula
    def __repr__(self):
        return f"{self.clock_name}.({self.formula})"

class SimpleTimeExpr(Expr):
    """Clock constraint like x<=4, j=100, y>=15 ..."""
    def __init__(self, clock: str, rel: str, const: int):
        super().__init__()
        self.clock = clock
        self.rel = rel
        self.const = const
        self.constraints = (clock, rel, const)
    def __repr__(self):
        return f"{self.clock}{self.rel}{self.const}"
    def __str__(self):
        return f"{self.clock}{self.rel}{self.const}"

class OpacityPath(Expr):
    """
    Opacity operator applied to a path subformula:
      OE( phi U psi ), OE( phi R psi )
      OA( phi U psi ), OA( phi R psi )
    """
    def __init__(self, op: str, path_formula: Expr):
        super().__init__()
        self.op = op  # 'OE' or 'OA'
        self.path_formula = path_formula
    def __repr__(self):
        return f"{self.op}({self.path_formula})"


# ============================================================
# Lexer
# ============================================================

reserved = {
    'implies': 'IMPLIES',

    # Opacity operators
    'OE': 'OP_EXISTS', 'oe': 'OP_EXISTS',
    'OA': 'OP_FORALL', 'oa': 'OP_FORALL',
    'BigCircExists': 'OP_EXISTS',
    'BigCircForall': 'OP_FORALL',

    # IMPORTANT: make U/R keywords so they don't get tokenized as PROP
    'U': 'UNTIL', 'until': 'UNTIL',
    'R': 'RELEASE', 'release': 'RELEASE',

    # True constant
    'T': 'TOP', 'true': 'TOP',
}

tokens = (
    'LPAREN', 'RPAREN',
    'AND', 'OR', 'NOT', 'IMPLIES',
    'UNTIL', 'RELEASE',
    'PROP',
    'OP_EXISTS', 'OP_FORALL',
    'LEQ', 'GEQ', 'GREATER', 'LESS', 'EQ',
    'CONST',
    'DOT',
    'TOP',
)

t_LPAREN   = r'\('
t_RPAREN   = r'\)'
t_AND      = r'&&|\&|and'
t_OR       = r'\|\||\||or'
t_NOT      = r'!|not'
t_IMPLIES  = r'->|implies'

# relations
t_LEQ      = r'\<\='
t_GEQ      = r'\>\='
t_EQ       = r'='
t_GREATER  = r'\>'
t_LESS     = r'\<'

t_CONST    = r'\d+'
t_DOT      = r'\.'

t_ignore = ' \t\r\n'

precedence = (
    ('right', 'IMPLIES'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
)

def t_PROP(t):
    r'[A-Za-z_]+\w*'
    t.type = reserved.get(t.value, 'PROP')
    return t

def t_error(t):
    t.lexer.skip(1)

lexer = lex.lex()

# ============================================================
# Parser (ETOL)
# ============================================================

def p_expression_binary(p):
    '''expression : expression AND expression
                  | expression OR expression
                  | expression IMPLIES expression'''
    p[0] = Binary(p[2], p[1], p[3])

def p_expression_not(p):
    '''expression : NOT expression'''
    p[0] = Unary(p[1], p[2])

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_top(p):
    '''expression : TOP'''
    p[0] = AtomicProp("T")  # treat as always-true atom; checker can special-case if desired

def p_expression_atomic(p):
    '''expression : PROP'''
    p[0] = AtomicProp(p[1])

# -----------------------------
# Freeze: j . phi
# -----------------------------
def p_expression_freeze(p):
    '''expression : PROP DOT expression'''
    p[0] = Freeze(p[1], p[3])

# -----------------------------
# Clock constraints: x<=10, j=100, y>=15, ...
# -----------------------------
def p_expression_time(p):
    '''expression : PROP LEQ CONST
                  | PROP LESS CONST
                  | PROP GEQ CONST
                  | PROP GREATER CONST
                  | PROP EQ CONST'''
    p[0] = SimpleTimeExpr(p[1], p[2], int(p[3]))

# -----------------------------
# Opacity operators: OE(...) / OA(...)
#   OE(phi U psi), OE(phi R psi)
#   OA(phi U psi), OA(phi R psi)
# -----------------------------
def p_expression_opacity(p):
    '''expression : OP_EXISTS LPAREN expression UNTIL expression RPAREN
                  | OP_EXISTS LPAREN expression RELEASE expression RPAREN
                  | OP_FORALL LPAREN expression UNTIL expression RPAREN
                  | OP_FORALL LPAREN expression RELEASE expression RPAREN
    '''
    # Determine which opacity operator
    op = 'OE' if p.slice[1].type == 'OP_EXISTS' else 'OA'

    # Determine path connective (UNTIL/RELEASE)
    path_op = 'U' if p.slice[4].type == 'UNTIL' else 'R'
    path = Binary(path_op, p[3], p[5])

    p[0] = OpacityPath(op, path)

def p_error(p):
    raise SyntaxError(f"Syntax error at token={p.type if p else None}, value={p.value if p else None}")

parser = yacc.yacc(debug=False)

# ============================================================
# Public API
# ============================================================

def get_lexer():
    return lexer

def do_parsingETOL(formula: str):
    """
    Parse an ETOL formula string and return the AST.
    Examples:
      - j.OE(T U cash)
      - j.OA(!C U (E & j=100))
      - OE(!cash R balance)
      - j>=15 & !cash
    """
    if not isinstance(formula, str):
        return None
    s = unicodedata.normalize('NFKC', formula)
    s = s.replace('\ufeff', '').replace('\u00A0', ' ')
    s = ' '.join(s.strip().split())
    return parser.parse(s, lexer=lexer)

def verifyETOL(token_name: str, string: str) -> bool:
    """
    Return True if token_name appears in the token stream of string.
    Example: verifyETOL('OP_EXISTS', 'j.OE(T U cash)') -> True
    """
    sanitized = str(string)
    lexer.input(sanitized)
    for tok in lexer:
        if tok.type == token_name:
            return True
    return False