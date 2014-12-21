import re

class RouteNode(object):
    def __init__(self, segment, responder=None):
        self._children = []
        self.responder = responder

        # Create regex for any variables
        seg = segment.replace('.', '\\.')
        variables = list(re.finditer('{([-_a-zA-Z0-9]*)}', seg))

        if variables:
            self.is_var = True
            if len(variables) == 1 and variables[0].span() == (0,len(seg)):
                self.is_complex = False
                self.var_name = segment[1:-1]
            else:
                self.is_complex = True
                seg_fields = []
                prev_end_idx = 0
                for mo in variables:
                    var_span = mo.span()
                    var_start_idx = var_span[0]
                    seg_fields.append(seg[prev_end_idx:var_start_idx])
                    seg_name = mo.groups()[0]
                    seg_name = seg_name.replace('-', '_')
                    seg_fields.append('(?P<%s>[^/]*)' % seg_name)
                    prev_end_idx = var_span[1]
            
                seg_fields.append(seg[prev_end_idx:])
                seg_pattern = ''.join(seg_fields)
                self.var_regex = re.compile(seg_pattern)
        else:
            self.segment = segment
            self.is_var = False

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
        if self.is_var:
            if self.is_complex:
                match = self.var_regex.search(s)
                if match:
                    self.variables = match.groupdict()
                    return True
            else:
                self.variables = { self.var_name: s }
                return True
                
        elif s == self.segment:
            return True
        else:
            return False

    def add_child(self, node):
        self._children.append(node)

    def __repr__(self):
        return str(self)

    def __str__(self):
        if self.is_var:
            if self.is_complex:
                s = 'complex(%s)' % self.var_regex.pattern
            else:
                s = 'var(%s)' % self.var_name
        else:
            s = 'literal(%s)' % self.segment

        return 'RouteNode(%s, %s)' % (s, str(self.responder))


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
                        params.update(child.variables)

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
