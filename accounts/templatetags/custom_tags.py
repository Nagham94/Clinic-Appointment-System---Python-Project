from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='is_equal')
def is_equal(value, arg):
    """
    Check if two values are equal (converted to strings for comparison).
    This avoids the '==' operator in templates which can be broken by auto-formatters.
    """
    return str(value) == str(arg)

@register.simple_tag
def selected_if_equal(val1, val2):
    """
    Returns 'selected' if the two values are equal (converted to strings).
    This consolidates logic into a single tag to avoid formatter-induced template errors.
    """
    if str(val1) == str(val2):
        return 'selected'
    return ''

@register.simple_tag
def first_name_display(user):
    """Returns the user's first name or a default dash."""
    return user.first_name if user.first_name else "—"

@register.simple_tag
def last_name_display(user):
    """Returns the user's last name or a default dash."""
    return user.last_name if user.last_name else "—"

@register.simple_tag
def date_joined_display(user):
    """Returns the formatted date joined."""
    return user.date_joined.strftime("%b %d, %Y")
@register.filter
def format_date(value):
    """Formats a datetime object as a string."""
    if not value:
        return "—"
    return value.strftime("%b %d, %Y")

@register.simple_tag
def render_errors(errors):
    """Renders form field errors as an unordered list."""
    if not errors:
        return ""
    html = '<ul class="error-list">'
    for error in errors:
        html += f'<li>{error}</li>'
    html += '</ul>'
    return mark_safe(html)

@register.simple_tag
def stat_display(value):
    """Returns the value or 0 if it's None/empty, for dashboard stats."""
    return value if value is not None and value != "" else 0
