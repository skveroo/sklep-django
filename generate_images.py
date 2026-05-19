"""
Skrypt generujący placeholder obrazki dla produktów.
Tworzy okładkę + 3 zdjęcia galerii dla każdego produktu.
"""
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'SklepInternetowy.settings'
django.setup()

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.base import ContentFile
from shop.models import Product, ProductImage

# Kolory dla różnych kategorii
CATEGORY_COLORS = {
    'Laptopy': [(75, 0, 130), (138, 43, 226), (72, 61, 139)],
    'Komputery stacjonarne': [(220, 20, 60), (178, 34, 34), (139, 0, 0)],
    'Karty graficzne': [(0, 128, 0), (34, 139, 34), (0, 100, 0)],
    'Procesory': [(255, 140, 0), (255, 165, 0), (204, 85, 0)],
    'Monitory': [(0, 71, 171), (30, 144, 255), (0, 0, 139)],
    'Klawiatury i myszki': [(199, 21, 133), (186, 85, 211), (148, 0, 211)],
    'Audio': [(0, 139, 139), (32, 178, 170), (0, 128, 128)],
    'Akcesoria': [(105, 105, 105), (169, 169, 169), (128, 128, 128)],
}

# Ikony/symbole dla różnych typów zdjęć galerii
GALLERY_LABELS = [
    "Widok z przodu",
    "Widok z boku",
    "Szczegóły / porty",
]


def create_placeholder(width, height, bg_color, text, sub_text="", border_color=None):
    """Tworzy placeholder z gradientem i tekstem."""
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Gradient overlay
    for y in range(height):
        alpha = int(80 * (y / height))
        draw.line([(0, y), (width, y)], fill=(
            max(0, bg_color[0] - alpha),
            max(0, bg_color[1] - alpha),
            max(0, bg_color[2] - alpha),
        ))

    # Border
    if border_color:
        for i in range(3):
            draw.rectangle([i, i, width - 1 - i, height - 1 - i], outline=border_color)

    # Tekst - nazwa produktu
    try:
        font_large = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Wyśrodkuj tekst
    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font_large)
        if bbox[2] - bbox[0] > width - 40:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    total_text_height = len(lines) * 36
    y_start = (height - total_text_height) // 2 - 15

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_large)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        # Cień
        draw.text((x + 2, y_start + i * 36 + 2), line, fill=(0, 0, 0), font=font_large)
        draw.text((x, y_start + i * 36), line, fill=(255, 255, 255), font=font_large)

    # Sub text (np. "Widok z przodu")
    if sub_text:
        bbox = draw.textbbox((0, 0), sub_text, font=font_small)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        y = y_start + len(lines) * 36 + 10
        draw.text((x, y), sub_text, fill=(200, 200, 200), font=font_small)

    # Ikona aparatu w rogu
    draw.text((width - 35, height - 30), "📷", fill=(200, 200, 200), font=font_small)

    return img


def save_image_to_field(img, filename):
    """Konwertuje PIL Image na Django ContentFile."""
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=filename)


def main():
    products = Product.objects.all()

    if not products.exists():
        print("Brak produktów w bazie! Uruchom najpierw populate_products.py")
        return

    # Wyczyść stare obrazki
    ProductImage.objects.all().delete()
    print("Wyczyszczono stare zdjęcia galerii.")

    # Utwórz folder media jeśli nie istnieje
    os.makedirs('media/products', exist_ok=True)
    os.makedirs('media/products/gallery', exist_ok=True)

    for product in products:
        cat_name = product.category.name if product.category else 'Akcesoria'
        colors = CATEGORY_COLORS.get(cat_name, [(100, 100, 100), (80, 80, 80), (60, 60, 60)])

        # 1. Okładka produktu (800x600)
        cover = create_placeholder(
            800, 600,
            bg_color=colors[0],
            text=product.name,
            sub_text=cat_name,
            border_color=(255, 255, 255)
        )
        cover_file = save_image_to_field(cover, f"{product.slug}_cover.jpg")
        product.image.save(f"{product.slug}_cover.jpg", cover_file, save=True)
        print(f"  📸 Okładka: {product.name}")

        # 2. Zdjęcia galerii (3 sztuki, różne kolory)
        for i, (label, color) in enumerate(zip(GALLERY_LABELS, colors)):
            gallery_img = create_placeholder(
                800, 600,
                bg_color=color,
                text=product.name,
                sub_text=label,
            )
            gallery_file = save_image_to_field(gallery_img, f"{product.slug}_gallery_{i+1}.jpg")

            ProductImage.objects.create(
                product=product,
                image=gallery_file,
                caption=label,
                order=i,
            )
            # Nadaj plik
            pi = ProductImage.objects.filter(product=product, order=i).last()
            pi.image.save(f"{product.slug}_gallery_{i+1}.jpg", gallery_file, save=True)

        print(f"  🖼️  Galeria (3 zdjęcia): {product.name}")

    print(f"\n✅ Gotowe! Wygenerowano obrazki dla {products.count()} produktów.")
    print(f"   Okładki: {products.count()}")
    print(f"   Zdjęcia galerii: {ProductImage.objects.count()}")


if __name__ == '__main__':
    main()
