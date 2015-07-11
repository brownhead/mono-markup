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
        for k in self.spec:
            if isinstance(self.spec[k], InheritMarker):
                self.spec[k] = self.spec[self.spec[k].name]

    def parse(self, source):
        # The root node of the document
        document = Node("document", None)

        # Our iterator through our to-be-built AST. We will add new nodes we
        # encounter to this node as children.
        current_node = document

        # Our iterator through the source text.
        position = 0

        state_stack = [("document", document)]

        while position < len(source):
            # Go through each regex associated with current state in order
            for pattern in self.spec[state_stack[-1][0]]:
                match = pattern.regex.match(source, position)
                if match:
                    position += len(match.group())

                    if pattern.name is not None and not pattern.name.startswith("Start:"):
                        new_node = Node(pattern.name, match_object=match,
                                        parent=current_node)
                        current_node.children.append(new_node)

                    for i in pattern.actions or []:
                        if isinstance(i, PopAction):
                            if state_stack.pop()[1]:
                                current_node = current_node.parent
                        elif isinstance(i, PushAction):
                            if i.create_node:
                                new_node = Node(i.state, parent=current_node)
                                current_node.children.append(new_node)
                                current_node = new_node

                            state_stack.append((i.state, i.create_node))
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
    def __init__(self, state, create_node=True):
        self.state = state
        self.create_node = create_node

    def __repr__(object):
        return "PushAction(%r, %r)" % (self.state, self.create_node)

    @classmethod
    def from_string(self, string):
        if string.startswith(":"):
            return PushAction(string[1:], False)

        return PushAction(string, True)

def pop():
    return [PopAction()]

def push(*args):
    return [PushAction.from_string(i) for i in args]

class InheritMarker(object):
    def __init__(self, name):
        self.name = name

def inherit(name):
    return InheritMarker(name)

def parse(source):
    p = Pattern

    BLANK_LINE_RE = r"[ \t]*\n"

    spec = {
        "document": [
            p("BlankLine", BLANK_LINE_RE),

            # Text
            p(None, r"\\", push("text", ":inline-content")),

            # Heading
            p(None, r"#{1,6} ", push("header", ":inline-content")),

            # UnorderedListItem
            p(None, r" \* ", push("unordered-list", "unordered-list-item")),

            # OrderedListItem
            p(None, r" \# ", push("ordered-list", "ordered-list-item")),

            # Code
            p(None, r"    ", push("code", "code-line")),

            # Annotation
            p(None, r"!(?![ \t]*\n)", push("annotation")),

            # Text
            p(None, r"", push("text", ":inline-content")),
        ],

        "annotation": inherit("raw-content"),

        "raw-content": [
            p("PlainText", r"[^\n]+"),
            p(None, r"\n", pop()),
        ],

        "inline-content": [
            p("PlainText", r"[^\n]+"),
            p(None, r"\n", pop()),
        ],

        "text": [
            p(None, BLANK_LINE_RE, pop()),

            # Text
            p(None, r"", push("inline-content")),
        ],

        "header": [
            p(None, BLANK_LINE_RE, pop()),
        ],

        "unordered-list": [
            p(None, BLANK_LINE_RE, pop()),

            # UnorderedListItem
            p(None, r"(?:    )* \* ", push("unordered-list-item")),

            # UnorderedListItemContinuation
            p(None, r"(?:    )*   ", push("unordered-list-item-continuation")),
        ],
        "unordered-list-item": inherit("inline-content"),
        "unordered-list-item-continuation": inherit("inline-content"),

        "ordered-list": [
            p(None, BLANK_LINE_RE, pop()),

            # OrderedListItem
            p(None, r"(?:    )* \# ", push("ordered-list-item")),

            # OrderedListItemContinuation
            p(None, r"(?:    )*   ", push("ordered-list-item-continuation")),
        ],
        "ordered-list-item": inherit("inline-content"),
        "ordered-list-item-continuation": inherit("inline-content"),

        "code": [
            p(None, BLANK_LINE_RE, pop()),

            # Code
            p(None, r"    ", push("code-line"))
        ],
        "code-line": inherit("raw-content"),
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
