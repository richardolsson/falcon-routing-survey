import tree

class CompiledTreeRouter(tree.TreeRouter):
    def __init__(self):
        super(CompiledTreeRouter, self).__init__()
        self._find = None
        self._code_lines = None
        self._responders = []

    def find_responder(self, pattern):
        if self._find is None:
            self._compile()

        path = pattern.split('/')
        if path[0]=='':
            path = path[1:]

        params = {}
        responder = self._find(path, self._responders, params)
        return responder, params

    def _compile_node(self, node=None, level=0):
        pad = '  ' + level * '  '

        if node.is_var:
            # TODO: Collapse this somehow?
            self._code_lines.append(pad + 'if path_len > %d:' % level)
            self._code_lines.append(pad + '  params["%s"] = path[%d]' % (node.var_name, level))
        else:
            cond_src = 'if path_len > %d and path[%d] == "%s":' % (level, level, node.segment)
            self._code_lines.append(pad + cond_src)

        if node.responder is not None:
            responder_idx = len(self._responders)
            self._responders.append(node.responder)

        if len(node._children):
            for child in node._children:
                self._compile_node(child, level+1)
            
        if node.responder is not None:
            ret_src = '  return responders[%d]' % responder_idx
            self._code_lines.append(pad + ret_src)


    def _compile(self):
        self._responders = []
        self._code_lines = [
            'def find(path, responders, params):',
            '  path_len = len(path)',
        ]

        for root in self._roots:
            self._compile_node(root)

        src = '\n'.join(self._code_lines)

        print(src)
        ns = {}
        exec compile(src, '<string>', 'exec') in ns
        self._find = ns['find']

