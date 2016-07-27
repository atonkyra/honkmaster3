import plugins.filemonitor
import plugins.testplugin


def add_plugin(target, name, plugin):
    target[name] = plugin


available_plugins = {}
add_plugin(available_plugins, 'filemonitor', plugins.filemonitor.FileMonitor)
add_plugin(available_plugins, 'testplugin', plugins.testplugin.TestPlugin)
