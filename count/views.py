from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from .models import Count
from .forms import ClientForm
from .serializers import CountSerializer
from .people_count_manager import newTrack

# Create your views here.

class CountView(viewsets.ModelViewSet):
    queryset = Count.objects.all()
    serializer_class = CountSerializer
    
def ClientCreateView(request):
    success = False
    form = ClientForm(request.POST or None)
    if form.is_valid():
        form.save()
        newTrack(form.cleaned_data['name'])
        form = ClientForm()
        success = True

    context = {
        'form': form, 
        'success': success,
    }

    return render(request, "count/count_create.html", context)

def DetailedView(request, name):
    
    obj = get_object_or_404(Count, name = name)
    context = {
        "object": obj
    }
    if request.method == 'POST':
        obj.tracking = False
        obj.save()
        obj.refresh_from_db()

    return render(request, "count/detailed_view.html", context)
