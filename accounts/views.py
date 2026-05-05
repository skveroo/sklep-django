from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from shop.models import Order
from .models import UserProfile
from django.utils import timezone

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "accounts/login.html", {"error": "Błędne dane"})

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("/")



def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        errors = []

        if not username:
            errors.append("Login nie może być pusty.")
        elif len(username) < 3:
            errors.append("Login musi mieć co najmniej 3 znaki.")
        if User.objects.filter(username=username).exists():
            errors.append("Użytkownik o tej nazwie już istnieje.")

        if not email:
            errors.append("Email jest wymagany.")
        if User.objects.filter(email=email).exists():
            errors.append("Email jest już zajęty.")

        if password != password2:
            errors.append("Hasła się różnią.")

        try:
            validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)

        if errors:
            return render(request, "accounts/register.html", {
                "errors": errors,
                "username": username
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        domain = request.get_host()
        print(uid, token)
        link = f"http://{domain}/accounts/activate/{uid}/{token}/"

        send_mail(
            subject="Weryfikacja nowego użytkownika",
            message=(f"Cześć {username}!\n"
                f"Aby aktywować swoje konto kliknij w link:\n"
                f"{link}"),
            from_email="noreply@sklepdjango.pl",
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect("login")

    return render(request, "accounts/register.html")


@login_required
def panel_view(request):

    user = request.user

    # Ensure profile exists (for users created before UserProfile was added)
    profile, _ = UserProfile.objects.get_or_create(user=user)

    orders = Order.objects.filter(user=user).order_by('-created_at')

    stats = {
        "orders_count": orders.count(),
        "total_spent": orders.aggregate(Sum("total_price"))["total_price__sum"] or 0,
        "avg_order_value": orders.aggregate(Sum("total_price"))[
                               "total_price__sum"] / orders.count() if orders.exists() else 0,
    }

    last_order = (
        Order.objects
        .filter(user=user)
        .order_by('-created_at')
        .first()
    )

    days_since_last_order = None

    if last_order:
        delta = timezone.now() - last_order.created_at
        days_since_last_order = delta.days

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_profile":

            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()

            errors = []

            if not username:
                errors.append("Login nie może być pusty.")

            if len(username) < 3:
                errors.append("Login musi mieć co najmniej 3 znaki.")

            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                errors.append("Taki login już istnieje.")

            if errors:
                return render(request, "accounts/panel.html", {
                    "errors": errors,
                    "orders": orders
                })

            user.username = username
            user.email = email
            user.save()

            # Save address and phone to profile
            profile.address = request.POST.get("address", "").strip()
            profile.phone = request.POST.get("phone", "").strip()
            profile.save()

            return redirect("panel")
        elif action == "change_password":
            old_password = request.POST.get("old_password", "")
            new_password = request.POST.get("new_password", "")
            new_password2 = request.POST.get("new_password2", "")

            errors = []

            if not user.check_password(old_password):
                errors.append("Stare hasło jest nieprawidłowe.")

            if new_password != new_password2:
                errors.append("Hasła się różnią.")

            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError

            try:
                validate_password(new_password, user)
            except ValidationError as e:
                errors.extend(e.messages)

            if errors:
                return render(request, "accounts/panel.html", {
                    "errors": errors,
                    "orders": orders,
                    "stats": stats
                })

            user.set_password(new_password)
            user.save()

            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)

            return redirect("panel")

    return render(request, "accounts/panel.html", {
        "orders": orders,
        "stats": stats,
        "profile": profile,
        "days_since_last_order": days_since_last_order
    })


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse("Konto aktywowane pomyślnie! Możesz się teraz zalogować.")
    else:
        return HttpResponse("Link aktywacyjny jest nieprawidłowy lub wygasł.")