from .base import Clause, CompoundStatement, Py2PyException, Renderable, Suite
import base

__all__ = ('IfStatement', 'WhileStatement', 'ForStatement', 'TryStatement')


class BlankLine(Renderable):
    def render_to_list(self, render_list, indent_level):
        render_list.append(base.BLOCK_STATEMENT_EOS)


class Assign(Renderable):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def render_to_list(self, render_list, indent_level):
        base.render_item(self.lhs, render_list, indent_level)
        render_list.append(' = ')
        base.render_item(self.rhs, render_list, indent_level)
        render_list.append(base.BLOCK_STATEMENT_EOS)


class IfStatement(CompoundStatement):
    def __init__(self, expression, parent, render_inline=None):
        super(IfStatement, self).__init__(parent)
        self.render_inline = render_inline
        self.expression = expression
        self.if_clause = Clause('if', content=expression,
                                parent=parent,
                                proxy_methods={
                                    'elif_': self.elif_,
                                    'else_': self.else_
                                },
                                render_inline=render_inline)
        self.elif_clauses = []
        self.else_clause = None

    def __getattr__(self, item):
        if item[-1] == '_':
            return getattr(self.if_clause.suite, item)
        raise AttributeError(item)

    def write(self, statement):
        return self.if_clause.write(statement)

    def elif_(self, expression):
        elif_clause = Clause('elif', content=expression,
                             parent=self,
                             proxy_methods={
                                 'elif_': self.elif_,
                                 'else_': self.else_
                             },
                             render_inline=self.render_inline)
        self.elif_clauses.append(elif_clause)
        print 'elif returning', elif_clause
        return elif_clause

    def else_(self):
        if not self.else_clause:
            self.else_clause = Clause('else', parent=self,
                                      render_inline=self.render_inline)
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


Suite.if_ = lambda self, expression: \
    self.add(IfStatement(expression, parent=self))


class WhileStatement(CompoundStatement):
    def __init__(self, expression, parent, render_inline=None):
        super(WhileStatement, self).__init__(parent)
        self.expression = expression
        self.render_inline = render_inline

        self.while_clause = Clause('while', content=expression,
                                   parent=parent,
                                   proxy_methods={
                                       'else_': self.else_
                                   },
                                   render_inline=render_inline)

        self.else_clause = None

    def write(self, statement):
        self.while_clause.write(statement)
        return self

    def else_(self):
        if not self.else_clause:
            self.else_clause = Clause('else', parent=self,
                                      render_inline=self.render_inline)
            return self.else_clause
        else:
            raise Py2PyException('Only one "else" clause permitted in '
                                 '"while" statement')

    def render_to_list(self, render_list, indent_level):
        self.while_clause.render_to_list(render_list, indent_level)
        if self.else_clause:
            self.else_clause.render_to_list(render_list, indent_level)


Suite.while_ = lambda self, expression: \
    self.add(WhileStatement(expression, parent=self))


class ForStatement(CompoundStatement):
    def __init__(self, target_list, in_, parent, render_inline=None):
        super(ForStatement, self).__init__(parent)
        self.target_list = target_list
        self.expression_list = in_
        self.render_inline = render_inline

        self.for_clause = Clause(
            'for',
            content='%s in %s' % (target_list, in_),
            parent=parent,
            proxy_methods={
                'else_': self.else_
            },
            render_inline=render_inline)

        self.else_clause = None

    def write(self, statement):
        self.for_clause.write(statement)
        return self

    def else_(self):
        if not self.else_clause:
            self.else_clause = Clause('else', parent=self,
                                      render_inline=self.render_inline)
            return self.else_clause
        else:
            raise Py2PyException('Only one "else" clause permitted in '
                                 '"for" statement')

    def render_to_list(self, render_list, indent_level):
        self.for_clause.render_to_list(render_list, indent_level)
        if self.else_clause:
            self.else_clause.render_to_list(render_list, indent_level)


Suite.for_ = lambda self, target_list, in_: \
    self.add(ForStatement(target_list, in_, parent=self))


class TryStatement(CompoundStatement):
    def __init__(self, parent, render_inline=None):
        super(TryStatement, self).__init__(parent)
        self.render_inline = render_inline

        self.try_clause = Clause('try', content='', parent=parent,
                                 proxy_methods={
                                     'else_': self.else_,
                                     'except_': self.except_,
                                     'finally_': self.finally_
                                 },
                                 render_inline=render_inline)
        self.except_clauses = []
        self.else_clause = None
        self.finally_clause = None

    def write(self, statement):
        self.try_clause.write(statement)
        return self

    def else_(self):
        if not self.else_clause:
            self.else_clause = Clause('else', parent=self,
                                      render_inline=self.render_inline)
            return self.else_clause
        else:
            raise Py2PyException('Only one "else" clause permitted in '
                                 '"if" statement')
        
    def except_(self, expression):
        except_clause = Clause('except', content=expression, parent=self,
                               proxy_methods={
                                   'except_': self.except_
                               },
                               render_inline=self.render_inline)
        self.except_clauses.append(except_clause)
        return except_clause
    
    def finally_(self):
        if not self.finally_clause:
            self.finally_clause = Clause('finally', parent=self,
                                         render_inline=self.render_inline)
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


Suite.try_ = lambda self: \
    self.add(TryStatement(parent=self))


class WithStatement(CompoundStatement):
    def __init__(self, expression, as_=None, parent=None, render_inline=None):
        if not parent:
            raise Py2PyException('WithStatement requires a parent')
        super(WithStatement, self).__init__(parent)
        self.items = [(expression, as_)]
        self.clause = Clause('with', content='', parent=parent,
                             render_inline=render_inline)

    def write(self, statement):
        self.clause.write(statement)
        return self

    def add_with_item(self, expression, as_=None):
        self.items.append((expression, as_))
        return self

    @staticmethod
    def _render_item(item):
        return '%s as %s' % (item[0], item[1]) if item[1] else item[0]

    def render_to_list(self, render_list, indent_level):
        rendered_items = ', '.join([self._render_item(x) for x in self.items])
        self.clause.header.set_content(rendered_items)
        self.clause.render_to_list(render_list, indent_level=indent_level)

Suite.with_ = lambda self, expression, as_=None: \
    self.add(WithStatement(expression, as_=as_, parent=self))


class DefStatement(CompoundStatement):
    def __init__(self, name, parameter_list=None, decorators=None, parent=None,
                 render_inline=None):
        if not parent:
            raise Py2PyException('Function definition requires parent')
        super(DefStatement, self).__init__(parent)
        self.name = name
        self.parameter_list = parameter_list or []
        self.clause = Clause('def', content='', parent=parent,
                             decorators=decorators,
                             render_inline=render_inline)

    def write(self, statement):
        self.clause.write(statement)
        return self

    def render_to_list(self, render_list, indent_level):
        func_str = '%s(%s)' % (self.name, ', '.join(self.parameter_list))
        self.clause.header.set_content(func_str)
        self.clause.render_to_list(render_list, indent_level=indent_level)

Suite.def_ = lambda self, name, parameter_list=None, decorators=None: \
    self.add(DefStatement(name, parameter_list=parameter_list,
                          decorators=decorators, parent=self))


class ClassStatement(CompoundStatement):
    def __init__(self, name, bases=None, old_style=False, decorators=None,
                 parent=None,
                 render_inline=None):
        self.name = name
        if not bases and not old_style:
            bases = ['object']
        self.bases = bases
        if not parent:
            raise Py2PyException('Class definition requires parent')
        super(ClassStatement, self).__init__(parent)
        self.clause = Clause('class', content='', parent=parent,
                             decorators=decorators,
                             render_inline=render_inline)

    def write(self, statement):
        self.clause.write(statement)
        return self

    def render_to_list(self, render_list, indent_level):
        base_part = ('(%s)' % ','.join(self.bases)) if self.bases else ''
        content = '%s%s' % (self.name, base_part)
        self.clause.header.set_content(content)
        self.clause.render_to_list(render_list, indent_level=indent_level)
        render_list.append(base.BLOCK_STATEMENT_EOS)
        render_list.append(base.BLOCK_STATEMENT_EOS)


Suite.class_ = lambda self, name, bases=None, old_style=False, decorators=None: \
    self.add(ClassStatement(name, bases=bases, old_style=old_style,
                            decorators=decorators,
                            parent=self))
