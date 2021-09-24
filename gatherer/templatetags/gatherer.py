
from django import template

register = template.Library()

@register.simple_tag
def localize_tag_name(tag, lang_code):
    return tag.name(lang_code)

@register.simple_tag
def localize_tag_slug(tag, lang_code):
    return tag.slug(lang_code)

@register.simple_tag
def localize_group_name(group, lang_code):
    return group.name(lang_code)

@register.simple_tag
def define(val=None):
      return val
