#!/usr/bin/env python3
"""Small XHTML reader used only to prepare version-locked book recipes."""
from html.parser import HTMLParser
from pathlib import Path


class Node:
    def __init__(self, tag="", attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def text(self):
        return "".join(x if isinstance(x, str) else x.text() for x in self.children)

    def walk(self, tag=None):
        if tag is None or self.tag == tag:
            yield self
        for x in self.children:
            if isinstance(x, Node):
                yield from x.walk(tag)


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.cur = self.root
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in {"meta", "link", "img", "br", "hr", "input", "col", "wbr"}:
            self.cur = n

    def handle_startendtag(self, t, a):
        n = Node(t, a, self.cur)
        self.cur.children.append(n)

    def handle_endtag(self, tag):
        p = self.cur
        while p.parent:
            if p.tag == tag:
                self.cur = p.parent
                return
            p = p.parent

    def handle_data(self, d):
        self.cur.children.append(d)


def read(path):
    return Document(Path(path).read_text()).root


def commands(doc):
    return [
        n.text()
        for n in doc.walk("pre")
        if n.attrs.get("class") in {"userinput", "root"}
    ]
