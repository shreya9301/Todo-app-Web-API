# -*- coding: utf-8 -*-
import typing

class _NULL(object):
    pass
_NULL = _NULL()

def fix_object(data):
    if isinstance(data, dict):
        keys = list(data.keys())
        for key in keys:
            data[key] = to_object(data[key])
    elif isinstance(data, list):
        for index in range(len(data)):
            data[index] = to_object(data[index])
    elif isinstance(data, set):
        data2 = list(data)
        data.clear()
        for item in data2:
            data.add(to_object(item))

def to_object(data):
    if isinstance(data, Object):
        return data
    elif isinstance(data, dict):
        result = Object()
        for key, value in data.items():
            if isinstance(value, dict):
                value = to_object(value)
            result[key] = value
            setattr(result, key, value)
        return result
    elif isinstance(data, list):
        for index in range(len(data)):
            data[index] = to_object(data[index])
        return data
    elif isinstance(data, set):
        data = list(data)
        for index in range(len(data)):
            data[index] = to_object(data[index])
        return set(data)
    elif isinstance(data, tuple):
        data = list(data)
        for index in range(len(data)):
            data[index] = to_object(data[index])
        return tuple(data)
    return data

class Object(dict):
    """Dict object allow use dot path selector.

    Example:

    In [32]: from fastutils import dictutils
    
    In [33]: config = dictutils.Object()

    In [34]: config.listen = ('0.0.0.0', 6379)

    In [35]: config.listen
    Out[35]: ('0.0.0.0', 6379)

    In [36]: config['listen']
    Out[36]: ('0.0.0.0', 6379)

    In [39]: config['debug'] = True

    In [40]: config.debug
    Out[40]: True
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fix_object(self)
        for key, value in self.items():
            setattr(self, key, value)

    def __setitem__(self, key, value):
        if not isinstance(value, self.__class__):
            value = to_object(value)
        result = super().__setitem__(key, value)
        self.__dict__[key] = value
        return result

    def __setattr__(self, name, value):
        if not isinstance(value, self.__class__):
            value = to_object(value)
        self[name] = value
        result = super().__setattr__(name, value)
        return result

    def fix(self):
        fix_object(self)
        return self

    def update(self, *args, **kwargs):
        result = super().update(*args, **kwargs)
        fix_object(self)
        return result

    def pop(self, key, default=_NULL):
        if default == _NULL:
            result = super().pop(key)
        else:
            result = super().pop(key, default)
        if hasattr(self, key):
            delattr(self, key)
        return result

    def popitem(self):
        key, value = super().popitem()
        if hasattr(self, key):
            delattr(self, key)
        return key, value

    def setdefault(self, key, default=None):
        super().setdefault(key, default)
        fix_object(self)

    def clear(self):
        keys = list(super().keys())
        result = super().clear()
        for key in keys:
            if hasattr(self, key):
                delattr(self, key)
        return result
    
    def copy(self):
        return Object(super().copy())

def deep_merge(target: dict, data: dict) -> dict:
    """Merge the second dict into the first one deeply. Always returns the first dict reference.

    Example:

    In [14]: from fastutils import dictutils

    In [15]: data1 = {"a": {"b": {"c": "c"}}}

    In [16]: data2 = {"a": {"b": {"d": "d"}}}

    In [17]: dictutils.deep_merge(data1, data2)

    In [18]: data1
    Out[18]: {'a': {'b': {'c': 'c', 'd': 'd'}}}
    """
    for key2, value2 in data.items():
        value1 = target.get(key2, None)
        if isinstance(value1, dict) and isinstance(value2, dict):
            deep_merge(value1, value2)
        else:
            target[key2] = value2
    return target

def select(data : typing.Union[dict, Object, object], path : str, default_value : typing.Any = None) -> typing.Any:
    """Get field value in dot sperated path.

    Example:

    In [6]: from fastutils import dictutils

    In [7]: data = {
    ...: "a": {
    ...:     "b": {
    ...:         "c": "abc",
    ...:     }
    ...: }
    ...: }

    In [8]: dictutils.select(data, "a.b.c")
    Out[8]: 'abc'

    """
    paths = path.split(".")
    for path in paths:
        if isinstance(data, dict) and path in data:
            data = data[path]
        elif isinstance(data, (list, tuple)) and path.isdigit() and int(path) < len(data):
            data = data[int(path)]
        elif hasattr(data, path):
            data = getattr(data, path)
        else:
            return default_value
    return data

def touch(data : typing.Union[dict, Object, object], path : str, default_value : typing.Any) -> typing.Any:
    """Make sure data has the path.
    If data has the path, return the orignal value.
    If data NOT has the path, create a new path, and set to default_value, returns the default value.
    """
    result = select(data, path, _NULL)
    if result == _NULL:
        update(data, path, default_value)
        return default_value
    else:
        return result

def attrgetorset(data : typing.Union[dict, Object, object], key : str, default_value : typing.Any) -> typing.Any:
    """Get or set attr to data directly, and the key is a one level key.
    If data contains the key, get the original value.
    If data NOT contains the key, set the key to the default value.
    """
    if isinstance(data, dict):
        if not key in data:
            data[key] = default_value
        return data[key]
    elif isinstance(data, list):
        key = int(key)
        if key >= len(data):
            for _ in range(key + 1 - len(data)):
                data.append(None)
            data[key] = default_value
        return data[key]
    else:
        if not hasattr(data, key):
            setattr(data, key, default_value)
        return getattr(data, key)

def attrset(data : typing.Union[dict, Object, object], key : str, value : typing.Any) -> None:
    """Set attr to data directory, and the key is a one level key.
    If data contains the key, overrdie the original value with the new value.
    If data NOT contains the key, add a new key to the new value.
    """
    if isinstance(data, dict):
        data[key] = value
    elif isinstance(data, list):
        key = int(key)
        if key >= len(data):
            for _ in range(key + 1 - len(data)):
                data.append(None)
        data[key] = value
    else:
        setattr(data, key, value)

def update(data : typing.Union[dict, Object, object], path : str, value : typing.Any) -> typing.Union[dict, Object, object]:
    """Set attr to data, and the key is a dot-seperated-path.

    If data contains the key, override the original value with the new value.
    If data NOT contains the key, add a new key to the new value.


    """
    old_data = data
    is_object = isinstance(data, Object)
    paths = path.split(".")
    for index in range(0, len(paths) - 1):
        path = paths[index]
        path_next = paths[index + 1]
        if path_next.isdigit():
            next_empty_value = []
        else:
            if is_object:
                next_empty_value = Object()
            else:
                next_empty_value = {}
        data = attrgetorset(data, path, next_empty_value)
    path = paths[-1]
    attrset(data, path, value)
    return old_data

def ignore_none_item(data: dict) -> dict:
    """Returns a new dict that only contains empty-value field.

    None, empty list, empty dict: are treat as empty values.
    0, empty string, False: are NOT empty values.

    Example:

    In [3]: from fastutils import dictutils

    In [4]: data = {
    ...: "a": "",
    ...: "b": None,
    ...: "c": 0,
    ...: "d": False,
    ...: "e": [],
    ...: "f": {},
    ...: }

    In [5]: dictutils.ignore_none_item(data)
    Out[5]: {'a': '', 'c': 0, 'd': False}
    """
    result = {}
    for key, value in data.items():
        if value is None:
            continue
        if not value:
            if isinstance(value, (list, dict)):
                continue
        result[key] = value
    return result


def change(object_instance : typing.Union[object, dict], data_dict : typing.Union[object, dict], object_key : str, dict_key : str = None, do_update=True, ignore_empty_value=False) -> bool:
    """Update property value of object_instance, using the value from data_dict. If value changed, return True. If value is equals, return False.
    """
    dict_key = dict_key or object_key
    if isinstance(object_instance, dict):
        object_value = object_instance.get(object_key, None)
    else:
        object_value = getattr(object_instance, object_key, None)
    if isinstance(data_dict, dict):
        dict_value = data_dict.get(dict_key, None)
    else:
        dict_value = getattr(data_dict, dict_key, None)
    if (object_value == dict_value) or (ignore_empty_value and (object_value == "" or object_value == None) and (dict_value == "" or dict_value == None)):
        return False
    else:
        if do_update:
            if isinstance(object_instance, dict):
                object_instance[object_key] = dict_value
            else:
                setattr(object_instance, object_key, dict_value)
        return True

def changes(object_instance : typing.Union[object, dict], data_dict : typing.Union[object, dict], keys : typing.List[typing.Union[str, typing.Tuple[str, str]]], return_changed_keys=False, do_update=True, ignore_empty_value=False) -> typing.Union[bool, typing.Tuple[bool, list]]:
    """Update property values of object_instance, using the value form data_dict. If any property changed, return True. If values are equal, return False. keys is a list of string or string pair.
    """
    result = False
    changed_keys = []
    for key in keys:
        if isinstance(key, (tuple, set, list)) and len(key) > 1:
            object_key = key[0]
            dict_key = key[1]
        else:
            object_key = key
            dict_key = None
        changed = change(object_instance, data_dict, object_key, dict_key, do_update=do_update, ignore_empty_value=ignore_empty_value)
        if changed:
            changed_keys.append(object_key)
            result = True
    if return_changed_keys:
        return result, changed_keys
    else:
        return result

def prefix_key(data, prefix):
    """Add a prefix for all keys.

    Example:

    In [41]: from fastutils import dictutils

    In [42]: dictutils.prefix_key({"id": 1, "name": "mktg"}, 'department')
    Out[42]: {'departmentId': 1, 'departmentName': 'mktg'}

    """
    data2 = {}
    for key, value in data.items():
        key = prefix + key.capitalize()
        data2[key] = value
    return data2


def diff(object_instance1: dict, object_instance2: dict) -> typing.Tuple[list, list, list]:
    """Find keys that changed. Returns: created_keys, updated_keys, deleted_keys
    """
    deleted_keys = []
    updated_keys = []
    created_keys = []

    keys1 = set(object_instance1.keys())
    keys2 = set(object_instance2.keys())

    deleted_keys = list(keys1 - keys2)
    created_keys = list(keys2 - keys1)
    both_keys = keys1.intersection(keys2)
    for key in both_keys:
        if object_instance1[key] != object_instance2[key]:
            updated_keys.append(key)
    
    return created_keys, updated_keys, deleted_keys
