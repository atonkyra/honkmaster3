from collections import OrderedDict


# http://stackoverflow.com/questions/15848674/how-to-configparse-a-file-keeping-multiple-values-for-identical-keys
class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if key in self:
            if isinstance(value, list):
                self[key].extend(value)
                return
            elif isinstance(value,str):
                return # ignore conversion list to string (line 554)
        super(MultiOrderedDict, self).__setitem__(key, value)
