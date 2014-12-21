#!/usr/bin/env python

import sys
import codecs
import timeit

from routers import TreeRouter, RegexRouter, CompiledTreeRouter


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

    print('----------------------------------------')
    print('BENCHMARKING ROUTER: %s' % router_name)
    print('> %s' % imp_stmt)
    print('> %s' % run_stmt)

    t = timeit.timeit(run_stmt, setup=imp_stmt, number=n)

    print('RESULT: %ss (%d iterations)' % (t, n))


def main():
    global tree_router
    global regex_router
    global compiled_router

    if len(sys.argv) < 3:
        print('Usage: %s <api.txt> <url_to_find> [num_iterations]\n' %
            sys.argv[0])

        sys.exit(-1)

    file_name = sys.argv[1]
    url_to_find = sys.argv[2]

    iterations = 100000
    if len(sys.argv)>3:
        iterations = int(sys.argv[3])

    with codecs.open(file_name, 'r', 'utf8') as f:
        endpoint_methods = {}
        num_endpoints = 0
        num_methods = 0
        for line in f:
            if len(line) and line[0] == '#':
                # Skip comments
                continue

            fields = line.split()
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
        compiled_router = setup_router(endpoint_methods, CompiledTreeRouter)
        compiled_router._compile()

        for root in tree_router._roots:
            root.print_debug()

        measure_router('tree_router', url_to_find, n=iterations)
        print('RETURN: %s' % str(tree_router.find_responder(url_to_find)))

        measure_router('regex_router', url_to_find, n=iterations)
        print('RETURN: %s' % str(regex_router.find_responder(url_to_find)))

        measure_router('compiled_router', url_to_find, n=iterations)
        print('RETURN: %s' % str(compiled_router.find_responder(url_to_find)))


if __name__ == '__main__':
    main()

