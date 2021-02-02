# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import pdb
import importlib
import types


class FastLoader(types.ModuleType):
    """ 快速导入模块工具
    """
    def __init__(self, local_name, parent_module_globals, name):  
        # pylint: disable=super-on-old-class
        self._local_name = local_name
        self._parent_module_globals = parent_module_globals

        super(FastLoader, self).__init__(name)

    def _load(self):
        # Import the target module and insert it into the parent's namespace
        module = importlib.import_module(self.__name__)
        print( module)
        self._parent_module_globals[self._local_name] = module  # 将真实的 module 用本地名做绑定
        print(type(self._parent_module_globals))
        # pdb.set_trace()
        # Update this object's dict so that if someone keeps a reference to the    
        # FastLoader, lookups are efficient (__getattr__ is only called on lookups
        # that fail).
        self.__dict__.update(module.__dict__)

        return module
    
    def __getattr__(self, item):
        module = self._load()
        return getattr(module, item)

    def __dir__(self):
        module = self._load()
        return dir(module)


if __name__ == '__main__':
    fl = FastLoader('contrib', globals(), 'tensorflow.contrib')
    print(fl.__name__)
    pdb.set_trace()
    print(dir(fl))
