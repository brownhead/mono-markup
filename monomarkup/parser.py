from funcparserlib.lexer import make_tokenizer
import re

def tokenize(str):
    """str -> Sequence(Token)"""
    specs = [
        (u"BlankLine", (ur"\n", )),
        (u"CollapsedBlankLine", (ur"!\n", )),
        (u"Header", (ur"#\S.*\n", )),
        (u"UnorderedListItem", (ur" \* .*\n", )),
        (u"OrderedListItem", (ur" # .*\n", )),
        (u"ListItemContinuation", (ur"   .+\n", )),
        (u"Code", (ur"    [^ ].*\n", )),
        (u"Annotation", (ur"!.+\n", )),
        (u"Text", (ur".+",)),
    ]
    t = make_tokenizer(specs)
    return [x for x in t(str)]

z = (
"""#= Mono-Markup Specification

Hello world [link](href).

!syntax=c++
    printf("hello!");

    printf("hello!");

 * I am a list
   continue

 # I am also a list
   continue
""")
for i in tokenize(z):
    print i.type, repr(i.value)
