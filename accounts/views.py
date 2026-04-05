from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


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
        username = request.POST["username"]
        password = request.POST["password"]
        if password != request.POST["password2"]:
            return render(request, "accounts/register.html", {"error": "Hasła się różnią."})

        if User.objects.filter(username=username).exists():
            return render(request, "accounts/register.html", {"error": "Użytkownik o danej nazwie już istnieje."})

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect("/")

    return render(request, "accounts/register.html")