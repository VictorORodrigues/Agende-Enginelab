from django import template

register = template.Library()

CORES = {
    'primary': '#5cb680',
    'danger': '#ad1925',
    'secondary': '#6b7280',
}


@register.inclusion_tag('emails/_botao.html')
def email_botao(url, texto, cor='primary'):
    return {'url': url, 'texto': texto, 'cor': CORES.get(cor, CORES['primary'])}


@register.inclusion_tag('emails/_botoes_duplo.html')
def email_botoes(url_esquerda, texto_esquerda, url_direita, texto_direita, cor_esquerda='primary', cor_direita='danger'):
    return {
        'url_esquerda': url_esquerda,
        'texto_esquerda': texto_esquerda,
        'cor_esquerda': CORES.get(cor_esquerda, CORES['primary']),
        'url_direita': url_direita,
        'texto_direita': texto_direita,
        'cor_direita': CORES.get(cor_direita, CORES['danger']),
    }
