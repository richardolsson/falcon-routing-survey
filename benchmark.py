#!/usr/bin/env python

import re
import sys
import timeit


def res_factory(url, methods):
    class Resource(object):
        def __init__(self):
            self.url = url

        def __repr__(self):
            return 'Resource(%s)' % self.url

    def method(self, req, resp):
        pass

    res = Resource()
    for method in methods:
        method_name = 'on_' + method.lower()
        setattr(res, method_name, method)

    return res


def setup_router(endpoints, cls):
    router = cls()
    for template, methods in endpoints.iteritems():
        resource = res_factory(template, methods)
        router.add_route(template, resource)

    return router


def measure_router(router_name, url, n=100000):
    imp_stmt = 'from __main__ import %s' % router_name
    run_stmt = '%s.find_responder("%s")' % (router_name, url)

    print('BENCHMARKING ROUTER: %s' % router_name)
    print('> %s' % imp_stmt)
    print('> %s' % run_stmt)

    t = timeit.timeit(run_stmt, setup=imp_stmt, number=n)

    print('RESULT: %ss (%d iterations)' % (t, n))


def main():
    global tree_router
    global regex_router

    if len(sys.argv) < 3:
        print('Usage: %s <api.txt> <url_to_find> [num_iterations]\n' %
            sys.argv[0])

        sys.exit(-1)

    file_name = sys.argv[1]
    url_to_find = sys.argv[2]

    iterations = 100000
    if len(sys.argv)>3:
        iterations = int(sys.argv[3])

    with open(file_name, 'r') as f:
        ws = re.compile('\s*')
        endpoint_methods = {}
        num_endpoints = 0
        num_methods = 0
        for line in f:
            if len(line) and line[0] == '#':
                # Skip comments
                continue

            fields = ws.split(line)
            if len(fields) and len(fields[0]):
                method, endpoint = fields[0:2]

                if endpoint not in endpoint_methods:
                    num_endpoints += 1
                    endpoint_methods[endpoint] = []

                if method not in endpoint_methods[endpoint]:
                    num_methods += 1
                    endpoint_methods[endpoint].append(method)
        
        print('%d endpoints (total of %d methods)' %
            (num_endpoints, num_methods))

        tree_router = setup_router(endpoint_methods, TreeRouter)
        regex_router = setup_router(endpoint_methods, RegexRouter)

        for root in tree_router._roots:
            root.print_debug()

        print('-----------')

        measure_router('tree_router', url_to_find, n=iterations)
        print('RETURN: %s' % tree_router.find_responder(url_to_find))

        print('-----------')

        measure_router('regex_router', url_to_find, n=iterations)
        print('RETURN: %s' % regex_router.find_responder(url_to_find))



class RouteNode(object):
    def __init__(self, segment, responder=None):
        self._children = []
        self.segment = segment
        self.responder = responder
        self.is_var = False
        if segment[0] == '{' and segment[-1] == '}':
            self.is_var = True

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
                    depth += 1

                    if depth == seg_count:
                        # Found leaf!
                        return child.responder
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
        # Naive
        path = pattern.split('/')

        if path[0] == '':
            path = path[1:]

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



class RegexRouter(object):
    def __init__(self):
        self._routes = []

    def find_responder(self, url):
        for route in self._routes:
            exp = route[0]
            if exp.search(url):
                return route[1]

    def add_route(self, pattern, responder):
        segments = pattern.lstrip('/').split('/')
        re_segments = []
        for seg in segments:
            if len(seg) and seg[0] == '{' and seg[-1] == '}':
                seg_name = seg[1:-1]
                seg_name = seg_name.replace('-', '_')
                seg = '(?P<%s>[-_a-zA-Z0-9]*)' % seg_name

            re_segments.append(seg)

        re_pattern = '^/%s$' % '/'.join(re_segments)
        exp = re.compile(re_pattern)

        self._routes.append((exp, responder))


if __name__ == '__main__':
    main()

