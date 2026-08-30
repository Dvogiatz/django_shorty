from django import forms

from .models import Url


class UrlForm(forms.ModelForm):
    class Meta:
        model = Url
        fields = ['original_url']
        labels = {
            'original_url': 'Enter a URL to shorten',
        }
        widgets = {
            'original_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/very/long/path',
            }),
        }
