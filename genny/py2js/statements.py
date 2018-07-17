from __future__ import absolute_import, unicode_literals


import copy

from . import base


class Assign(base.Statement):
    def __init__(self, lhs, rhs, add_eos=True, add_eol=True):
        self.lhs = lhs
        self.rhs = rhs
        self.add_eos = add_eos
        self.add_eol = add_eol

    def render_to_list(self, render_list, do_indent=True):
        base.render_item(self.lhs, render_list, do_indent=do_indent)
        render_list.append(' = ', do_indent=False)
        base.render_item(self.rhs, render_list, do_indent=False)
        render_list.append('', do_indent=False,
                           add_eos=self.add_eos, add_eol=self.add_eol)


class Let(base.Statement):
    def __init__(self, var_name, rhs=None, type_str=None, add_let=True,
                 add_eos=True, add_eol=True):
        self.var_name = var_name
        self.rhs = rhs
        self.add_eos = add_eos
        self.add_eol = add_eol
        self.add_let = add_let
        self.type_str = type_str

    def render_to_list(self, render_list, do_indent=True):
        if self.type_str:
            TypeAnnotation(self.type_str).render_to_list(
                render_list,
                do_indent=do_indent
            )

        if self.add_let:
            render_list.append('let ', do_indent=do_indent)

        if self.rhs:
            Assign(
                lhs=self.var_name,
                rhs=self.rhs,
                add_eos=self.add_eos
            ).render_to_list(
                render_list,
                do_indent=do_indent if not self.add_let else False
            )
        else:
            render_list.append(self.var_name, do_indent=False,
                               add_eos=self.add_eos, add_eol=self.add_eol)


class MemberVarAssign(Let):
    def __init__(self, var_name, rhs, type_str=None,
                 add_eos=True, add_eol=True):
        super(MemberVarAssign, self).__init__('this.' + var_name,
                                              rhs=rhs,
                                              type_str=type_str,
                                              add_let=False,
                                              add_eos=add_eos,
                                              add_eol=add_eol)


class If(base.BlockStatement):
    def __init__(self, condition, indent_first_line=True):
        self.condition = condition
        self.indent_first_line = indent_first_line
        self.if_block = base.CodeBlock()
        self.else_if_blocks = []
        self.else_block = base.CodeBlock()

        super(If, self).__init__(delegated_block=self.if_block)

    def else_(self):
        return self.else_block

    def else_if_(self, condition):
        else_if_block = If(condition, indent_first_line=False)
        self.else_if_blocks.append(else_if_block)
        return else_if_block

    def render_to_list(self, render_list, do_indent=True):
        render_list.append('if ({}) '.format(self.condition),
                           do_indent=self.indent_first_line)
        self.if_block.render_to_list(render_list, do_indent=False)

        for else_if_block in self.else_if_blocks:  # type: If
            render_list.append('else ')
            else_if_block.render_to_list(render_list, do_indent=False)

        if not self.else_block.is_empty():
            render_list.append('else ')
            self.else_block.render_to_list(render_list, do_indent=False)


# monkey patch into code
base.CodeFragment.if_ = lambda self, condition: \
    self.add(If(condition))


class Param(object):
    def __init__(self, name, type_str):
        self.name = name
        self.type_str = type_str

    def render_annotation(self):
        return '@param {{{}}} {}'.format(self.type_str, self.name)

    def render_record_annotation(self):
        """
        Render annotation for record typedef
        """
        return '{}: {}'.format(self.name, self.type_str)


class Function(base.BlockStatement):
    def __init__(self, name='', params=None, return_type_str=None,
                 comment='', add_eos=False):
        self.name = name
        self.params = params or []  # type: list
        self.code_block = base.CodeBlock(add_eos=add_eos)
        self.return_type_str = return_type_str
        self.comment = comment

        super(Function, self).__init__(delegated_block=self.code_block)

    def render_to_list(self, render_list, do_indent=True):
        FunctionAnnotation(
            self.params,
            return_type_str=self.return_type_str,
            comment=self.comment
        ).render_to_list(
            render_list,
            do_indent=do_indent
        )
        render_list.append(
            'function {}({}) '.format(
                self.name,
                ', '.join([x.name for x in self.params])
            ),
            do_indent=do_indent
        )
        self.code_block.render_to_list(render_list, do_indent=do_indent)


base.CodeFragment.function_ = lambda self, name='', params=None: \
    self.add(Function(name, params))


class FunctionCall(base.SimpleStatement):
    def __init__(self, name, params=None, add_eos=True, add_eol=True):
        if not params:
            params = []
        super(FunctionCall, self).__init__(
            '{}({})'.format(name, ', '.join(params)),
            add_eos=add_eos,
            add_eol=add_eol
        )


base.CodeFragment.call_ = lambda self, name, params=None, add_eos=True: \
    self.add(FunctionCall(name, params, add_eos))


class Class(base.BlockStatement):
    def __init__(self, name='', base_class=None, add_eos=False):
        self.name = name
        self.base_class = base_class
        self.code_block = base.CodeBlock(add_eos=add_eos)
        self.constructor = None
        self.methods = []

        super(Class, self).__init__(delegated_block=self.code_block)

    def constructor_(self, params=None):
        self.constructor = ClassMethod('constructor', params)
        return self.constructor

    def add_method(self, name, is_static=False, params=None,
                   return_type_str=None, comment=''):
        method = ClassMethod(name, params, is_static=is_static,
                             return_type_str=return_type_str,
                             comment=comment)
        self.methods.append(method)
        return method

    def render_to_list(self, render_list, do_indent=True):
        # render using a temporary code block
        # this allows multiple calls to this method
        code_block = copy.deepcopy(self.code_block)

        declaration = 'class'
        if self.name:
            declaration += ' self.name'
        if self.base_class:
            declaration += ' extends {}'.format(self.base_class)

        render_list.append('{} '.format(declaration), do_indent=do_indent)

        if self.constructor:
            code_block.add(self.constructor)
        for method in self.methods:
            code_block.add(method)
        code_block.render_to_list(render_list, do_indent=do_indent)


base.CodeFragment.class_ = \
    lambda self, name='', base_class=None, add_eos=True: self.add(
        FunctionCall(name, base_class, add_eos)
    )


class ClassMethod(base.BlockStatement):
    def __init__(self, name, params=None, is_static=False,
                 return_type_str=None, comment=''):
        self.name = name
        self.params = params or []
        self.return_type_str = return_type_str
        self.is_static = is_static
        self.comment = comment
        self.code_block = base.CodeBlock()

        super(ClassMethod, self).__init__(delegated_block=self.code_block)

    def return_(self, value=None):
        self.code_block.add(Return(value))

    def render_to_list(self, render_list, do_indent=True):
        FunctionAnnotation(
            self.params,
            return_type_str=self.return_type_str,
            comment=self.comment
        ).render_to_list(
            render_list,
            do_indent=do_indent
        )
        render_list.append(
            '{}{}({}) '.format(
                'static ' if self.is_static else '',
                self.name,
                ', '.join([x.name for x in self.params])
            )
        )
        self.code_block.render_to_list(render_list, do_indent=False)


class SingleLineComment(base.Statement):
    def __init__(self, text):
        self.text = text.strip()

    def render_to_list(self, render_list, do_indent=True):
        render_list.append('// ' + self.text, add_eol=True)


class MultiLineComment(base.Statement):
    def __init__(self, text, prefix='  '):
        self.text = text.strip()
        self.prefix = prefix

    def render_to_list(self, render_list, do_indent=True):
        text_list = self.text.split(base.EOL)
        count = len(text_list)

        render_list.append('/*')
        for i, text in enumerate(text_list):
            if i == 0:
                line = self.prefix.strip() + ' ' + text
                line_indent = False  # continued from /*
            else:
                line = ' ' + self.prefix + text
                line_indent = True
            render_list.append(line.rstrip(),
                               do_indent=line_indent,
                               add_eol=count > 1)
        render_list.append(' */', add_eol=True)


class CodeBlockAnnotationComment(MultiLineComment):
    def __init__(self, text):
        super(CodeBlockAnnotationComment, self).__init__(
            text,
            prefix='* '
        )
        # ensure first line is empty
        self.text = base.EOL + self.text


class TypeAnnotation(MultiLineComment):
    def __init__(self, type_str):
        super(TypeAnnotation, self).__init__(
            '@type {{{}}}'.format(type_str),
            prefix='* '
        )


class FunctionAnnotation(CodeBlockAnnotationComment):
    def __init__(self, params, return_type_str=None, comment=''):
        text_list = []
        if comment:
            text_list.append(comment)
        for param in params:  # type: Param
            text_list.append(param.render_annotation())
        if return_type_str:
            text_list.append('@return {{{}}}'.format(return_type_str))
        super(FunctionAnnotation, self).__init__(base.EOL.join(text_list))


class RecordTypedefAnnotation(CodeBlockAnnotationComment):
    def __init__(self, params):
        param_list = []
        for param in params:  # type: Param
            param_list.append('  ' + param.render_record_annotation())
        text = '@typedef {{' + base.EOL + (',' + base.EOL).join(param_list) + \
               base.EOL + '}}'
        super(RecordTypedefAnnotation, self).__init__(text)


class RecordTypedef(base.Statement):
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def render_to_list(self, render_list, do_indent=True):
        RecordTypedefAnnotation(self.params).render_to_list(
            render_list, do_indent=do_indent
        )
        base.SimpleStatement(
            self.name, add_eos=True
        ).render_to_list(
            render_list, do_indent=do_indent
        )
        render_list.append_blank_line()


class ObjectLiteralMember(base.Statement):
    def __init__(self, lhs, rhs, add_comma=True, add_eol=True):
        self.lhs = lhs
        self.rhs = rhs
        self.add_comma = add_comma
        self.add_eol = add_eol

    def render_to_list(self, render_list, do_indent=True):
        base.render_item(self.lhs, render_list, do_indent=do_indent)
        render_list.append(': ', do_indent=False)
        base.render_item(self.rhs, render_list, do_indent=False)
        if self.add_comma:
            render_list.append(',', do_indent=False, add_eol=False)
        if self.add_eol:
            render_list.append('', add_eol=True, do_indent=False)


class ObjectLiteral(base.Renderable):
    def __init__(self, add_eos=True, add_eol=True):
        super(ObjectLiteral, self).__init__()
        self.add_eos = add_eos
        self.add_eol = add_eol
        self.members = []

    def add_member(self, lhs, rhs):
        self.members.append(ObjectLiteralMember(lhs, rhs))

    def render_to_list(self, render_list, do_indent=False):
        render_list.append('{\n', do_indent=False)
        with render_list.indent_block():
            for member in self.members:  # type: ObjectLiteralMember
                member.render_to_list(render_list, do_indent=do_indent)

        render_list.append('}', add_eos=self.add_eos, add_eol=self.add_eol)


class Return(base.Statement):
    def __init__(self, value, add_eos=True, add_eol=True):
        self.value = value
        self.add_eos = add_eos
        self.add_eol = add_eol
        super(Return, self).__init__()

    def render_to_list(self, render_list, do_indent=True):
        render_list.append('return ')
        base.render_item(self.value, render_list, do_indent=do_indent)
        render_list.append('', do_indent=False,
                           add_eos=self.add_eos,
                           add_eol=self.add_eol)
