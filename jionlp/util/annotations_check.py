# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


def remove_undocumented(module_name, allowed_exception_list=None,
                        doc_string_modules=None):
    """ Removes symbols in a module that are not referenced by a docstring.

    Args:
        module_name: the name of the module (usually `__name__`).
        allowed_exception_list: a list of names that should not be removed.
        doc_string_modules: a list of modules from which to take the docstrings.
        If None, then a list containing only the module named `module_name` is used.

        Furthermore, if a symbol previously added with `add_to_global_whitelist`,
        then it will always be allowed. This is useful for internal tests.

      Returns:
        None
    """
    current_symbols = set(dir(_sys.modules[module_name]))
    should_have = make_all(module_name, doc_string_modules)
    should_have += allowed_exception_list or []
    extra_symbols = current_symbols - set(should_have)
    target_module = _sys.modules[module_name]
    for extra_symbol in extra_symbols:
        # Skip over __file__, etc. Also preserves internal symbols.
        if extra_symbol.startswith('_'): continue
        fully_qualified_name = module_name + '.' + extra_symbol
        _HIDDEN_ATTRIBUTES[fully_qualified_name] = (target_module,
                                                    getattr(target_module,
                                                            extra_symbol))
        delattr(target_module, extra_symbol)

