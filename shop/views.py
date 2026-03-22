from django.shortcuts import render

def home(request):
    context = {
        'title': 'Sklep internetowy',
        'message': 'Strona główna'
    }
    return render(request, 'shop/home.html', context)