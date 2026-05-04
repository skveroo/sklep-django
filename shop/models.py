from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from decimal import Decimal
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='children'
    )
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Klasa ikony Font Awesome, np. fa-laptop')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{original}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def get_all_children(self):
        """Recursively get all child categories."""
        children = list(self.children.all())
        for child in list(children):
            children.extend(child.get_all_children())
        return children

    def get_all_children_ids(self):
        """Get IDs of this category and all descendants."""
        ids = [self.id]
        for child in self.children.all():
            ids.extend(child.get_all_children_ids())
        return ids


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='Okładka')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{original}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0

    def review_count(self):
        return self.reviews.count()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - zdjęcie {self.order}"


class HardwareRequirement(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='requirements')
    processor = models.CharField(max_length=200, blank=True, verbose_name='Procesor')
    ram = models.CharField(max_length=100, blank=True, verbose_name='RAM')
    storage = models.CharField(max_length=100, blank=True, verbose_name='Dysk')
    graphics = models.CharField(max_length=200, blank=True, verbose_name='Karta graficzna')
    os = models.CharField(max_length=200, blank=True, verbose_name='System operacyjny')
    additional = models.TextField(blank=True, verbose_name='Dodatkowe informacje')

    def __str__(self):
        return f"Wymagania: {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, f'{i} ★') for i in range(1, 6)])
    comment = models.TextField(verbose_name='Komentarz')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # Jeden użytkownik = jedna recenzja na produkt

    def __str__(self):
        return f"{self.user.username} → {self.product.name}: {self.rating}★"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} ♥ {self.product.name}"


class ProductInquiry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inquiries')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='Imię')
    email = models.EmailField()
    message = models.TextField(verbose_name='Wiadomość')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Product inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Zapytanie: {self.product.name} od {self.name}"

class DiscountCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Procentowy'),
        ('amount', 'Kwotowy'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='Kod')
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percent',
        verbose_name='Typ rabatu'
    )
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Wartość rabatu')
    is_active = models.BooleanField(default=True, verbose_name='Aktywny')
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name='Ważny od')
    valid_to = models.DateTimeField(null=True, blank=True, verbose_name='Ważny do')
    min_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Minimalna wartość zamówienia'
    )
    usage_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name='Limit użyć')
    used_count = models.PositiveIntegerField(default=0, verbose_name='Liczba użyć')

    class Meta:
        verbose_name = 'Kod rabatowy'
        verbose_name_plural = 'Kody rabatowe'

    def __str__(self):
        return self.code

    def is_valid_for_order(self, total):
        now = timezone.now()

        if not self.is_active:
            return False, 'Ten kod rabatowy jest nieaktywny.'

        if self.valid_from and now < self.valid_from:
            return False, 'Ten kod rabatowy nie jest jeszcze aktywny.'

        if self.valid_to and now > self.valid_to:
            return False, 'Ten kod rabatowy wygasł.'

        if total < self.min_order_value:
            return False, f'Ten kod działa od kwoty {self.min_order_value} zł.'

        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, 'Ten kod rabatowy został już wykorzystany maksymalną liczbę razy.'

        return True, ''

    def calculate_discount(self, total):
        if self.discount_type == 'percent':
            discount = total * (self.value / Decimal('100'))
        else:
            discount = self.value

        if discount > total:
            discount = total

        return discount.quantize(Decimal('0.01'))

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Oczekujące'),
        ('processing', 'W realizacji'),
        ('completed', 'Zrealizowane'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    original_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_code = models.ForeignKey(
        DiscountCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Zamówienie #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
