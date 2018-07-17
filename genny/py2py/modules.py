from .base import Suite
import os


class Module(Suite):
    def __init__(self, name, sort_imports=True):
        super(Module, self).__init__()
        self.name = name
        self.sort_imports = sort_imports
        self.imports = set()
        self.shebang_str = None
        self.encoding = None

    def add_import(self, expr):
        if expr.startswith('import ') or expr.startswith('from '):
            import_expr = expr
        else:
            import_expr = 'import ' + expr
        if not import_expr.endswith('\n'):
            import_expr += '\n'
        self.imports.add(import_expr)
        return self

    def set_shebang(self, shebang_str=''):
        if shebang_str:
            if not shebang_str.startswith('#!'):
                self.shebang_str = '#!' + shebang_str
        else:
            self.shebang_str = '#!/usr/bin/env python'
        if not self.shebang_str.endswith('\n'):
            self.shebang_str += '\n'
        return self

    def set_encoding(self, encoding):
        self.encoding = '# -*- coding: %s -*-\n' % encoding
        return self

    def render_to_list(self, render_list, indent_level):
        if self.shebang_str:
            render_list.append(self.shebang_str)
        if self.encoding:
            render_list.append(self.encoding)

        if self.sort_imports:
            self.imports = sorted(self.imports)
        render_list.extend(self.imports)

        super(Module, self).render_to_list(render_list,
                                           indent_level=indent_level)

    def save(self, dir_name):
        file_name = os.path.join(dir_name, self.name + '.py')
        with open(file_name, 'w') as f:
            f.write(self.render())