from boto.dynamodb2.types import (STRING, STRING_SET, BINARY, BINARY_SET,
                                  NUMBER, NUMBER_SET)


class Attribute(object):
    """Declare the attribute of the model as a descriptor."""

    # (:class:`str`) The attribute name. It is assigned by Model meta class.
    attr_name = None

    # (:class:`bool`) `True` if the attribute is the hash key of the model.
    hash_key = False

    # (:class:`bool`) `True` if the attribute is the range key of the model.
    range_key = False

    # (:class:`str`) Type string defined in :mod:`boto.dynamodb2.types`
    type = None

    def __init__(self, hash_key=False, range_key=False,
                 null=False, default=None):
        self.hash_key = hash_key
        self.range_key = range_key
        self.null = null
        self.default = default

    def __get__(self, obj, cls=None):
        if obj is not None:
            return obj._data.get(self.attr_name)
        return self

    def __set__(self, obj, value):
        if obj is not None:
            obj._data[self.attr_name] = value
            return
        raise ValueError('Cannot change the class attribute')


class StringAttribute(Attribute):
    type = STRING


class StingSetAttribute(Attribute):
    type = STRING_SET


class BinaryAttribute(Attribute):
    type = BINARY


class BinarySetAttribute(Attribute):
    type = BINARY_SET


class NumberAttribute(Attribute):
    type = NUMBER


class NumberSetAttribute(Attribute):
    type = NUMBER_SET