
class RouteNode(object):
    def __init__(self, segment, responder=None):
        self._children = []
        self.segment = segment
        self.responder = responder
        self.is_var = False
        if segment[0] == '{' and segment[-1] == '}':
            self.is_var = True
            self.var_name = segment[1:-1]

    def traverse(self, segments, index=0, seg_count=None):
        if seg_count is None:
            seg_count = len(segments)

        if self.matches(segments[index]):
            index += 1
            if index == seg_count:
                return self
            elif index < seg_count:
                for child in self._children:
                    result = child.traverse(segments, index, seg_count)
                    if result is not None:
                        return result

        return None


    #TODO: Remove
    def print_debug(self, level=0):
        pad = '  '*level
        print(pad+str(self))
        for child in self._children:
            child.print_debug(level+1)


    def matches(self, s):
        if self.is_var or s == self.segment:
            return True
        else:
            return False

    def add_child(self, node):
        self._children.append(node)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return 'RouteNode(%s, %s)' % (self.segment, str(self.responder))


class TreeRouter(object):
    def __init__(self):
        self._roots = []

    def add_route(self, pattern, responder):
        root, leaf = self._parse(pattern)
        leaf.responder = responder
        if root is not None:
            self._roots.append(root)

    def find_responder(self, pattern):
        path = pattern.split('/')
        if path[0] == '':
            path = path[1:]

        seg_count = len(path)

        child_lists = [None] * (seg_count+1)
        child_indices = [0] * (seg_count+1)
        child_lists[0] = self._roots
        depth = 0

        params = {}

        while depth < seg_count:
            children = child_lists[depth]
            child_index = child_indices[depth]
            going_deeper = False
            num_children = 0
            if children is not None:
                num_children = len(children)

            if child_index >= num_children and depth == 0:
                # Traversed all
                return None

            while child_index < num_children:
                child = children[child_index]
                if child.matches(path[depth]):
                    child_lists[depth+1] = child._children
                    child_indices[depth] = child_index + 1

                    if child.is_var:
                        params[child.var_name] = path[depth]

                    depth += 1

                    if depth == seg_count:
                        # Found leaf!
                        return child.responder, params
                    else:
                        going_deeper = True
                        # Get back to outer loop, which will
                        # now be one step deeper in recursion
                        break

                child_index += 1

            # Nothing found, pop back
            if not going_deeper:
                depth -= 1
                if depth < 0:
                    return None

                children = child_lists[depth]
                child_index = child_indices[depth]

        return None


    def _find_leaf_from_path(self, path):
        for root in self._roots:
            result = root.traverse(path)
            if result is not None:
                return root, result

        return None, None

    def _parse(self, pattern):
        # Remove any leading slash, and surrounding white space
        pattern = pattern.strip().lstrip('/')
        path = pattern.split('/')

        # This node has already been created?
        ancestor, parent = self._find_leaf_from_path(path)
        if ancestor is not None:
            root = None
            leaf = parent
        else:
            # Find potentially existing ancestor
            parent = None
            ancestor = None
            index = len(path) - 1
            while index > 0:
                ancestor, parent = self._find_leaf_from_path(path[0:index])
                if ancestor is not None:
                    break

                index -= 1

            root = RouteNode(path[index])
            leaf = root
            index += 1
            if index < len(path):
                for segment in path[index:]:
                    node = RouteNode(segment)
                    leaf.add_child(node)
                    leaf = node

            if ancestor is not None:
                parent.add_child(root)
                root = None

        return root, leaf
