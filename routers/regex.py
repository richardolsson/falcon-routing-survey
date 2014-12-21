import re

class Route(object):
    def __init__(self, exp, responder):
        self.expression = exp
        self.responder = responder


class RegexRouter(object):
    def __init__(self):
        self._routes = []

    def find_responder(self, url):
        for route in self._routes:
            match = route.expression.search(url)
            if match:
                return route.responder, match.groupdict()

    def add_route(self, pattern, responder):
        segments = pattern.lstrip('/').split('/')
        re_segments = []
        for seg in segments:
            if len(seg) > 0:
                seg = seg.replace('.', '\\.')
                variables = re.finditer('{([-_a-zA-Z0-9]*)}', seg)
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
                seg = ''.join(seg_fields)


            re_segments.append(seg)

        re_pattern = '^/%s$' % '/'.join(re_segments)
        exp = re.compile(re_pattern)

        route = Route(exp, responder)
        self._routes.append(route)

