from django import template
from django.utils.html import mark_safe
import math

register = template.Library()


@register.filter(name='split')
def split(value, sep=';'):
        return value.split(sep)


@register.filter(name='is_nan')
def is_nan(value):
    if str(value) != 'nan':
        return False
    else:
        return math.isnan(float(value))


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()

    for kwarg in kwargs:
        try:
            query.pop(kwarg)
        except KeyError:
            pass
    query.update(kwargs)
    return mark_safe(query.urlencode())
