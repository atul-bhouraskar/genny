from __future__ import absolute_import, unicode_literals


from contextlib import contextmanager
import copy
import six


INDENT = ' ' * 4  # 4 spaces
EOS = ';'  # end of statement
EOL = '\n'  # unix end of line


class IndentedRenderList(list):
    def __init__(self, *args, **kwargs):
        super(IndentedRenderList, self).__init__(*args, **kwargs)
        self.indent_level = 0

    def append(self, text, do_indent=True, add_eos=False, add_eol=False):
        if do_indent:
            text = self.indent_text(text)
        if add_eos:
            text += EOS
        if add_eol:
            text += EOL
        super(IndentedRenderList, self).append(
            text
        )

    def append_blank_line(self):
        self.append('', add_eol=True)

    @contextmanager
    def indent_block(self):
        self.indent_level += 1
        yield
        if self.indent_level > 0:
            self.indent_level -= 1

    def indent_text(self, text):
        if self.indent_level > 0:
            return INDENT * self.indent_level + text
        else:
            return text


class Renderable(object):
    def render_to_list(self, render_list, do_indent=True):
        raise NotImplementedError('render_to_list() should be implemented by '
                                  'all statements')

    def render(self):
        render_list = IndentedRenderList()
        self.render_to_list(render_list)
        return ''.join(render_list)


class Statement(Renderable):
    def render_to_list(self, render_list, do_indent=True):
        raise NotImplementedError('render_to_list() should be implemented by '
                                  'all statements')


class SimpleStatement(Statement):
    def __init__(self, text, add_eos=True, add_eol=True):
        self.text = str(text)
        self.add_eos = add_eos
        self.add_eol = add_eol
        super(SimpleStatement, self).__init__()

    def render_to_list(self, render_list, do_indent=True):
        text = self.text.strip()
        if self.add_eos and text and text[-1] != EOS:
            text += EOS
        render_list.append(text, add_eol=self.add_eol)


class BlankLine(Statement):
    def render_to_list(self, render_list, do_indent=False):
        render_list.append_blank_line()


class CodeFragment(Renderable):
    """
    A collection of statements
    """
    def __init__(self):
        self.statements = []

    def write(self, statement):
        self.add(statement)
        return self

    def add(self, statement):
        if isinstance(statement, six.string_types):
            if statement.strip() == '':
                statement = BlankLine()
            else:
                # convert to SimpleStatement
                statement = SimpleStatement(statement)

        self.statements.append(statement)
        return statement

    def clear(self):
        self.statements.clear()

    def create_copy(self):
        c = CodeFragment()
        c.statements = copy.deepcopy(self.statements)
        return c

    def is_empty(self):
        return len(self.statements) == 0

    def render_to_list(self, render_list, do_indent=True):
        for statement in self.statements:
            statement.render_to_list(render_list, do_indent=do_indent)


class CodeBlock(Renderable):
    """
    A code fragment enclosed in braces
    """
    def __init__(self, add_eos=False):
        self.add_eos = add_eos
        self.code_fragment = CodeFragment()
        super(CodeBlock, self).__init__()

    def write(self, statement):
        self.code_fragment.write(statement)
        return self

    def add(self, statement):
        return self.code_fragment.add(statement)

    def clear(self):
        self.code_fragment.clear()

    def __getattr__(self, item):
        if item == '__setstate__':
            # Bug 4074
            # allow deepcopy to work in py3.6
            # if we delegate this, we get infinite recursion
            # let deepcopy know that we don't have a __setstate__ method
            raise AttributeError()
        # delegate to code fragment
        return getattr(self.code_fragment, item)

    def is_empty(self):
        return self.code_fragment.is_empty()

    def render_to_list(self, render_list, do_indent=False):
        render_list.append('{\n', do_indent)
        with render_list.indent_block():
            self.code_fragment.render_to_list(render_list)
        render_list.append('}', add_eos=self.add_eos, add_eol=True)


class BlockStatement(Statement):
    """
    Statement containing a code block eg. if, for, etc
    """
    def __init__(self, delegated_block=None):
        super(BlockStatement, self).__init__()
        self.delegated_block = delegated_block  # type: CodeBlock

    def delegate_to(self, block):
        self.delegated_block = block

    def __getattr__(self, item):
        if self.delegated_block:
            return getattr(self.delegated_block, item)
        else:
            raise AttributeError()

    def write(self, statement):
        if self.delegated_block:
            self.delegated_block.write(statement)
        return self

    def add(self, statement):
        if self.delegated_block:
            return self.delegated_block.add(statement)

    def render_to_list(self, render_list, do_indent=True):
        raise NotImplementedError('render_to_list() should be implemented by '
                                  'all statements')


def quote_text(text, quote_char="'"):
    # return quote_char + text + quote_char
    escaped = repr(text)  # returns u"text\'s representation"
    if escaped[0] == 'u':
        return escaped[1:]
    else:
        return escaped


def render_item(item, render_list, do_indent):
    if isinstance(item, six.string_types):
        render_list.append(item, do_indent=do_indent)
    elif hasattr(item, 'render_to_list'):
        item.render_to_list(render_list, do_indent=do_indent)
    else:
        render_list.append(str(item), do_indent=do_indent)
