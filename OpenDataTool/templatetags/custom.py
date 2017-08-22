from django import template
from django.utils.html import mark_safe
import math

register = template.Library()


@register.filter(name='split')
def split(value, sep=';'):
        return value.split(sep)


@register.filter(name='country_code')
def country_code(value):
    value = str(value).lower()
    if value == 'uk':
        value = 'gb'
    elif value == 'el':
        value = 'gr'
    return value


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


@register.filter(name='in_region')
def in_region(organisations, region_id):
    return organisations.filter(regionCode_id=region_id)


@register.filter(name='divide')
def divide(value, arg):
    try:
        return int(value)/float(arg)
    except (ValueError, ZeroDivisionError):
        return None


@register.filter(name='multiply')
def multiply(value, arg):
    return value*arg
