from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),

    # Favorites
    path('favorite/<int:id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.my_favorites, name='my_favorites'),

    # Reviews & Inquiries
    path('product/<int:id>/review/', views.add_review, name='add_review'),
    path('product/<int:id>/inquiry/', views.product_inquiry, name='product_inquiry'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/increase/<int:id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:id>/', views.decrease_quantity, name='decrease_quantity'),

    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('admin-stats/', views.admin_stats, name='admin_stats'),
    path('compare/', views.compare_products, name='compare_products'),
    path('compare/add/<int:id>/', views.add_to_compare, name='add_to_compare'),
    path('compare/remove/<int:id>/', views.remove_from_compare, name='remove_from_compare'),
    path('compare/clear/', views.clear_compare, name='clear_compare'),

    # Returns
    path('returns/', views.my_returns, name='my_returns'),
    path('order/<int:order_id>/return/', views.create_return, name='create_return'),
]