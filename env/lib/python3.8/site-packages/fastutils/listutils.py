# -*- coding: utf-8 -*-
import typing

def int_list_to_bytes(intlist):
    from .strutils import ints2bytes
    return ints2bytes(intlist)

def pad(thelist, size, padding):
    if len(thelist) < size:
        for _ in range(size - len(thelist)):
            thelist.append(padding)
    return thelist

def chunk(thelist, size, with_padding=False, padding=None):
    data = []
    start = 0
    while True:
        if len(thelist) < size:
            if with_padding:
                pad(thelist, size, padding)
            data.append(thelist)
            break
        data.append(thelist[start:start+size])
        thelist = thelist[start+size:]
        if not thelist:
            break
    return data

def clean_none(thelist):
    """Remove None or empty element in thelist.
    """
    return [element for element in thelist if element]

ignore_none_element = clean_none


def unique(thelist):
    """Remove duplicated elements from the list.
    """
    result = []
    for element in thelist:
        if not element in result:
            result.append(element)
    return result

def replace(thelist, map, inplace=False):
    """Replace element in thelist, the map is collection of {old_value: new_value}.
    
    inplace == True, will effect the original list.
    inplace == False, will create a new list to return.
    """
    if inplace:
        for index in range(len(thelist)):
            value = thelist[index]
            if value in map:
                thelist[index] = map[value]
        return thelist
    else:
        newlist = []
        thelist = list(thelist)
        for index in range(len(thelist)):
            value = thelist[index]
            if value in map:
                newlist.append(map[value])
            else:
                newlist.append(value)
        return newlist

def append_new(thelist, value):
    """Append new value and only new value to the list.
    """
    if not value in thelist:
        thelist.append(value)
    return value

def group(thelist):
    """Count every element in thelist. e.g. ["a", "b", "c", "a", "b", "b"] => {"a": 2, "b": 3, "c": 1}.
    """
    info = {}
    for x in thelist:
        if x in info:
            info[x] += 1
        else:
            info[x] = 1
    return info


def compare(old_set, new_set):
    """Compare old_set and new_set, return set_new, set_delete, set_update.
    """
    old_set = set(old_set)
    new_set = set(new_set)

    set_new = new_set - old_set
    set_delete = old_set - new_set
    set_update = old_set.intersection(new_set)

    return set_new, set_delete, set_update

def first(*thelist, check=lambda x: x, default=None):
    """Return first non-none value. check is a callable function that returns the real value.
    """
    for value in thelist:
        if check(value) != None:
            return value
    return default


class CyclicDependencyError(ValueError):
    pass

def topological_sort(*thelists):
    mapping = {}
    for thelist in thelists:
        for element in thelist:
            if not element in mapping:
                mapping[element] = set()
        for index in range(1, len(thelist)):
            prev = thelist[index-1]
            current = thelist[index]
            mapping[current].add(prev)
    result = []
    while True:
        oks = []
        for k in list(mapping.keys()):
            v = mapping[k]
            if not len(v):
                result.append(k)
                oks.append(k)
                del mapping[k]
        if not oks:
            break
        else:
            for ok in oks:
                for k, v in mapping.items():
                    if ok in v:
                        v.remove(ok)
    if mapping:
        raise CyclicDependencyError()
    return result

def topological_test(thelist, tester):
    last_index = -1
    for element in tester:
        index = thelist.index(element)
        if index < last_index:
            return False
        last_index = index
    return True

def is_ordered(thelist, reverse=False):
    if reverse:
        for index in range(1, len(thelist)):
            if thelist[index] > thelist[index-1]:
                return False
        return True
    else:
        for index in range(1, len(thelist)):
            if thelist[index] < thelist[index-1]:
                return False
        return True

def list2dict(thelist, fields):
    """Turn list to dict, using keys in fields.

    Examples:

    In [1]: from fastutils import listutils

    In [2]: listutils.list2dict([1,2,3], ['a', 'b'])
    Out[2]: {'a': 1, 'b': 2}

    In [3]: listutils.list2dict([1,2,3], ['a', 'b', 'c'])
    Out[3]: {'a': 1, 'b': 2, 'c': 3}

    In [4]: listutils.list2dict([1,2,3], ['a', 'b', 'c', 'd'])
    Out[4]: {'a': 1, 'b': 2, 'c': 3, 'd': None}
    """
    result = {}
    thelistlength = len(thelist)
    field_infos = []
    for field in fields:
        if isinstance(field, str):
            field_info = (field, None)
        elif isinstance(field, (tuple, list)):
            field_name = field[0]
            if len(field) >= 2:
                field_default = field[1]
            field_info = (field_name, field_default)
        field_infos.append(field_info)
    for index, field_info in enumerate(field_infos):
        if index < thelistlength:
            result[field_info[0]] = thelist[index]
        else:
            result[field_info[0]] = field_info[1]
    return result


def compare_execute(old_data, new_data, create_callback, delete_callback, change_callback, old_key, new_key=None):
    """Compare two list, find elements to create/delete/change, and do callbacks.
    
    Returns elements of: (created, deleted, changed).
    """
    new_key = new_key or old_key

    old_mapping = {}
    new_mapping = {}

    for data in old_data:
        key = old_key(data)
        old_mapping[key] = data
    
    for data in new_data:
        key = new_key(data)
        new_mapping[key] = data
    
    old_keys = set(list(old_mapping.keys()))
    new_keys = set(list(new_mapping.keys()))

    create_keys = new_keys - old_keys
    change_keys = new_keys.intersection(old_keys)
    delete_keys = old_keys - new_keys

    created = []
    if create_callback:
        for key in create_keys:
            data = new_mapping[key]
            result = create_callback(key, data)
            if not result is None:
                created.append(result)
        
    changed = []
    if change_callback:
        for key in change_keys:
            instance = old_mapping[key]
            data = new_mapping[key]
            result = change_callback(key, instance, data)
            if not result is None:
                changed.append(result)
    
    deleted = []
    if delete_callback:
        for key in delete_keys:
            instance = old_mapping[key]
            result = delete_callback(key, instance)
            if not result is None:
                deleted.append(result)
    
    return created, deleted, changed