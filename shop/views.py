from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Order, OrderItem

def get_cart_count(request):
    cart = request.session.get('cart', {})
    return sum(cart.values())

def home(request):
    return render(request, 'shop/home.html', {
        'title': 'Witamy w sklepie',
        'message': 'Sprawdź naszą ofertę produktów',
        'cart_count': get_cart_count(request),
    })
def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()

    category_id = request.GET.get('category')
    query = request.GET.get('q')
    sort = request.GET.get('sort')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if category_id:
        products = products.filter(category_id=category_id)

    if query:
        products = products.filter(name__icontains=query)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')

    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories,
        'cart_count': get_cart_count(request),
    })
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'cart_count': get_cart_count(request),
    })
def add_to_cart(request, id):
    cart = request.session.get('cart', {})
    product_id = str(id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    request.session['cart'] = cart
    return redirect('cart')
    
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * quantity
        total += item_total

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total,
        })

    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': get_cart_count(request),
    })
    
def remove_from_cart(request, id):
    cart = request.session.get('cart', {})
    product_id = str(id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart
    return redirect('cart')
    
def increase_quantity(request, id):
    cart = request.session.get('cart', {})
    product_id = str(id)

    if product_id in cart:
        cart[product_id] += 1

    request.session['cart'] = cart
    return redirect('cart')


def decrease_quantity(request, id):
    cart = request.session.get('cart', {})
    product_id = str(id)

    if product_id in cart:
        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

    request.session['cart'] = cart
    return redirect('cart')
    
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('product_list')

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')

        total = 0
        items = []

        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            total += product.price * quantity
            items.append((product, quantity))

        order = Order.objects.create(
            total_price=total,
            customer_name=name,
            customer_email=email,
            user=request.user if request.user.is_authenticated else None
        )

        for product, quantity in items:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

        request.session['cart'] = {}

        return render(request, 'shop/checkout_success.html', {
            'order': order,
            'cart_count': 0,
        })

    return render(request, 'shop/checkout.html', {
        'cart_count': get_cart_count(request),
    })
    
def my_orders(request):
    if not request.user.is_authenticated:
        return redirect('login')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'shop/my_orders.html', {
        'orders': orders,
        'cart_count': get_cart_count(request),
    })