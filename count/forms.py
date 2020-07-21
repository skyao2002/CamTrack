from django import forms

from .models import Count

class ClientForm(forms.ModelForm):
    class Meta:
        model = Count
        fields = [
            'name',
            'ip_path',
            'count',
            'enterDirection',
        ]
