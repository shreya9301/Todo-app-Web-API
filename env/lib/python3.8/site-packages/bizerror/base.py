# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import
import json
import typing

LANGUAGE = "zh-hans"

ERROR_INFO = {
    "en": {},
    "zh-hans": {}
}


def clean_language_name(language):
    if language is None:
        return LANGUAGE
    else:
        return language.lower().strip().replace("_", "-")

def set_language(language):
    global LANGUAGE
    language = clean_language_name(language)
    LANGUAGE = language

def set_error_info(language, class_name, code, message):
    language = clean_language_name(language)
    if not language in ERROR_INFO:
        ERROR_INFO[language] = {}
    ERROR_INFO[language][class_name] = {
        "code": code,
        "message": message,
    }

def get_error_info(class_name, language=None):
    language = clean_language_name(language)
    return ERROR_INFO[language][class_name]

class classproperty(property):
    """Subclass property to make classmethod properties possible"""
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

class BizErrorBase(RuntimeError):
    """Base class of all errors.
    """

    def __init__(self, message=None, code=None, **kwargs):
        if isinstance(message, BizErrorBase):
            code = code or message.code
            message = message.message
        else:
            # load default code & message
            info = get_error_info(self.__class__.__name__)
            code = code or info["code"]
            message = message or info["message"]
            # message format
            if not isinstance(message, str):
                message = str(message)
        if kwargs:
            message = message.format(**kwargs)
        super().__init__(code, message)

    def __repr__(self):
        return str(self)

    def __str__(self):
        result = json.dumps({
            "code": self.args[0],
            "message": self.args[1]
        }, ensure_ascii=False)
        return result

    def update(self, **kwargs):
        self.args = (self.args[0], self.args[1].format(**kwargs))

    @property
    def code(self):
        return self.args[0]

    @property
    def message(self):
        return self.args[1]

    @property
    def json(self):
        return {
            "code": self.code,
            "message": self.message,
        }


class OK(BizErrorBase):
    pass
set_error_info("en", "OK", 0, "OK")
set_error_info("zh-hans", "OK", 0, "正常。")

class BizError(BizErrorBase):
    pass
set_error_info("en", "BizError", 1, "Error")
set_error_info("zh-hans", "BizError", 1, "异常！")
