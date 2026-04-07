from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Order, OrderItem

def home(request):
    return render(request, 'shop/home.html', {
        'title': 'Witamy w sklepie',
        'message': 'Sprawdź naszą ofertę produktów'
    })
    
def product_list(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'shop/product_list.html', {'products': products})

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'shop/product_detail.html', {'product': product})
    
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
            'order': order
        })

    return render(request, 'shop/checkout.html')
    
def my_orders(request):
    if not request.user.is_authenticated:
        return redirect('login')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'shop/my_orders.html', {
        'orders': orders
    })