from .modules import Module
import os


class Package(object):
    def __init__(self, name):
        self.name = name
        self.init_module = Module('__init__')
        self.modules = []
        self.sub_packages = []

    def add_module(self, name):
        module = Module(name)
        self.modules.append(module)
        return module

    def add_sub_package(self, name):
        sub_package = Package(name)
        self.sub_packages.append(sub_package)
        return sub_package

    def write(self, statement):
        self.init_module.write(statement)
        return self

    def save(self, dir_name):
        package_path = os.path.join(dir_name, self.name)
        os.makedirs(package_path)
        self.init_module.save(package_path)
        for module in self.modules:
            module.save(package_path)
