import time


class TestPlugin(object):
    __name__ = "TestPlugin"

    def get_messages(self):
        while True:
            # yield 'test with a fairly long string of characters'
            yield 'test'
            time.sleep(1)


__plugin_class__ = TestPlugin
