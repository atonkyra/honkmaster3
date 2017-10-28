# HonkMaster3

HonkMaster3 is an IRC bot that build upon earlier HonkMasters, hopefully with less fail in the progress. Main purpose
of a honkmaster is to relay messages from source X to IRC and perhaps from IRC to somewhere else too.

## Usage

```$ ./honkmaster3.py -s irc.server.tld -c '#testhonk' -n honkleet -p filemonitor:/tmp/testfile```

## Writing plugins

Writing plugins is simple. The following creates a plugin with minimum required implemented functions.

```
import time


class MyPlugin(object):
    __name__ = "MyPlugin"

    def get_messages(self):
        """
        The bot will send the yielded messages to the targeted channel.
        """
        while True:
            # yield 'test with a fairly long string of characters'
            yield 'test'
            time.sleep(60)


__plugin_class__ = TestPlugin

```

If you need to implement an inbound message handler for the channel you simply need to add a `handle_message` function.

```
def handle_message(self, msg):
    print(msg)
```
