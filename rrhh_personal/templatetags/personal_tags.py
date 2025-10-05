from django import template

register = template.Library()

@register.filter
def get_field_label(form, field_name):
    """
    Returns the label for a form field
    """
    try:
        return form.fields[field_name].label
    except (KeyError, AttributeError):
        return field_name.replace('_', ' ').title() 