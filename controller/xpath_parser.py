import re
from pathlib import Path
from lark import Lark, UnexpectedInput

AXIS = {
    "self", "descendant", "next-sibling", "following",
    "child", "descendant-or-self", "following-sibling",
    "preceding", "parent", "ancestor", "previous-sibling",
    "ancestor-or-self", "preceding-sibling"
}

def detect_grammar(expression: str) -> str:
    """
    Return 'syntax' if any axis name appears as a whole word,
    otherwise return 'abbreviated'.
    """
    # Tokenize roughly by splitting on non-alphanumeric characters
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]*", expression)
    for tok in tokens:
        if tok in AXIS:
            return "syntax"
    return "abbreviated_syntax"


class XPathParser:
    def __init__(self):
        # Get the grammars from files in ../grammar
        base_path = Path(__file__).parent
        with open(base_path / "../grammar/syntax.lark", "r") as f:
            syntax = f.read()

        with open(base_path / "../grammar/abbreviated_syntax.lark", "r") as f:
            abbreviated_syntax = f.read()

        self._parsers = {
            "syntax": Lark(syntax, parser="earley", start="start"),
            "abbreviated_syntax": Lark(abbreviated_syntax, parser="earley", start="start")
        }

    def parse(self, expression: str):
        # Decide which grammar to use
        grammar_type = detect_grammar(expression)
        _parser = self._parsers[grammar_type]
        try:
            tree = _parser.parse(expression)
            return tree
        except UnexpectedInput as e:
            raise SyntaxError(f"Invalid XPath expression for {grammar_type} grammar: {e}")