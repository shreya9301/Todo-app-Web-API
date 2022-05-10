import re
import uuid
import logging

from django.apps import apps
from django.db.models import QuerySet
from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django_redis import get_redis_connection

from django_middleware_global_request.middleware import get_request

from ..views import cache as decorator_cache

logger = logging.getLogger(__name__)

class CacheCleanerBase(object):

    def __init__(self, key, model, cache_connection=None, **kwargs):
        self.key = key
        self.model = isinstance(model, str) and apps.get_model(model) or model
        self.cache_connection = cache_connection or get_redis_connection()
        self.kwargs = kwargs
        self.setup()
    
    def setup(self):
        logger.info("Cache setup cleaner, key={0}, model={1}, cleaner={2}".format(self.key, self.model, self.__class__.__name__))
        post_save.connect(self.clean, sender=self.model)
        post_delete.connect(self.clean, sender=self.model)
        return self

    def clean(self, sender, instance, **kwargs):
        try:
            self._clean(sender, instance, **kwargs)
        except Exception:
            logger.exception("Cache do clean failed.")

    def _clean(self, sender, instance, **kwargs):
        key_patterns = self.get_clean_keys(instance)
        if key_patterns:
            logger.info("clean cache: key_patterns={0}".format(key_patterns))
            self.delete_key_patterns(key_patterns)
        else:
            logger.info("clean cache: none")
        return self

    def delete_key_patterns(self, key_patterns):
        keys = []
        for key_pattern in key_patterns:
            if "*" in key_pattern:
                keys += self.cache_connection.keys(key_pattern)
            else:
                keys.append(key_pattern)
        keys = list(set(keys))
        logger.info("{} keys deleted".format(len(keys)))
        if keys:
            self.cache_connection.delete(*keys)
    
    def get_clean_keys(self, instance):
        raise NotImplementedError()

class SimpleCacheCleaner(CacheCleanerBase):
    """SimpleCacheCleaner Cache cleaner should only do once per request.
    """
    def get_clean_keys(self, instance):
        request = get_request()
        doneflag_key = "SimpleCacheCleaner:{}:doneflag".format(id(self))
        if hasattr(request, doneflag_key):
            return []
        setattr(request, doneflag_key, True)
        return [
            re.sub('\{[^\}]*\}', '*', self.key),
        ]

class CleanByModelFields(CacheCleanerBase):
    fields = []
    extra = {}

    def get_clean_keys(self, instance):
        info = self.get_fields_mapping(instance)
        return [
            self.key.format(**info, **self.extra)
        ]
    
    def get_fields_mapping(self, instance):
        info = {}
        for field in self.fields:
            if isinstance(field, (list, tuple)):
                model_field = field[1]
                field = field[0]
            else:
                model_field = field
            info[field] = getattr(instance, model_field, None)
        return info

    @classmethod
    def make(cls, *fields, **kwargs):
        suffix = str(uuid.uuid4()).replace("-", "")
        cleaner_class = type("CleanByModelFields_" + suffix, (cls,), {"fields": fields, "extra": kwargs})
        return cleaner_class

class CleanByRelatedModelFields(CacheCleanerBase):
    related = None
    fields = []
    extra = {}

    def get_clean_keys(self, instance):
        infos = self.get_related_objects_fields_mapping(instance)
        keys = []
        for info in infos:
            keys.append(self.key.format(**info, **self.extra))
        return keys

    def get_related_objects_fields_mapping(self, instance):
        infos = []
        related_instances = getattr(instance, self.related)
        if isinstance(related_instances, QuerySet):
            related_instances = related_instances.all()
        else:
            related_instances = [related_instances]
        for related_instance in related_instances:
            info = {}
            for field in self.fields:
                if isinstance(field, (list, tuple)):
                    model_field = field[1]
                    field = field[0]
                else:
                    model_field = field
                info[field] = getattr(related_instance, model_field, None)
            infos.append(info)
        return infos

    @classmethod
    def make(cls, related, *fields, **kwargs):
        suffix = str(uuid.uuid4()).replace("-", "")
        cleaner_class = type("CleanByRelatedModelFields_" + suffix, (cls,), {"related": related, "fields": fields, "extra": kwargs})
        return cleaner_class

class CleanByImplicitRelatedModelFields(CacheCleanerBase):
    related_model = None
    related_fields = []
    fields = []
    extra = {}

    def get_clean_keys(self, instance):
        infos = self.get_related_objects_fields_mapping(instance)
        keys = []
        for info in infos:
            keys.append(self.key.format(**info, **self.extra))
        return keys
    
    def get_related_objects_fields_mapping(self, instance):
        infos = []
        params = {}
        for related_field in self.related_fields:
            if isinstance(related_field, (list, tuple)):
                to_field = related_field[1]
                related_field = related_field[0]
            else:
                to_field = related_field
            params[to_field] = getattr(instance, related_field, None)
        related_instances = self.related_model.objects.filter(**params).all()
        for related_instance in related_instances:
            info = {}
            for field in self.fields:
                if isinstance(field, (list, tuple)):
                    model_field = field[1]
                    field = field[0]
                else:
                    model_field = field
                info[field] = getattr(related_instance, model_field, None)
            infos.append(info)
        return infos

    @classmethod
    def make(cls, related_model, related_fields, *fields, **kwargs):
        if isinstance(related_fields, str):
            related_fields = [related_fields]
        suffix = str(uuid.uuid4()).replace("-", "")
        cleaner_class = type("CleanByImplicitRelatedModelFields_" + suffix, (cls,), {"related_model": related_model, "related_fields": related_fields, "fields": fields, "extra": kwargs})
        return cleaner_class

CACHE_CLEANERS = {}

def _get_model_name(model):
    if isinstance(model, str):
        return model
    return ".".join([model._meta.app_label, model._meta.model_name])

def setup_cleaner(key, model, cleaner=None):
    model_name = _get_model_name(model)
    cleaner = cleaner or SimpleCacheCleaner
    cleaner_key = ":".join([key, model_name])
    if not cleaner_key in CACHE_CLEANERS:
        CACHE_CLEANERS[cleaner_key] = cleaner(key, model)

def auto_discover_caches():
    from django.urls import reverse
    from django.urls import NoReverseMatch
    from django.urls import Resolver404
    try:
        reverse("none-exist-view")
    except NoReverseMatch:
        pass
    except Resolver404:
        pass
    except Exception:
        logger.exception("auto_discover_caches failed on load url configs...")
    return decorator_cache.related_models_mapping

def auto_setup_cleaners():
    logger.info("Cache auto setup cleaners...")
    related_models_mapping = auto_discover_caches()
    for entry_point, info in related_models_mapping.items():
        for model in info.get("related_models", []):
            if isinstance(model, (list, tuple)):
                cleaner = model[1]
                model = model[0]
            else:
                cleaner = None
            key = info.get("key", None)
            if key and model:
                setup_cleaner(key, model, cleaner)
    logger.info("Cache auto setup cleaners done!")
    return related_models_mapping, CACHE_CLEANERS