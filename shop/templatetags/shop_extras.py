from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Get value from dict by key in template: dict|dict_get:key"""
    if isinstance(d, dict):
        return d.get(key, 0)
    return 0


@register.simple_tag(takes_context=True)
def build_category_url(context, category_slug=''):
    """Build URL preserving tags, price, sort when switching category."""
    request = context['request']
    params = []
    if category_slug:
        params.append(f'category={category_slug}')
    for tag in request.GET.getlist('tag'):
        params.append(f'tag={tag}')
    if request.GET.get('q'):
        params.append(f'q={request.GET["q"]}')
    if request.GET.get('min_price'):
        params.append(f'min_price={request.GET["min_price"]}')
    if request.GET.get('max_price'):
        params.append(f'max_price={request.GET["max_price"]}')
    if request.GET.get('sort'):
        params.append(f'sort={request.GET["sort"]}')
    base = '/products/'
    return f'{base}?{"&".join(params)}' if params else base


@register.simple_tag(takes_context=True)
def build_remove_tag_url(context, tag_slug_to_remove):
    """Build URL removing one specific tag while preserving everything else."""
    request = context['request']
    params = []
    if request.GET.get('category'):
        params.append(f'category={request.GET["category"]}')
    for tag in request.GET.getlist('tag'):
        if tag != tag_slug_to_remove:
            params.append(f'tag={tag}')
    if request.GET.get('q'):
        params.append(f'q={request.GET["q"]}')
    if request.GET.get('min_price'):
        params.append(f'min_price={request.GET["min_price"]}')
    if request.GET.get('max_price'):
        params.append(f'max_price={request.GET["max_price"]}')
    if request.GET.get('sort'):
        params.append(f'sort={request.GET["sort"]}')
    base = '/products/'
    return f'{base}?{"&".join(params)}' if params else base


@register.simple_tag(takes_context=True)
def build_remove_category_url(context):
    """Build URL removing category while preserving everything else."""
    request = context['request']
    params = []
    for tag in request.GET.getlist('tag'):
        params.append(f'tag={tag}')
    if request.GET.get('q'):
        params.append(f'q={request.GET["q"]}')
    if request.GET.get('min_price'):
        params.append(f'min_price={request.GET["min_price"]}')
    if request.GET.get('max_price'):
        params.append(f'max_price={request.GET["max_price"]}')
    if request.GET.get('sort'):
        params.append(f'sort={request.GET["sort"]}')
    base = '/products/'
    return f'{base}?{"&".join(params)}' if params else base

