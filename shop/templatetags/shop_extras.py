from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Get value from dict by key in template: dict|dict_get:key"""
    if isinstance(d, dict):
        return d.get(key, 0)
    return 0
