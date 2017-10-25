import glob
import importlib
import logging
import sys

from os.path import dirname, basename


def add_plugin(target, name, plugin):
    target[name] = plugin


logger = logging.getLogger('plugins')
available_plugins = {}
candidate_plugins = glob.glob(dirname(__file__)+'/*.py')
for plugin in candidate_plugins:
    plugin_module_name = basename(plugin).split('.')[0]
    if plugin_module_name in ['__init__']:
        continue
    try:
        importlib.import_module('plugins.%s' % plugin_module_name)
        add_plugin(
            available_plugins,
            plugin_module_name,
            sys.modules["plugins.%s" % plugin_module_name].__plugin_class__
        )
        logger.info('imported plugin %s', plugin_module_name)
    except BaseException as be:
        logger.error('plugin load failed: %s', be)
