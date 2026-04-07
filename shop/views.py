from django.shortcuts import render

def home(request):
    context = {
        'title': 'Sklep internetowy',
        'message': 'Strona główna',
        'user': request.user
    }
    return render(request, 'shop/home.html', context)