from django.shortcuts import render
from rest_framework import viewsets
from .models import Count
from .forms import ClientForm
from .serializers import CountSerializer

# Create your views here.

class CountView(viewsets.ModelViewSet):
    queryset = Count.objects.all()
    serializer_class = CountSerializer
    
def ClientCreateView(request):
    success = False
    form = ClientForm(request.POST or None)
    if form.is_valid():
        form.save()
        form = ClientForm()
        success = True

    context = {
        'form': form, 
        'success': success,
    }

    return render(request, "count/count_create.html", context)