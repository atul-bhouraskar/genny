from __future__ import annotations
from typing import List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from . import statements

INDENT = ' ' * 4  # 4 spaces

CAN_RENDER_SUITES_INLINE = False
INLINE_STATEMENT_EOS = ';'
BLOCK_STATEMENT_EOS = '\n'

RenderList = List[str]


class Py2PyException(Exception):
    pass


class Expression:
    def __init__(self, text):
        self.text = text

    def render(self):
        return self.text


class Renderable:
    def __init__(self, parent: Optional[Renderable] = None):
        self.parent: Optional[Renderable] = parent

    def render_to_list(self, render_list: RenderList, indent_level: int):
        raise NotImplementedError('render_to_list() should be implemented by '
                                  'all statements')

    def render(self, indent_level: int = 0) -> str:
        render_list = []
        self.render_to_list(render_list, indent_level=indent_level)
        return ''.join(render_list)

    def set_parent(self):
        return self.parent

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class SimpleStatement(Renderable):
    def __init__(self, text: str):
        self.text: str = text
        super().__init__()

    def render_to_list(self, render_list, indent_level):
        return render_list.append(
            do_indent(self.text.strip(), indent_level)
        )


class Clause(Renderable):
    def __init__(self, keyword: str, content: str = '', proxy_methods=None,
                 decorators: Optional[List[str]] = None,
                 parent=None):
        self.decorators: Optional[List[str]] = decorators or []
        self.header = ClauseHeader(keyword, content=content)
        self.suite = Suite(parent=parent, proxy_methods=proxy_methods)
        self.proxy_methods = proxy_methods
        super().__init__(parent)
        
    def __getattr__(self, item):
        if self.proxy_methods:
            try:
                return self.proxy_methods[item]
            except KeyError:
                raise AttributeError()

    def dedent(self):
        return self.parent

    def write(self, statement: Statement):
        return self.suite.write(statement)

    @staticmethod
    def render_decorator(d: str):
        if len(d) == 0:
            return

        prefix = '@' if d[0] != '@' else ''
        return f'{prefix}{d}\n'

    def render_to_list(self, render_list, indent_level):
        for d in self.decorators:
            render_list.append(
                do_indent(self.render_decorator(d), indent_level)
            )
        self.header.render_to_list(render_list, indent_level)
        self.suite.render_to_list(render_list, indent_level+1)


class ClauseHeader(Renderable):
    def __init__(self, keyword: str, content: str = ''):
        self.keyword: str = keyword
        self.content: str = ''
        self.set_content(content)
        super().__init__()

    def set_content(self, content: str):
        self.content = ' ' + content if content else ''

    def render_to_list(self, render_list, indent_level):
        return render_list.append(
            do_indent(
                f'{self.keyword}{self.content}:\n',
                indent_level=indent_level))


class CompoundStatement(Renderable):
    def __init__(self, parent: Renderable):
        super().__init__(parent)

    def dedent(self):
        return self.parent

    def get_clause(self) -> Clause:
        raise NotImplementedError('Every CompoundStatement must implement '
                                  'get_clause()')

    def __getattr__(self, item):
        if item[-1] == '_':
            return getattr(self.get_clause(), item)
        raise AttributeError(item)

    def render_to_list(self, render_list, indent_level):
        raise NotImplementedError('render_to_list() should be implemented by '
                                  'all compound statements')


Statement = Union[CompoundStatement, SimpleStatement]


class Suite(Renderable):
    def __init__(self, pass_if_empty: bool = True,
                 parent: Optional[Renderable] = None,
                 proxy_methods=None):
        self.statements = []
        self.pass_if_empty = pass_if_empty
        self.proxy_methods = proxy_methods
        super().__init__(parent)

    def __getattr__(self, item):
        if self.proxy_methods:
            try:
                return self.proxy_methods[item]
            except KeyError:
                pass
        raise AttributeError(item)

    def write(self, statement: Statement):
        self.add(statement)
        return self

    def add(self, statement: Union[str, Statement]):
        if isinstance(statement, str):
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

    def call_(self, function_name, *args, **kwargs) -> statements.FunctionCall:
        from .statements import FunctionCall
        statement = FunctionCall(function_name, *args, **kwargs)
        self.add(statement)
        return statement

    def class_(self, name, bases=None,
               decorators=None) -> statements.ClassStatement:
        from .statements import ClassStatement
        statement = ClassStatement(name, bases, decorators)
        self.add(statement)
        return statement

    def def_(self, name, parameter_list=None,
             decorators=None) -> statements.DefStatement:
        from .statements import DefStatement
        statement = DefStatement(name, parameter_list, decorators, parent=self)
        self.add(statement)
        return statement

    def for_(self, target_list, in_) -> statements.ForStatement:
        from .statements import ForStatement
        statement = ForStatement(target_list, in_, parent=self)
        self.add(statement)
        return statement

    def if_(self, expression) -> statements.IfStatement:
        from .statements import IfStatement
        statement = IfStatement(expression, parent=self)
        self.add(statement)
        return statement

    def try_(self) -> statements.TryStatement:
        from .statements import TryStatement
        statement = TryStatement(parent=self)
        self.add(statement)
        return statement

    def while_(self, expression) -> statements.WhileStatement:
        from .statements import WhileStatement
        statement = WhileStatement(expression, parent=self)
        self.add(statement)
        return statement

    def with_(self, expression, as_) -> statements.WithStatement:
        from .statements import WithStatement
        statement = WithStatement(expression, as_, parent=self)
        return statement

    def render_to_list(self, render_list, indent_level):
        if not self.statements and self.pass_if_empty:
            # no statements, automatically add pass
            self.write(SimpleStatement('pass'))

        for statement in self.statements:
            statement.render_to_list(render_list, indent_level)


class SimpleAssignmentStatement(SimpleStatement):
    def __init__(self, lhs: str, rhs: str):
        super().__init__(f'{lhs} = {rhs}')


def do_indent(text: str, indent_level: int):
    if indent_level > 0:
        return INDENT * indent_level + text
    else:
        return text


def render_item_to_list(item: Union[str, Renderable],
                        render_list: RenderList, indent_level: int):
    if isinstance(item, str):
        render_list.append(do_indent(item, indent_level))
    else:
        item.render_to_list(render_list, indent_level)


def render_item(item: Union[str, Renderable]):
    if isinstance(item, str):
        return item

    render_list = []
    item.render_to_list(render_list, 0)
    return ''.join(render_list)
