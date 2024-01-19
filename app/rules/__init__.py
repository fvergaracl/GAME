import os
import pkgutil

# Import all modules in this directory 
__all__ = []
for loader, module_name, is_pkg in pkgutil.iter_modules([
        os.path.dirname(__file__)]):
    __all__.append(module_name)
    module = loader.find_module(module_name).load_module(module_name)
    globals().update({name: getattr(module, name)
                      for name in dir(module) if not name.startswith('_')})


