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

class Node(object):
    def __init__(self, name, match_object=None, parent=None, children=None):
        self.name = name
        self.match_object = match_object
        self.parent = parent
        self.children = children or []

    def _print(self):
        node_stack = [(0, self)]
        while node_stack:
            depth, node = node_stack.pop()
            print "  " * depth + u"Node({0.name}, {1!r})".format(node, node.match_object.group() if node.match_object else "None")
            node_stack += [(depth + 1, i) for i in reversed(node.children)]

    def __repr__(self):
        return u'Node(%r, %r)' % (self.name, self.children)

# class LiteralTextNode(object):

class PushdownParser(object):
    def __init__(self, spec):
        self.spec = spec

    def parse(self, source):
        # The root node of the document
        document = Node("document", None)

        # Our iterator through our to-be-built AST. We will add new nodes we
        # encounter to this node as children.
        current_node = document

        # Our iterator through the source text.
        position = 0

        while position < len(source):
            # Go through each regex associated with current state in order
            for pattern in self.spec[current_node.name]:
                match = pattern.regex.match(source, position)
                if match:
                    position += len(match.group())

                    if not pattern.name.startswith("Start:"):
                        new_node = Node(pattern.name, match_object=match,
                                        parent=current_node)
                        current_node.children.append(new_node)

                    for i in pattern.actions or []:
                        if isinstance(i, PopAction):
                            current_node = current_node.parent
                        elif isinstance(i, PushAction):
                            new_node = Node(i.state, parent=current_node)
                            current_node.children.append(new_node)
                            current_node = new_node
                        else:
                            raise RuntimeError("dunno")

                    break
            else:
                current_node.children.append(Token("InvalidCharacter", None))#source[position]))
                position += 1

        if position < len(source):
            RuntimeError("Finished early somehow")

        return document

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

def parse(source):
    p = Pattern

    BLANK_LINE_RE = r"[ \t]*(?=\n)"

    spec = {
        "document": [
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

    return PushdownParser(spec).parse(source)


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
parse(z)._print()
