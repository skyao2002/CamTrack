from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.

def home_view(request, *args, **kwargs):     # *args means a variable number of arguments can be passed, args will be a dynamic array
    # return HttpResponse("<h1>Hello World</h1>")  #string of HTML code
    return render(request, "home.html", {})

def contact_view(request, *args, **kwargs):     
    # return HttpResponse("<h1>Contact Page</h1>")  #string of HTML code
    return render(request, "contact.html", {})

def about_view(request, *args, **kwargs):   
    my_context = {                          # standard python dictionary with key (string): value
        "my_text": "henlo this is my text", 
        "my_number": 123, 
        "print_list": True,
        "my_list": [1,12,123,1234,512, "ABC"],
    } 
    return render(request, "about.html", my_context)