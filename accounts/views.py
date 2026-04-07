from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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
            password=password
        )

        return redirect("login")

    return render(request, "accounts/register.html")