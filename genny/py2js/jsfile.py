from __future__ import absolute_import, unicode_literals


from . import base
from .import statements


class JSFile(base.CodeFragment):
    def __init__(self):
        super(JSFile, self).__init__()
        self.goog_provides = []
        self.goog_requires = []
        self.comment = None

    def add_goog_provide(self, provides_text):
        self.goog_provides.append(provides_text)

    def add_goog_requires(self, requires_text):
        self.goog_requires.append(requires_text)

    def add_file_comment(self, text):
        self.comment = text

    def render_to_list(self, render_list, do_indent=True):
        if self.comment:
            statements.MultiLineComment(
                self.comment
            ).render_to_list(
                render_list,
                do_indent=do_indent
            )
            render_list.append_blank_line()
        for provide in sorted(self.goog_provides):
            render_list.append(
                'goog.provide({})'.format(base.quote_text(provide)),
                do_indent=do_indent,
                add_eos=True,
                add_eol=True
            )
        render_list.append('\n')

        for require in sorted(self.goog_requires):
            render_list.append(
                'goog.require({})'.format(base.quote_text(require)),
                do_indent=do_indent,
                add_eos=True,
                add_eol=True
            )
        render_list.append('\n')

        super(JSFile, self).render_to_list(render_list)

    def save(self, path):
        with open(path, 'w') as f:
            f.write(self.render().encode('utf-8'))
