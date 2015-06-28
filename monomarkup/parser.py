import re

class Pattern(object):
    def __init__(self, name, regex, actions=None):
        self.name = name
        self.regex = re.compile(regex) if isinstance(regex, basestring) else regex
        self.actions = actions

    def __repr__(self):
        return "Pattern(%r, %r, %r)" % (self.name, self.regex.pattern, self.actions)

class Token(object):
    def __init__(self, name, value, start=None, end=None):
        self.name = name
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return u'Token(%r, %r)' % (self.name, self.value)

class PushdownLexer(object):
    def __init__(self, spec):
        self.spec = spec

    def lex(self, source):
        stack = ["default"]
        position = 0
        result = []
        while position < len(source):
            # Go through each regex associated with current state in order
            for pattern in self.spec[stack[-1]]:
                match = pattern.regex.match(source, position)
                if match:
                    result.append(Token(pattern.name, match.group()))
                    position += len(match.group())

                    for i in pattern.actions or []:
                        if isinstance(i, PopAction):
                            stack.pop()
                        elif isinstance(i, PushAction):
                            stack.append(i.state)
                        else:
                            raise RuntimeError("dunno")

                    break
            else:
                result.append(Token("InvalidCharacter", source[position]))
                position += 1

        return result

class PopAction(object):
    def __repr(object):
        return "PopAction()"

class PushAction(object):
    def __init__(self, state):
        self.state = state

    def __repr__(object):
        return "PushAction(%r)" % (self.state, )

def pop():
    return [PopAction()]

def push(*args):
    return [PushAction(i) for i in args]

def lex(source):
    p = Pattern

    BLANK_LINE_RE = r"[ \t]*(?=\n)"

    spec = {
        "default": [
            p("EndLine", r"\n"),

            p("Start:Blank", BLANK_LINE_RE),

            p("Start:Text", r"\\", push("text", "inline-content")),

            p("Start:Heading", r"#{1,6} ", push("header", "inline-content")),

            p("Start:UnorderedListItem", r" \* ",
              push("unordered-list", "inline-content")),

            p("Start:OrderedListItem", r" \# ",
              push("ordered-list", "inline-content")),

            p("Start:Code", r"    ",
              push("code", "raw-content")),

            p("Start:Annotation", r"!(?![ \t]*\n)", push("inline-content")),

            p("Start:Text", r"", push("text", "inline-content")),
        ],

        "raw-content": [
            p("PlainText", r"[^\n]+"),
            p("EndLine", r"\n", pop()),
        ],

        "inline-content": [
            p("PlainText", r"[^\n]+"),
            p("EndLine", r"\n", pop()),
        ],

        "text": [
            p("Start:Blank", BLANK_LINE_RE, pop()),
            p("Start:Text", r"", push("inline-content")),
        ],

        "header": [
            p("Start:Blank", BLANK_LINE_RE, pop()),
        ],

        "unordered-list": [
            p("Start:Blank", BLANK_LINE_RE, pop()),
            p("Start:UnorderedListItem", r"(?:    )* \* ",
              push("inline-content")),
            p("Start:UnorderedListItemContinuation", r"(?:    )*   ",
              push("inline-content")),
        ],

        "ordered-list": [
            p("Start:Blank", BLANK_LINE_RE, pop()),
            p("Start:OrderedListItem", r"(?:    )* # ",
              push("inline-content")),
            p("Start:OrderedListItemContinuation", r"(?:    )*   ",
              push("inline-content")),
        ],

        "code": [
            p("Start:Blank", BLANK_LINE_RE, pop()),
            p("Start:Code", r"    ", push("raw-content"))
        ],
    }

    return PushdownLexer(spec).lex(source)

class Node(object):
    def __init__(self, name, parent=None, children=None, start=None, end=None):
        self.name = name
        self.parent = parent
        self.children = children or []
        self.start = start
        self.end = end

    def __repr__(self):
        return u'Node(%r, %r)' % (self.name, self.value)

def parse(tokens):
    document = Node("Document")

    node_stack = [document]
    for i in tokens:
        assert len(node_stack) != 0

        if i.name.startswith("Start:"):
            if len(node_stack) == 1:
                # Create a new node if this is the start of a new block
                node_stack.append(Node(i.name[len("Start:"):], node_stack[-1]))


z = (
"""# Mono-Markup Specification

Hello world [link](href).

!syntax=c++
    if (awesome) {
        printf("Hello world")
    }

 * I am a list
   continue
 * Yes indeed

 # I am an ordered list
   continue
 # Onward!
""")
print lex(z)
