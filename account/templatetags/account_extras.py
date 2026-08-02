from django import template

register = template.Library()

@register.filter
def get_pode_itens_field(form, setor_id):
    """Retorna o campo pode_itens_ID do formulário"""
    try:
        field_name = f'pode_itens_{setor_id}'
        return form[field_name]
    except Exception:
        return ""

@register.filter
def get_pode_emprestimos_field(form, setor_id):
    """Retorna o campo pode_emprestimos_ID do formulário"""
    try:
        field_name = f'pode_emprestimos_{setor_id}'
        return form[field_name]
    except Exception:
        return ""

@register.filter
def get_obj_attr(obj, attr):
    try:
        if hasattr(obj, 'fields'):
            if attr in obj.fields:
                return obj[attr]
            return None
        return getattr(obj, attr)
    except (AttributeError, KeyError):
        return None
