import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def render_markdown(text):
    html = str(text)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    html = html.replace('\n', '<br>')
    return mark_safe(html)
