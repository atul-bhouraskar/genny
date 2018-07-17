
INDENT = ' ' * 4  # 4 spaces

CAN_RENDER_SUITES_INLINE = False
INLINE_STATEMENT_EOS = ';'
BLOCK_STATEMENT_EOS = '\n'


class Py2PyException(Exception):
    pass


class Expression(object):
    def __init__(self, text):
        self.text = text

    def render(self):
        return self.text


class Renderable(object):
    def render_to_list(self, render_list, indent_level):
        raise NotImplementedError('render_to_list() should be implemented by '
                                  'all statements')

    def render(self, indent_level=0):
        render_list = []
        self.render_to_list(render_list, indent_level=indent_level)
        return ''.join(render_list)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class SimpleStatement(Renderable):
    def __init__(self, text):
        self.text = text
        self.render_inline = CAN_RENDER_SUITES_INLINE

    def render_to_list(self, render_list, indent_level):
        bos = ' ' if self.render_inline else ''  # Beginning of statement
        eos = INLINE_STATEMENT_EOS if self.render_inline \
            else BLOCK_STATEMENT_EOS  # End of statement
        return render_list.append(do_indent(bos + self.text.strip() + eos,
                                            indent_level))


class Clause(Renderable):
    def __init__(self, keyword, content='', proxy_methods=None,
                 decorators=None,
                 parent=None, render_inline=None):
        if not parent:
            raise Py2PyException('Clause requires parent')
        self.decorators = decorators or []
        self.header = ClauseHeader(keyword, content=content)
        self.suite = Suite(parent=parent, proxy_methods=proxy_methods,
                           render_inline=render_inline)
        self.proxy_methods = proxy_methods
        self.p = self.parent = parent
        
    def __getattr__(self, item):
        if self.proxy_methods:
            try:
                print 'Clause Proxy - ', item, self.proxy_methods
                return self.proxy_methods[item]
            except KeyError:
                raise AttributeError()

    def dedent(self):
        return self.parent

    def write(self, statement):
        return self.suite.write(statement)

    @staticmethod
    def render_decorator(d):
        if len(d) == 0:
            return

        prefix = '@' if d[0] != '@' else ''
        return '%s%s\n' % (prefix, d)

    def render_to_list(self, render_list, indent_level):
        if self.suite.render_inline:
            self.header.eos = ''
        for d in self.decorators:
            render_list.append(self.render_decorator(d))
        self.header.render_to_list(render_list, indent_level)
        self.suite.render_to_list(render_list, indent_level+1)


class ClauseHeader(Renderable):
    def __init__(self, keyword, content=''):
        self.keyword = keyword
        self.content = ''
        self.set_content(content)
        self.eos = BLOCK_STATEMENT_EOS

    def set_content(self, content):
        self.content = ' ' + content if content else ''

    def render_to_list(self, render_list, indent_level):
        return render_list.append(
            do_indent(
                '%s%s:%s' % (self.keyword, self.content, self.eos),
                indent_level=indent_level))


class CompoundStatement(Renderable):
    def __init__(self, parent):
        self.p = self.parent = parent

    def dedent(self):
        return self.parent

    def render_to_list(self, render_list, indent_level):
        raise NotImplementedError('render_to_list() should be implemented by '
                                  'all compound statements')


class Suite(Renderable):
    def __init__(self, pass_if_empty=True, parent=None, proxy_methods=None,
                 render_inline=None):
        self.statements = []
        self.pass_if_empty = pass_if_empty
        self.p = self.parent = parent
        self.proxy_methods = proxy_methods
        self.render_inline = render_inline if render_inline is not None \
            else CAN_RENDER_SUITES_INLINE

    def __getattr__(self, item):
        if self.proxy_methods:
            try:
                print 'Suite Proxy - ', item, self.proxy_methods
                return self.proxy_methods[item]
            except KeyError:
                pass
        raise AttributeError(item)

    def write(self, statement):
        self.add(statement)
        return self

    def add(self, statement):
        if isinstance(statement, SimpleStatement):
            pass  # TODO validate?
        elif isinstance(statement, CompoundStatement):
            # A suite can only be rendered inline if all statements are simple
            self.render_inline = False
        else:  # assume string, convert to SimpleStatement
            statement = SimpleStatement(statement)

        self.statements.append(statement)
        return statement

    def clear(self):
        self.statements = []

    def dedent(self):
        if self.parent:
            return self.parent
        else:
            return self  # FIXME should this raise exception?

    def render_to_list(self, render_list, indent_level):
        if not self.statements and self.pass_if_empty:
            # no statements, automatically add pass
            self.write('pass')

        if self.render_inline:
            # render as inline statement list
            local_indent_level = 0  # don't indent
        else:
            # render as indented code block
            local_indent_level = indent_level  # indent each statement
        for statement in self.statements:
            statement.render_inline = self.render_inline
            statement.render_to_list(render_list, local_indent_level)
        if self.render_inline:
            render_list.append('\n')


class SimpleAssignmentStatement(SimpleStatement):
    def __init__(self, lhs, rhs):
        super(SimpleAssignmentStatement, self).__init__('%s = %s' % (lhs, rhs))


def do_indent(text, indent_level):
    if indent_level > 0:
        return INDENT * indent_level + text
    else:
        return text
