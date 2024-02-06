# import all .py and export automatically

import os
import glob

# get all .py files in the current directory
modules = glob.glob(os.path.dirname(__file__) + "/*.py")

# import all .py files
__all__ = [os.path.basename(
    f)[:-3] for f in modules if os.path.basename(f) != '__init__.py' and 
    os.path.basename(f) != '__pycache__' and 
    os.path.basename(f) != 'base_strategy.py']


# export all .py files
for module in __all__:
    __import__(module, locals(), globals())
