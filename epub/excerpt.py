#!/usr/bin/env python3
"""Write a standalone excerpt of a chapter for visual checks.

Takes the top-level <body> child containing the element with the given id,
plus the next N siblings, and writes them into a page using the same CSS.

Usage: excerpt.py OEBPS/chapter.xhtml ID N out.xhtml
"""
import sys
import xml.dom.minidom as minidom


def main():
    src, target, n, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    dom = minidom.parse(src)
    body = dom.getElementsByTagName("body")[0]
    node = next(el for el in dom.getElementsByTagName("*")
                if el.getAttribute("id") == target)
    while node.parentNode is not body:
        node = node.parentNode
    keep, count = [], 0
    while node is not None and count <= n:
        keep.append(node)
        if node.nodeType == node.ELEMENT_NODE:
            count += 1
        node = node.nextSibling
    for child in list(body.childNodes):
        if child not in keep:
            body.removeChild(child)
    with open(out, "w", encoding="utf-8") as f:
        f.write(dom.toxml())


if __name__ == "__main__":
    main()
