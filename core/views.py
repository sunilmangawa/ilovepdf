from django.shortcuts import render

# Create your views here.
def home(request):
    
    context = {}
    return render(request, 'core/home.html', context)

def about(request):
    
    context = {}
    return render(request, 'core/about.html', context)

def contactus(request):
    
    context = {}
    return render(request, 'core/contactus.html', context)

def termscondition(request):
    
    context = {}
    return render(request, 'core/terms_and_condition.html', context)

