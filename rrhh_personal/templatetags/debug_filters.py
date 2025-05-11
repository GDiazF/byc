from django import template

register = template.Library()

@register.filter(name='type_filter')
def type_filter(value):
    return type(value).__name__ 