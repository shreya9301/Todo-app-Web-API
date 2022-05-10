from pprint import pprint

import djclick as click
from django_apiview.extras.cache_admin import auto_setup_cleaners


@click.command()
def list_cache_entries():
    related_models_mapping, cache_cleaners = auto_setup_cleaners()

    print("Cache related models mapping:")
    pprint(related_models_mapping)

    print("Cache cleaners")
    pprint(cache_cleaners)
