from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter
def translate_rating(value):
    translations = {
        'exceptional': 'Excellent',
        'recommended': 'Recommandé',
        'meh': 'Bof',
        'skip': 'À éviter',
    }
    return translations.get(value.lower(), value.capitalize())