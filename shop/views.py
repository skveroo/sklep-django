from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    Product, Category, Tag, Order, OrderItem,
    Review, Favorite, ProductInquiry
)


def get_cart_count(request):
    cart = request.session.get('cart', {})
    return sum(cart.values())


def get_category_tree():
    """Build category tree for sidebar."""
    return Category.objects.filter(parent__isnull=True).prefetch_related('children')


def home(request):
    featured = Product.objects.filter(is_active=True)[:6]
    return render(request, 'shop/home.html', {
        'title': 'Witamy w sklepie',
        'message': 'Sprawdź naszą ofertę produktów',
        'cart_count': get_cart_count(request),
        'featured_products': featured,
    })


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    categories = get_category_tree()
    tags = Tag.objects.all()

    # Category filter (including children)
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()
        if selected_category:
            category_ids = selected_category.get_all_children_ids()
            products = products.filter(category_id__in=category_ids)

    # Tag filter
    tag_slug = request.GET.get('tag')
    selected_tag = None
    if tag_slug:
        selected_tag = Tag.objects.filter(slug=tag_slug).first()
        if selected_tag:
            products = products.filter(tags=selected_tag)

    # Search (name + description + tags)
    query = request.GET.get('q')
    if query:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    # Price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'rating':
        from django.db.models import Avg
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    # Check favorites for logged-in user
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(
            Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        )

    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories,
        'tags': tags,
        'selected_category': selected_category,
        'selected_tag': selected_tag,
        'favorite_ids': favorite_ids,
        'cart_count': get_cart_count(request),
    })


def category_products(request, slug):
    """Show products for a specific category."""
    category = get_object_or_404(Category, slug=slug)
    category_ids = category.get_all_children_ids()
    products = Product.objects.filter(is_active=True, category_id__in=category_ids)

    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': get_category_tree(),
        'tags': Tag.objects.all(),
        'selected_category': category,
        'favorite_ids': list(
            Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        ) if request.user.is_authenticated else [],
        'cart_count': get_cart_count(request),
    })


def product_detail(request, id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'requirements')
        .prefetch_related('images', 'tags', 'reviews__user'),
        id=id
    )

    # Check if user has purchased this product
    has_purchased = False
    has_reviewed = False
    is_favorite = False

    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status='completed',
            product=product
        ).exists()
        has_reviewed = Review.objects.filter(
            user=request.user, product=product
        ).exists()
        is_favorite = Favorite.objects.filter(
            user=request.user, product=product
        ).exists()

    reviews = product.reviews.all()
    avg_rating = product.average_rating()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'has_purchased': has_purchased,
        'has_reviewed': has_reviewed,
        'is_favorite': is_favorite,
        'cart_count': get_cart_count(request),
    })


@login_required(login_url='/accounts/login/')
def toggle_favorite(request, id):
    product = get_object_or_404(Product, id=id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user, product=product
    )
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': is_favorite})

    return redirect('product_detail', id=id)


@login_required(login_url='/accounts/login/')
def my_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product__category')
    return render(request, 'shop/favorites.html', {
        'favorites': favorites,
        'cart_count': get_cart_count(request),
    })


@login_required(login_url='/accounts/login/')
def add_review(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method != 'POST':
        return redirect('product_detail', id=id)

    # Check if user purchased this product
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__status='completed',
        product=product
    ).exists()

    if not has_purchased:
        messages.error(request, 'Możesz wystawiać recenzje tylko zakupionym produktom.')
        return redirect('product_detail', id=id)

    # Check if already reviewed
    if Review.objects.filter(user=request.user, product=product).exists():
        messages.error(request, 'Już wystawiłeś recenzję tego produktu.')
        return redirect('product_detail', id=id)

    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()

    if not rating or not comment:
        messages.error(request, 'Wypełnij ocenę i komentarz.')
        return redirect('product_detail', id=id)

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, 'Nieprawidłowa ocena.')
        return redirect('product_detail', id=id)

    Review.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        comment=comment
    )
    messages.success(request, 'Dziękujemy za recenzję!')
    return redirect('product_detail', id=id)


def product_inquiry(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method != 'POST':
        return redirect('product_detail', id=id)

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    message_text = request.POST.get('message', '').strip()

    if not name or not email or not message_text:
        messages.error(request, 'Wypełnij wszystkie pola zapytania.')
        return redirect('product_detail', id=id)

    ProductInquiry.objects.create(
        product=product,
        user=request.user if request.user.is_authenticated else None,
        name=name,
        email=email,
        message=message_text
    )
    messages.success(request, 'Twoje zapytanie zostało wysłane!')
    return redirect('product_detail', id=id)


# ========== Cart & Checkout (existing) ==========

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

    # Build cart items for display
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

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')

        order = Order.objects.create(
            total_price=total,
            customer_name=name,
            customer_email=email,
            user=request.user if request.user.is_authenticated else None
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )

        request.session['cart'] = {}

        return render(request, 'shop/checkout_success.html', {
            'order': order,
            'cart_count': 0,
        })

    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'total': total,
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