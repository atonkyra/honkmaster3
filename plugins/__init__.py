import logging


def add_plugin(target, name, plugin):
    target[name] = plugin


logger = logging.getLogger('plugins')
available_plugins = {}
import plugins.filemonitor
add_plugin(available_plugins, 'filemonitor', plugins.filemonitor.FileMonitor)
import plugins.testplugin
add_plugin(available_plugins, 'testplugin', plugins.testplugin.TestPlugin)

try:
    import plugins.zbusclient
    add_plugin(available_plugins, 'zbusclient', plugins.zbusclient.ZBusClient)
except BaseException as be:
    logger.error(be)
