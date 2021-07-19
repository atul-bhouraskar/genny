from __future__ import annotations

from typing import Union
from .base import Clause, CompoundStatement, Py2PyException, Renderable
from . import base


class BlankLine(Renderable):
    def render_to_list(self, render_list, indent_level):
        render_list.append(base.BLOCK_STATEMENT_EOS)


class Assign(Renderable):
    def __init__(self,
                 lhs: Union[str, Renderable],
                 rhs: Union[str, Renderable]):
        self.lhs = lhs
        self.rhs = rhs
        super().__init__()

    def render_to_list(self, render_list, indent_level):
        base.render_item_to_list(self.lhs, render_list, indent_level)
        render_list.append(' = ')
        base.render_item_to_list(self.rhs, render_list, indent_level=0)
        render_list.append(base.BLOCK_STATEMENT_EOS)


class IfStatement(CompoundStatement):
    def __init__(self, expression):
        super().__init__()
        self.expression = expression
        self.if_clause = Clause('if', content=expression,
                                parent=self,
                                proxy_methods={
                                    'elif_': self.elif_,
                                    'else_': self.else_
                                })
        self.elif_clauses = []
        self.else_clause = None

    def get_clause(self) -> Clause:
        return self.if_clause

    def write(self, statement):
        return self.if_clause.write(statement)

    def elif_(self, expression):
        elif_clause = Clause('elif', content=expression,
                             parent=self,
                             proxy_methods={
                                 'elif_': self.elif_,
                                 'else_': self.else_
                             })
        self.elif_clauses.append(elif_clause)
        print('elif returning', elif_clause)
        return elif_clause

    def else_(self):
        if not self.else_clause:
            self.else_clause = Clause('else', parent=self)
            return self.else_clause
        else:
            raise Py2PyException('Only one "else" clause permitted in '
                                 '"if" statement')

    def render_to_list(self, render_list, indent_level):
        self.if_clause.render_to_list(render_list, indent_level)
        for elif_clause in self.elif_clauses:
            elif_clause.render_to_list(render_list, indent_level)
        if self.else_clause:
            self.else_clause.render_to_list(render_list, indent_level)


class WhileStatement(CompoundStatement):
    def __init__(self, expression):
        super().__init__()
        self.expression = expression

        self.while_clause = Clause('while', content=expression,
                                   parent=self,
                                   proxy_methods={
                                       'else_': self.else_
                                   })

        self.else_clause = None

    def get_clause(self) -> Clause:
        return self.while_clause

    def write(self, statement):
        self.while_clause.write(statement)
        return self

    def else_(self):
        if not self.else_clause:
            self.else_clause = Clause('else', parent=self)
            return self.else_clause
        else:
            raise Py2PyException('Only one "else" clause permitted in '
                                 '"while" statement')

    def render_to_list(self, render_list, indent_level):
        self.while_clause.render_to_list(render_list, indent_level)
        if self.else_clause:
            self.else_clause.render_to_list(render_list, indent_level)


class ForStatement(CompoundStatement):
    def __init__(self, target_list, in_):
        super().__init__()
        self.target_list = target_list
        self.expression_list = in_

        self.for_clause = Clause(
            'for',
            content=f'{target_list} in {in_}',
            parent=self,
            proxy_methods={
                'else_': self.else_
            })

        self.else_clause = None

    def get_clause(self) -> Clause:
        return self.for_clause

    def write(self, statement):
        self.for_clause.write(statement)
        return self

    def else_(self):
        if not self.else_clause:
            self.else_clause = Clause('else', parent=self)
            return self.else_clause
        else:
            raise Py2PyException('Only one "else" clause permitted in '
                                 '"for" statement')

    def render_to_list(self, render_list, indent_level):
        self.for_clause.render_to_list(render_list, indent_level)
        if self.else_clause:
            self.else_clause.render_to_list(render_list, indent_level)


class TryStatement(CompoundStatement):
    def __init__(self):
        super().__init__()

        self.try_clause = Clause('try',
                                 content='',
                                 parent=self,
                                 proxy_methods={
                                     'else_': self.else_,
                                     'except_': self.except_,
                                     'finally_': self.finally_
                                 })
        self.except_clauses = []
        self.else_clause = None
        self.finally_clause = None

    def get_clause(self) -> Clause:
        return self.try_clause

    def write(self, statement):
        self.try_clause.write(statement)
        return self

    def else_(self):
        if not self.else_clause:
            self.else_clause = Clause('else', parent=self)
            return self.else_clause
        else:
            raise Py2PyException('Only one "else" clause permitted in '
                                 '"if" statement')
        
    def except_(self, expression):
        except_clause = Clause('except', content=expression, parent=self,
                               proxy_methods={
                                   'except_': self.except_
                               })
        self.except_clauses.append(except_clause)
        return except_clause
    
    def finally_(self):
        if not self.finally_clause:
            self.finally_clause = Clause('finally', parent=self)
            return self.finally_clause
        else:
            raise Py2PyException('Only one "finally" clause permitted in '
                                 '"try" statement')

    def render_to_list(self, render_list, indent_level):
        if not self.except_clauses and not self.finally_clause:
            raise Py2PyException('"try" statement must have at-least one '
                                 '"except" clause or a "finally" clause')
        self.try_clause.render_to_list(render_list, indent_level)
        for except_clause in self.except_clauses:
            except_clause.render_to_list(render_list, indent_level)
        if self.else_clause:
            self.else_clause.render_to_list(render_list, indent_level)
        if self.finally_clause:
            self.finally_clause.render_to_list(render_list, indent_level)


class WithStatement(CompoundStatement):
    def __init__(self, expression, as_=None):
        super().__init__()
        self.items = [(expression, as_)]
        self.clause = Clause('with', content='', parent=self)

    def get_clause(self) -> Clause:
        return self.clause

    def write(self, statement):
        self.clause.write(statement)
        return self

    def add_with_item(self, expression, as_=None):
        self.items.append((expression, as_))
        return self

    @staticmethod
    def _render_item(item):
        return f'{item[0]} as {item[1]}' if item[1] else item[0]

    def render_to_list(self, render_list, indent_level):
        rendered_items = ', '.join([self._render_item(x) for x in self.items])
        self.clause.header.set_content(rendered_items)
        self.clause.render_to_list(render_list, indent_level=indent_level)


class DefStatement(CompoundStatement):
    def __init__(self, name, parameter_list=None, decorators=None):
        super().__init__()
        self.name = name
        self.parameter_list = parameter_list or []
        self.clause = Clause('def', content='', parent=self,
                             decorators=decorators)

    def get_clause(self) -> Clause:
        return self.clause

    def write(self, statement):
        self.clause.write(statement)
        return self

    def render_to_list(self, render_list, indent_level):
        params = ', '.join(self.parameter_list)
        func_str = f'{self.name}({params})'
        self.clause.header.set_content(func_str)
        self.clause.render_to_list(render_list, indent_level=indent_level)


class ClassStatement(CompoundStatement):
    def __init__(self, name, bases=None, decorators=None):
        self.name = name
        self.bases = bases
        super().__init__()
        self.clause = Clause('class', content='', parent=self,
                             decorators=decorators)

    def get_clause(self) -> Clause:
        return self.clause

    def write(self, statement):
        self.clause.write(statement)
        return self

    def add_method(self, name, parameter_list=None, decorators=None):
        if parameter_list is None:
            parameter_list = []
        parameter_list.insert(0, 'self')

        return self.add_method_(name, parameter_list, decorators)

    def add_class_method(self, name, parameter_list=None, decorators=None):
        if parameter_list is None:
            parameter_list = []
        parameter_list.insert(0, 'cls')

        if decorators is None:
            decorators = []
        decorators.append('classmethod')

        return self.add_method_(name, parameter_list, decorators)

    def add_static_method(self, name, parameter_list=None, decorators=None):
        if parameter_list is None:
            parameter_list = []

        if decorators is None:
            decorators = []
        decorators.append('staticmethod')

        return self.add_method_(name, parameter_list, decorators)

    def add_method_(self, name, parameter_list, decorators=None):
        statement = DefStatement(name, parameter_list, decorators)
        self.write(statement)
        return statement

    def render_to_list(self, render_list, indent_level):
        base_part = '({})'.format(','.join(self.bases)) if self.bases else ''
        content = f'{self.name}{base_part}'
        self.clause.header.set_content(content)
        self.clause.render_to_list(render_list, indent_level=indent_level)
        render_list.append(base.BLOCK_STATEMENT_EOS)
        render_list.append(base.BLOCK_STATEMENT_EOS)


class FunctionCall(Renderable):
    def __init__(self, function_name, *args, **kwargs):
        super().__init__()
        self.function_name = function_name
        self.args = args
        self.kwargs = kwargs

    def render_to_list(self, render_list, indent_level):
        render_list.append(base.do_indent(self.function_name, indent_level))
        render_list.append('(')
        for arg in self.args:
            base.render_item_to_list(arg, render_list, indent_level=0)
            render_list.append(', ')

        for key, value in self.kwargs.items():
            render_list.append(f'{key}=')
            base.render_item_to_list(value, render_list, indent_level=0)
            render_list.append(', ')
        render_list.pop()
        render_list.append(')')
