from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from decimal import Decimal
import re
from .models import (
    Product, Category, Tag, Order, OrderItem,
    Review, Favorite, ProductInquiry, DiscountCode,
    ShippingMethod, Return, ReturnItem
)
from .invoice import generate_invoice_pdf


def validate_checkout_fields(post_data):
    """Walidacja pól formularza zamówienia. Zwraca listę błędów."""
    errors = []

    name = post_data.get('name', '').strip()
    email = post_data.get('email', '').strip()
    phone = post_data.get('phone', '').strip()
    street = post_data.get('street', '').strip()
    house_number = post_data.get('house_number', '').strip()
    postal_code = post_data.get('postal_code', '').strip()
    city = post_data.get('city', '').strip()

    if not name:
        errors.append('Imię i nazwisko jest wymagane.')
    elif len(name) < 3:
        errors.append('Imię i nazwisko musi mieć co najmniej 3 znaki.')

    if not email:
        errors.append('Adres e-mail jest wymagany.')
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append('Podaj poprawny adres e-mail.')

    if phone:
        phone_digits = re.sub(r'[\s\-\+\(\)]', '', phone)
        if not phone_digits.isdigit() or len(phone_digits) < 7 or len(phone_digits) > 15:
            errors.append('Podaj poprawny numer telefonu.')

    if not street:
        errors.append('Ulica jest wymagana.')

    if not house_number:
        errors.append('Numer domu jest wymagany.')

    if not postal_code:
        errors.append('Kod pocztowy jest wymagany.')
    elif not re.match(r'^\d{2}-\d{3}$', postal_code):
        errors.append('Kod pocztowy musi być w formacie XX-XXX (np. 00-001).')

    if not city:
        errors.append('Miejscowość jest wymagana.')
    elif len(city) < 2:
        errors.append('Miejscowość musi mieć co najmniej 2 znaki.')

    return errors

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

    # Build category product counts (including children)
    category_product_counts = {}
    for cat in Category.objects.all():
        cat_ids = cat.get_all_children_ids()
        category_product_counts[cat.id] = Product.objects.filter(
            is_active=True, category_id__in=cat_ids
        ).count()

    # Category filter (including children)
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()
        if selected_category:
            category_ids = selected_category.get_all_children_ids()
            products = products.filter(category_id__in=category_ids)

    # Tag filter (multiple tags)
    selected_tag_slugs = request.GET.getlist('tag')
    selected_tags = []
    if selected_tag_slugs:
        selected_tags = list(Tag.objects.filter(slug__in=selected_tag_slugs))
        for tag in selected_tags:
            products = products.filter(tags=tag)

    # Search (name + tags only — NOT description to avoid false matches)
    query = request.GET.get('q')
    if query:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=query) |
            Q(tags__name__icontains=query) |
            Q(category__name__icontains=query)
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

    products = products.distinct()

    # Build available tags from current product queryset (context-aware)
    available_tags = Tag.objects.filter(
        products__in=products
    ).distinct().order_by('name')

    # Check favorites for logged-in user
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(
            Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
        )

    # Build selected tag IDs for template
    selected_tag_ids = [t.id for t in selected_tags]

    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories,
        'tags': available_tags,
        'selected_category': selected_category,
        'selected_tags': selected_tags,
        'selected_tag_ids': selected_tag_ids,
        'category_product_counts': category_product_counts,
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

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': get_cart_count(request),
        })

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

def get_cart_data(request):
    cart = request.session.get('cart', {})

    cart_items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        item_total = product.price * quantity
        total += item_total
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'item_total': item_total,
        })

    return cart, cart_items, total


def get_applied_discount(request, total):
    discount_code_id = request.session.get('discount_code_id')

    if not discount_code_id:
        return None, Decimal('0.00'), total

    try:
        discount_code = DiscountCode.objects.get(id=discount_code_id)
    except DiscountCode.DoesNotExist:
        request.session.pop('discount_code_id', None)
        request.session.pop('discount_code_text', None)
        return None, Decimal('0.00'), total

    is_valid, message = discount_code.is_valid_for_order(total)

    if not is_valid:
        request.session.pop('discount_code_id', None)
        request.session.pop('discount_code_text', None)
        messages.error(request, message)
        return None, Decimal('0.00'), total

    discount_amount = discount_code.calculate_discount(total)
    final_total = total - discount_amount

    return discount_code, discount_amount, final_total

def checkout(request):
    cart, cart_items, total = get_cart_data(request)

    if not cart:
        request.session.pop('discount_code_id', None)
        request.session.pop('discount_code_text', None)
        return redirect('product_list')

    discount_code, discount_amount, final_total = get_applied_discount(request, total)

    # Shipping methods
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    selected_shipping_id = request.session.get('selected_shipping_id')
    selected_shipping = None
    shipping_cost = Decimal('0.00')

    if selected_shipping_id:
        try:
            selected_shipping = ShippingMethod.objects.get(id=selected_shipping_id, is_active=True)
            shipping_cost = selected_shipping.price
        except ShippingMethod.DoesNotExist:
            request.session.pop('selected_shipping_id', None)

    grand_total = final_total + shipping_cost

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'apply_discount':
            code_text = request.POST.get('discount_code', '').strip().upper()

            if not code_text:
                request.session.pop('discount_code_id', None)
                request.session.pop('discount_code_text', None)
                messages.info(request, 'Usunięto kod rabatowy.')
                return redirect('checkout')

            try:
                code = DiscountCode.objects.get(code__iexact=code_text)
            except DiscountCode.DoesNotExist:
                messages.error(request, 'Nieprawidłowy kod rabatowy.')
                return redirect('checkout')

            is_valid, message = code.is_valid_for_order(total)

            if not is_valid:
                messages.error(request, message)
                return redirect('checkout')

            request.session['discount_code_id'] = code.id
            request.session['discount_code_text'] = code.code
            messages.success(request, f'Kod {code.code} został zastosowany.')
            return redirect('checkout')

        if action == 'select_shipping':
            shipping_id = request.POST.get('shipping_method')
            if shipping_id:
                try:
                    sm = ShippingMethod.objects.get(id=shipping_id, is_active=True)
                    request.session['selected_shipping_id'] = sm.id
                except ShippingMethod.DoesNotExist:
                    pass
            else:
                request.session.pop('selected_shipping_id', None)
            return redirect('checkout')

        if action == 'place_order':
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()

            # Walidacja pól formularza
            validation_errors = validate_checkout_fields(request.POST)
            if validation_errors:
                for error in validation_errors:
                    messages.error(request, error)

                # Get user profile for address auto-fill
                user_profile = None
                if request.user.is_authenticated:
                    from accounts.models import UserProfile
                    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

                return render(request, 'shop/checkout.html', {
                    'cart_items': cart_items,
                    'total': total,
                    'discount_code': discount_code,
                    'discount_amount': discount_amount,
                    'final_total': final_total,
                    'shipping_methods': shipping_methods,
                    'selected_shipping': selected_shipping,
                    'shipping_cost': shipping_cost,
                    'grand_total': grand_total,
                    'user_profile': user_profile,
                    'cart_count': get_cart_count(request),
                    'form_data': request.POST,
                })

            discount_code, discount_amount, final_total = get_applied_discount(request, total)

            # Resolve shipping
            shipping_method_obj = None
            shipping_cost_final = Decimal('0.00')
            shipping_method_name = ''
            shipping_id = request.session.get('selected_shipping_id')
            if shipping_id:
                try:
                    shipping_method_obj = ShippingMethod.objects.get(id=shipping_id, is_active=True)
                    shipping_cost_final = shipping_method_obj.price
                    shipping_method_name = shipping_method_obj.name
                except ShippingMethod.DoesNotExist:
                    pass

            grand_total_final = final_total + shipping_cost_final

            order = Order.objects.create(
                original_total=total,
                discount_code=discount_code,
                discount_amount=discount_amount,
                total_price=grand_total_final,
                customer_name=name,
                customer_email=email,
                customer_phone=request.POST.get('phone', '').strip(),
                shipping_street=request.POST.get('street', '').strip(),
                shipping_house=request.POST.get('house_number', '').strip(),
                shipping_apartment=request.POST.get('apartment_number', '').strip(),
                shipping_postal_code=request.POST.get('postal_code', '').strip(),
                shipping_city=request.POST.get('city', '').strip(),
                payment_method=request.POST.get('payment_method', 'transfer'),
                shipping_method=shipping_method_obj,
                shipping_cost=shipping_cost_final,
                shipping_method_name=shipping_method_name,
                user=request.user if request.user.is_authenticated else None
            )

            for item in cart_items:
                product = item['product']
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_image=product.image.url if product.image else '',
                    quantity=item['quantity'],
                    price=product.price
                )
                # Odejmij stan magazynowy
                product.stock = max(0, product.stock - item['quantity'])
                product.save(update_fields=['stock'])

            if discount_code:
                discount_code.used_count += 1
                discount_code.save(update_fields=['used_count'])

            request.session['cart'] = {}
            request.session.pop('discount_code_id', None)
            request.session.pop('discount_code_text', None)
            request.session.pop('selected_shipping_id', None)

            return render(request, 'shop/checkout_success.html', {
                'order': order,
                'cart_count': 0,
            })

    # Get user profile for address auto-fill
    user_profile = None
    if request.user.is_authenticated:
        from accounts.models import UserProfile
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'discount_code': discount_code,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'shipping_methods': shipping_methods,
        'selected_shipping': selected_shipping,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
        'user_profile': user_profile,
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
    
@staff_member_required
def admin_stats(request):
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='completed').count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()

    total_revenue = Order.objects.aggregate(
        total=Sum('total_price')
    )['total'] or Decimal('0.00')

    total_original_revenue = Order.objects.aggregate(
        total=Sum('original_total')
    )['total'] or Decimal('0.00')

    total_discount = Order.objects.aggregate(
        total=Sum('discount_amount')
    )['total'] or Decimal('0.00')

    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(stock__lte=5).order_by('stock')[:8]

    total_users = User.objects.count()
    total_reviews = Review.objects.count()

    latest_orders = Order.objects.select_related(
        'user', 'discount_code'
    ).order_by('-created_at')[:8]

    best_selling_products = OrderItem.objects.values(
        'product__id',
        'product__name'
    ).annotate(
        sold_quantity=Sum('quantity'),
        revenue=Sum(
            ExpressionWrapper(
                F('quantity') * F('price'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
    ).order_by('-sold_quantity')[:8]

    status_stats = [
        {
            'label': 'Oczekujące',
            'count': pending_orders,
            'class': 'pending',
        },
        {
            'label': 'W realizacji',
            'count': processing_orders,
            'class': 'processing',
        },
        {
            'label': 'Zrealizowane',
            'count': completed_orders,
            'class': 'completed',
        },
    ]

    discount_stats = DiscountCode.objects.annotate(
        order_count=Count('orders')
    ).order_by('-used_count')[:8]

    return render(request, 'shop/admin_stats.html', {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'total_revenue': total_revenue,
        'total_original_revenue': total_original_revenue,
        'total_discount': total_discount,
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'total_users': total_users,
        'total_reviews': total_reviews,
        'latest_orders': latest_orders,
        'best_selling_products': best_selling_products,
        'status_stats': status_stats,
        'discount_stats': discount_stats,
        'cart_count': get_cart_count(request),
    })
    
def get_compare_count(request):
    compare = request.session.get('compare', [])
    return len(compare)


def add_to_compare(request, id):
    product = get_object_or_404(Product, id=id, is_active=True)

    compare = request.session.get('compare', [])

    if id not in compare:
        if len(compare) >= 4:
            messages.error(request, 'Możesz porównać maksymalnie 4 produkty.')
        else:
            compare.append(id)
            request.session['compare'] = compare
            request.session.modified = True
            messages.success(request, f'Dodano produkt "{product.name}" do porównania.')
    else:
        messages.info(request, 'Ten produkt jest już w porównaniu.')

    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


def remove_from_compare(request, id):
    compare = request.session.get('compare', [])

    if id in compare:
        compare.remove(id)
        request.session['compare'] = compare
        request.session.modified = True
        messages.success(request, 'Usunięto produkt z porównania.')

    return redirect('compare_products')


def clear_compare(request):
    request.session['compare'] = []
    request.session.modified = True
    messages.success(request, 'Wyczyszczono porównywarkę.')

    return redirect('compare_products')


def compare_products(request):
    compare_ids = request.session.get('compare', [])

    products = Product.objects.filter(
        id__in=compare_ids,
        is_active=True
    ).select_related('category', 'requirements').prefetch_related('tags', 'reviews')

    products = sorted(products, key=lambda product: compare_ids.index(product.id))

    return render(request, 'shop/compare.html', {
        'products': products,
        'cart_count': get_cart_count(request),
        'compare_count': len(compare_ids),
    })


# ========== Returns ==========

@login_required(login_url='/accounts/login/')
def my_returns(request):
    returns = Return.objects.filter(user=request.user).select_related('order').prefetch_related('items__order_item')
    return render(request, 'shop/returns.html', {
        'returns': returns,
        'cart_count': get_cart_count(request),
    })


@login_required(login_url='/accounts/login/')
def create_return(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Only completed orders can be returned
    if order.status != 'completed':
        messages.error(request, 'Zwroty można składać tylko dla zrealizowanych zamówień.')
        return redirect('my_orders')

    # Check if return already exists for this order
    existing_return = Return.objects.filter(order=order, user=request.user).first()
    if existing_return:
        messages.info(request, f'Zwrot do zamówienia #{order.id} został już zgłoszony.')
        return redirect('my_returns')

    order_items = order.items.all()

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(request, 'Podaj powód zwrotu.')
            return render(request, 'shop/create_return.html', {
                'order': order,
                'order_items': order_items,
                'cart_count': get_cart_count(request),
            })

        # Collect selected items
        selected_items = []
        for item in order_items:
            qty_key = f'qty_{item.id}'
            checked_key = f'item_{item.id}'
            if request.POST.get(checked_key):
                qty = int(request.POST.get(qty_key, 1))
                qty = max(1, min(qty, item.quantity))
                selected_items.append((item, qty))

        if not selected_items:
            messages.error(request, 'Wybierz przynajmniej jeden produkt do zwrotu.')
            return render(request, 'shop/create_return.html', {
                'order': order,
                'order_items': order_items,
                'cart_count': get_cart_count(request),
            })

        # Create return
        return_request = Return.objects.create(
            order=order,
            user=request.user,
            reason=reason
        )

        for item, qty in selected_items:
            ReturnItem.objects.create(
                return_request=return_request,
                order_item=item,
                quantity=qty
            )

        messages.success(request, f'Zwrot do zamówienia #{order.id} został zgłoszony.')
        return redirect('my_returns')

    return render(request, 'shop/create_return.html', {
        'order': order,
        'order_items': order_items,
        'cart_count': get_cart_count(request),
    })


# ========== Invoice PDF ==========

@login_required(login_url='/accounts/login/')
def download_invoice(request, order_id):
    """Download PDF invoice for order. Owner or staff only."""
    order = get_object_or_404(
        Order.objects.select_related('discount_code', 'shipping_method')
        .prefetch_related('items__product'),
        id=order_id
    )

    # Security: only order owner or staff
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, 'Nie masz dostępu do tej faktury.')
        return redirect('my_orders')

    return generate_invoice_pdf(order)
