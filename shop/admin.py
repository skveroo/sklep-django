from django.contrib import admin
from .models import (
    Product, Category, Tag, ProductImage,
    HardwareRequirement, Review, Favorite,
    ProductInquiry, Order, OrderItem, DiscountCode
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class HardwareRequirementInline(admin.StackedInline):
    model = HardwareRequirement
    extra = 0
    max_num = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('parent',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active', 'average_rating')
    list_filter = ('is_active', 'category', 'tags')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('tags',)
    inlines = [ProductImageInline, HardwareRequirementInline]

    def average_rating(self, obj):
        avg = obj.average_rating()
        return f'{avg} ★' if avg else '—'
    average_rating.short_description = 'Ocena'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')


@admin.register(ProductInquiry)
class ProductInquiryAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'name', 'email', 'message')
    readonly_fields = ('created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'customer_name', 'customer_email',
        'original_total', 'discount_code', 'discount_amount',
        'total_price', 'status', 'created_at'
    )
    list_filter = ('status', 'created_at', 'discount_code')
    search_fields = ('customer_name', 'customer_email')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_type', 'value', 'is_active',
        'min_order_value', 'usage_limit', 'used_count', 'valid_from', 'valid_to'
    )
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)