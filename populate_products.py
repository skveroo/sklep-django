import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'SklepInternetowy.settings'
django.setup()

from shop.models import Category, Tag, Product, HardwareRequirement

# ========== Czyścimy stare dane testowe ==========
Product.objects.all().delete()
Category.objects.all().delete()
Tag.objects.all().delete()

print("Wyczyszczono stare dane.")

# ========== KATEGORIE (drzewo) ==========
komputery = Category.objects.create(name="Komputery", slug="komputery", icon="fa-desktop", description="Komputery stacjonarne i laptopy")
laptopy = Category.objects.create(name="Laptopy", slug="laptopy", parent=komputery, icon="fa-laptop", description="Laptopy do pracy, nauki i gier")
pc = Category.objects.create(name="Komputery stacjonarne", slug="komputery-stacjonarne", parent=komputery, icon="fa-computer", description="Zestawy PC gamingowe i biurowe")

podzespoly = Category.objects.create(name="Podzespoły", slug="podzespoly", icon="fa-microchip", description="Karty graficzne, procesory, RAM, dyski")
karty_graf = Category.objects.create(name="Karty graficzne", slug="karty-graficzne", parent=podzespoly, icon="fa-display")
procesory = Category.objects.create(name="Procesory", slug="procesory", parent=podzespoly, icon="fa-microchip")

peryferia = Category.objects.create(name="Peryferia", slug="peryferia", icon="fa-keyboard", description="Monitory, klawiatury, myszki, słuchawki")
monitory = Category.objects.create(name="Monitory", slug="monitory", parent=peryferia, icon="fa-tv")
klawiatury_myszy = Category.objects.create(name="Klawiatury i myszki", slug="klawiatury-myszki", parent=peryferia, icon="fa-keyboard")
audio = Category.objects.create(name="Audio", slug="audio", parent=peryferia, icon="fa-headphones")

akcesoria = Category.objects.create(name="Akcesoria", slug="akcesoria", icon="fa-plug", description="Zasilacze, kable, torby, podkładki")

print(f"Utworzono {Category.objects.count()} kategorii.")

# ========== TAGI ==========
tagi_dane = [
    "gaming", "biurowy", "4K", "RGB", "bezprzewodowy", "mechaniczny",
    "SSD", "DDR5", "Intel", "AMD", "NVIDIA", "USB-C", "Bluetooth",
    "programowanie", "streaming", "budżetowy", "premium", "przenośny"
]
tagi = {}
for t in tagi_dane:
    tagi[t] = Tag.objects.create(name=t)

print(f"Utworzono {Tag.objects.count()} tagów.")

# ========== PRODUKTY ==========
produkty_data = [
    {
        "name": "Laptop ASUS ROG Strix G16",
        "category": laptopy,
        "price": 6499.00,
        "stock": 12,
        "description": "Wydajny laptop gamingowy z ekranem 16 cali o rozdzielczości 2560x1600 i częstotliwości odświeżania 240Hz. Wyposażony w procesor Intel Core i9-14900HX oraz kartę graficzną NVIDIA GeForce RTX 4070. Idealny do gier AAA, pracy z grafiką i streamingu. Podświetlana klawiatura RGB, szybkie WiFi 6E oraz port Thunderbolt 4.",
        "tags": ["gaming", "premium", "Intel", "NVIDIA", "RGB"],
        "requirements": {
            "processor": "Intel Core i9-14900HX (24 rdzenie, do 5.8 GHz)",
            "ram": "32 GB DDR5 4800 MHz",
            "storage": "1 TB NVMe SSD PCIe 4.0",
            "graphics": "NVIDIA GeForce RTX 4070 8 GB GDDR6",
            "os": "Windows 11 Home",
            "additional": "Ekran 16\" WQXGA 240Hz, WiFi 6E, Bluetooth 5.3, Thunderbolt 4"
        }
    },
    {
        "name": "Laptop Lenovo ThinkPad X1 Carbon Gen 12",
        "category": laptopy,
        "price": 7299.00,
        "stock": 8,
        "description": "Ultralekki laptop biznesowy o wadze zaledwie 1.08 kg. Wyposażony w procesor Intel Core Ultra 7 155H, ekran 14\" WUXGA IPS z pokryciem 100% sRGB. Certyfikat MIL-STD-810H gwarantuje wytrzymałość. Do 15 godzin pracy na baterii. Idealne narzędzie dla programistów i profesjonalistów.",
        "tags": ["biurowy", "premium", "Intel", "przenośny", "programowanie"],
        "requirements": {
            "processor": "Intel Core Ultra 7 155H (16 rdzeni)",
            "ram": "32 GB LPDDR5x 6400 MHz",
            "storage": "512 GB NVMe SSD PCIe 4.0",
            "graphics": "Intel Arc Graphics (zintegrowana)",
            "os": "Windows 11 Pro",
            "additional": "14\" WUXGA IPS, 1.08 kg, do 15h baterii, MIL-STD-810H, czytnik linii papilarnych"
        }
    },
    {
        "name": "PC Gaming FURY Destroyer RTX 4080",
        "category": pc,
        "price": 9999.00,
        "stock": 5,
        "description": "Topowy zestaw komputerowy do gier i pracy kreatywnej. Procesor AMD Ryzen 9 7950X w połączeniu z kartą NVIDIA RTX 4080 SUPER gwarantuje płynną grę w 4K. Obudowa z hartowanym szkłem i efektownym podświetleniem ARGB. Chłodzenie wodne AIO 360mm zapewnia cichą pracę nawet pod pełnym obciążeniem.",
        "tags": ["gaming", "premium", "AMD", "NVIDIA", "4K", "RGB"],
        "requirements": {
            "processor": "AMD Ryzen 9 7950X (16 rdzeni, do 5.7 GHz)",
            "ram": "64 GB DDR5 5600 MHz (2×32 GB)",
            "storage": "2 TB NVMe SSD PCIe 5.0 + 4 TB HDD",
            "graphics": "NVIDIA GeForce RTX 4080 SUPER 16 GB GDDR6X",
            "os": "Windows 11 Pro",
            "additional": "Chłodzenie AIO 360mm, zasilacz 850W 80+ Gold, WiFi 6E, obudowa z RGB"
        }
    },
    {
        "name": "NVIDIA GeForce RTX 4070 Ti SUPER",
        "category": karty_graf,
        "price": 3899.00,
        "stock": 18,
        "description": "Karta graficzna stworzona do gier w rozdzielczości 1440p i 4K. 16 GB pamięci GDDR6X zapewnia komfort w najnowszych tytułach. Technologia DLSS 3.5 z generowaniem klatek pozwala na dwukrotne zwiększenie wydajności. Obsługa ray tracingu nowej generacji. Ciche chłodzenie z trzema wentylatorami.",
        "tags": ["gaming", "NVIDIA", "4K", "premium"],
        "requirements": {
            "processor": "Minimum: Intel Core i5-12400 / AMD Ryzen 5 5600X",
            "ram": "Minimum 16 GB DDR4",
            "storage": "Wolne miejsce na dysku: 50 MB (sterowniki)",
            "graphics": "16 GB GDDR6X, CUDA Cores: 8448, Boost Clock: 2610 MHz",
            "os": "Windows 10/11 64-bit, Linux",
            "additional": "TDP: 285W, zasilacz min. 700W, złącza: 1× HDMI 2.1, 3× DisplayPort 1.4a"
        }
    },
    {
        "name": "AMD Ryzen 7 7800X3D",
        "category": procesory,
        "price": 1549.00,
        "stock": 25,
        "description": "Najlepszy procesor gamingowy na rynku dzięki technologii 3D V-Cache. 8 rdzeni i 16 wątków z taktowaniem do 5.0 GHz. 96 MB pamięci L3 cache zapewnia bezkonkurencyjną wydajność w grach. Niski pobór mocy (TDP 120W) w porównaniu do konkurencji. Socket AM5 z obsługą DDR5 i PCIe 5.0.",
        "tags": ["gaming", "AMD", "DDR5"],
        "requirements": {
            "processor": "AMD Ryzen 7 7800X3D (8C/16T, do 5.0 GHz, 96 MB L3 Cache)",
            "ram": "Obsługa DDR5 do 5200 MHz",
            "storage": "—",
            "graphics": "Brak zintegrowanej grafiki — wymagana dedykowana karta graficzna",
            "os": "Windows 10/11, Linux",
            "additional": "Socket AM5, TDP 120W, PCIe 5.0, technologia 3D V-Cache"
        }
    },
    {
        "name": "Monitor Samsung Odyssey G9 49\"",
        "category": monitory,
        "price": 4799.00,
        "stock": 7,
        "description": "Ultraszeroki monitor gamingowy 49 cali o zakrzywieniu 1000R i rozdzielczości 5120x1440 (Dual QHD). Częstotliwość odświeżania 240Hz i czas reakcji 1ms GTG zapewniają płynny obraz. Panel VA z HDR1000 i pokryciem 95% DCI-P3 gwarantuje żywe kolory i głęboką czerń. Zastępuje dwa monitory 27\".",
        "tags": ["gaming", "4K", "premium", "streaming"],
        "requirements": {
            "processor": "—",
            "ram": "—",
            "storage": "—",
            "graphics": "Złącze HDMI 2.1 lub DisplayPort 1.4, zalecana karta z min. 8 GB VRAM",
            "os": "Kompatybilny z Windows, macOS, Linux, konsolami",
            "additional": "49\" DQHD 5120x1440, 240Hz, 1ms GTG, HDR1000, 1000R, NVIDIA G-Sync, AMD FreeSync"
        }
    },
    {
        "name": "Klawiatura SteelSeries Apex Pro TKL",
        "category": klawiatury_myszy,
        "price": 899.00,
        "stock": 30,
        "description": "Mechaniczna klawiatura gamingowa z regulowanymi przełącznikami OmniPoint 2.0. Punkt aktywacji od 0.1mm do 4.0mm — dostosujesz reakcję klawisza do własnych preferencji. Kompaktowy format TKL, solidna aluminiowa rama. Podświetlenie RGB per-key z integracją SteelSeries GG. Magnetyczna podpórka pod nadgarstki w zestawie.",
        "tags": ["gaming", "mechaniczny", "RGB", "premium"],
        "requirements": {
            "processor": "—",
            "ram": "—",
            "storage": "—",
            "graphics": "—",
            "os": "Windows, macOS (oprogramowanie SteelSeries GG: Windows 10+)",
            "additional": "Przełączniki OmniPoint 2.0, USB-C, OLED ekran, aluminiowa rama, format TKL"
        }
    },
    {
        "name": "Mysz Logitech G Pro X Superlight 2",
        "category": klawiatury_myszy,
        "price": 599.00,
        "stock": 40,
        "description": "Ultraszybka bezprzewodowa mysz gamingowa o wadze zaledwie 60g. Sensor HERO 2 z czułością do 44000 DPI zapewnia precyzyjne śledzenie. Technologia LIGHTSPEED oferuje bezprzewodowe połączenie z opóźnieniem poniżej 1ms. Przełączniki LIGHTFORCE łączą szybkość optyczną z mechanicznym kliknięciem. Do 95 godzin na jednym ładowaniu.",
        "tags": ["gaming", "bezprzewodowy", "premium", "przenośny"],
        "requirements": {
            "processor": "—",
            "ram": "—",
            "storage": "—",
            "graphics": "—",
            "os": "Windows 10+, macOS 10.14+, ChromeOS",
            "additional": "60g, sensor HERO 2 (44K DPI), LIGHTSPEED wireless, USB-C, 95h baterii"
        }
    },
    {
        "name": "Słuchawki Sony WH-1000XM5",
        "category": audio,
        "price": 1399.00,
        "stock": 20,
        "description": "Najlepsze słuchawki bezprzewodowe z aktywną redukcją szumu (ANC) na rynku. 8 mikrofonów i 2 procesory redukują hałas otoczenia praktycznie do zera. Dźwięk Hi-Res Audio z obsługą LDAC. Do 30 godzin pracy na baterii, szybkie ładowanie (3 min = 3h muzyki). Ultrakomfortowe, składane, z etui transportowym.",
        "tags": ["bezprzewodowy", "Bluetooth", "premium", "przenośny"],
        "requirements": {
            "processor": "—",
            "ram": "—",
            "storage": "—",
            "graphics": "—",
            "os": "Android, iOS, Windows, macOS (aplikacja Sony Headphones Connect)",
            "additional": "ANC, 30h baterii, Hi-Res Audio, LDAC, multipoint, NFC, USB-C, 250g"
        }
    },
    {
        "name": "Zasilacz be quiet! Dark Power 13 1000W",
        "category": akcesoria,
        "price": 1099.00,
        "stock": 15,
        "description": "Zasilacz premium klasy 80+ Titanium o mocy 1000W. Certyfikat Cybenetics Lambda A++ gwarantuje cichą pracę (poniżej 15 dBA). W pełni modularny, z cyfrowym interfejsem pozwalającym na monitorowanie poboru mocy w czasie rzeczywistym. Ochrona OCP, OVP, UVP, SCP, OPP, OTP. 10-letnia gwarancja producenta.",
        "tags": ["premium"],
        "requirements": {
            "processor": "—",
            "ram": "—",
            "storage": "—",
            "graphics": "Złącze zasilania GPU: 2× PCIe 5.0 12+4pin (600W), kompatybilny z RTX 40/50 series",
            "os": "—",
            "additional": "1000W, 80+ Titanium, modularny, <15 dBA, 10 lat gwarancji, ATX 3.0"
        }
    },
    {
        "name": "Laptop Acer Nitro V 15",
        "category": laptopy,
        "price": 3499.00,
        "stock": 22,
        "description": "Przystępny cenowo laptop gamingowy z ekranem 15.6\" Full HD 144Hz. Procesor AMD Ryzen 5 7535HS w połączeniu z kartą NVIDIA RTX 4050 świetnie radzi sobie z grami w rozdzielczości 1080p. Solidna konstrukcja, podświetlana klawiatura, DTS:X Ultra Audio. Idealny na start w gaming bez rozbijania banku.",
        "tags": ["gaming", "budżetowy", "AMD", "NVIDIA"],
        "requirements": {
            "processor": "AMD Ryzen 5 7535HS (6 rdzeni, do 4.5 GHz)",
            "ram": "16 GB DDR5 4800 MHz",
            "storage": "512 GB NVMe SSD",
            "graphics": "NVIDIA GeForce RTX 4050 6 GB GDDR6",
            "os": "Windows 11 Home",
            "additional": "15.6\" FHD 144Hz, WiFi 6, podświetlana klawiatura, 2.1 kg"
        }
    },
    {
        "name": "Monitor LG UltraGear 27GP850-B",
        "category": monitory,
        "price": 1699.00,
        "stock": 16,
        "description": "Monitor gamingowy 27 cali Nano IPS z rozdzielczością 2560x1440 (QHD) i odświeżaniem 180Hz. Czas reakcji 1ms GTG, HDR400, pokrycie 98% DCI-P3. NVIDIA G-Sync Compatible i AMD FreeSync Premium. Tryb Black Stabilizer poprawia widoczność w ciemnych scenach. Regulowane ramię (wysokość, pochylenie, pivot).",
        "tags": ["gaming", "4K", "USB-C"],
        "requirements": {
            "processor": "—",
            "ram": "—",
            "storage": "—",
            "graphics": "HDMI 2.0 lub DisplayPort 1.4",
            "os": "Windows, macOS, Linux, konsole",
            "additional": "27\" QHD Nano IPS, 180Hz, 1ms GTG, HDR400, G-Sync Compatible, pivot"
        }
    },
]

for data in produkty_data:
    product = Product.objects.create(
        name=data["name"],
        category=data["category"],
        price=data["price"],
        stock=data["stock"],
        description=data["description"],
        is_active=True,
    )

    # Dodaj tagi
    for tag_name in data.get("tags", []):
        if tag_name in tagi:
            product.tags.add(tagi[tag_name])

    # Dodaj wymagania sprzętowe
    req = data.get("requirements", {})
    if req:
        HardwareRequirement.objects.create(
            product=product,
            processor=req.get("processor", ""),
            ram=req.get("ram", ""),
            storage=req.get("storage", ""),
            graphics=req.get("graphics", ""),
            os=req.get("os", ""),
            additional=req.get("additional", ""),
        )

    print(f"  + {product.name} ({product.category.name}) - {product.price} zl")

print(f"\nGotowe! Dodano {Product.objects.count()} produktów z wymaganiami sprzętowymi.")
print(f"Kategorie: {Category.objects.count()}")
print(f"Tagi: {Tag.objects.count()}")
print(f"Wymagania sprzętowe: {HardwareRequirement.objects.count()}")
