# SklepInternetowy
# Wymagania

Aby uruchomić projekt potrzebne są:
Docker 
Docker Compose

# Uruchomienie projektu

1. Sklonuj repozytorium:
git clone https://github.com/skveroo/sklep-django.git
cd sklep-django

2. Uruchom aplikację:
docker compose up --build

3. Otwórz w przeglądarce:
http://127.0.0.1:8000/

# Pierwsze uruchomienie (baza danych)

Po uruchomieniu kontenera wykonaj migracje:
docker compose exec web python manage.py migrate

# Konto administratora
Panel admina dostępny pod:
http://127.0.0.1:8000/admin/

# Zatrzymywanie aplikacji
docker compose down

# Ponowne uruchomienie
docker compose up

# Aktualizacja zależności
Jeśli zmieniono requirements.txt:
docker compose up --build

# Jak działa projekt

Projekt wykorzystuje framework Django działający w kontenerze Docker.
Frontend jest generowany na razie przez szablony HTML (Django templates, ale CSS i JavaScript łatwo podpiąć), a backend w Pythonie.
Baza danych to SQLite zapisywana jako plik w projekcie.
