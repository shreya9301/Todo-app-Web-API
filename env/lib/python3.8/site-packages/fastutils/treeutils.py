from . import dictutils

def build_tree(thelist, pk_attr="id", parent_attr="parent_id", children_attr="children"):
    """Tree node is a dict with pk_attr, parent_attr and children_attr fields: {"id": 2, "parent_id": 1, "children": []}.
    """
    roots = []
    nodes = {}
    for node in thelist:
        dictutils.touch(node, children_attr, [])
        node_id = dictutils.select(node, pk_attr)
        nodes[node_id] = node
    for node in thelist:
        parent_id = dictutils.select(node, parent_attr)
        if (not parent_id) or (not parent_id in nodes):
            roots.append(node)
        else:
            dictutils.select(nodes[parent_id], children_attr).append(node)
    return roots

def tree_walk(tree, callback, children_attr="children", callback_args=None, callback_kwargs=None, depth=0, parent=None):
    callback_args = callback_args or ()
    callback_kwargs = callback_kwargs or {}

    for node in tree:
        callback(node, tree, depth, parent, *callback_args, **callback_kwargs)
        children = dictutils.select(node, children_attr, [])
        if children:
            tree_walk(children, callback, children_attr, callback_args, callback_kwargs, depth+1, node)

def print_tree_callback(node, tree, depth, parent, *args, **kwargs):
    title_attr = kwargs.get("title_attr", "title")
    indent_string = kwargs.get("indent_string", "    ")
    print(indent_string * depth + dictutils.select(node, title_attr))

def print_tree(tree, title_attr="title", children_attr="children", indent_string="     "):
    tree_walk(tree, print_tree_callback, children_attr, (), {"title_attr": title_attr, "indent_string": indent_string})
