from django.http import HttpResponse

def index(request):
    return HttpResponse("To jest sekcja zamówień")