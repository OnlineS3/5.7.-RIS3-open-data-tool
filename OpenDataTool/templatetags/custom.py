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


@register.filter(name='zip')
def zip_lists(a, b):
    a = a.split(';')
    b = b.split(';')
    if len(a) != len(b):
        b = ['']*len(a)
    return zip(a, b)


@register.filter(name='parse_id')
def parse_id(bookmarks, b_id):
    bookmark_k = ' '.join(map(str, bookmarks.keys()))
    if str(b_id) in bookmark_k:
        return True
    return False


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


@register.filter(name='extract_programme')
def extract_programme(value):
    return value.split('-')[0].lower()
