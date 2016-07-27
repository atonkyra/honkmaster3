import time


class TestPlugin(object):
    __name__ = "TestPlugin"

    def get_messages(self):
        while True:
            yield 'test'
            time.sleep(5)