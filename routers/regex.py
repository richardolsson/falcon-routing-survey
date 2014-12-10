import re

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
                seg = '(?P<%s>[^/]*)' % seg_name

            re_segments.append(seg)

        re_pattern = '^/%s$' % '/'.join(re_segments)
        exp = re.compile(re_pattern)

        self._routes.append((exp, responder))

