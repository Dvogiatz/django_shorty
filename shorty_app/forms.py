from django import forms

from .models import Url
from .safety import (
    is_internationalized_domain,
    is_url_flagged_unsafe,
    is_url_from_another_shortener,
)


class UrlForm(forms.ModelForm):
    class Meta:
        model = Url
        fields = ['original_url']
        labels = {
            'original_url': 'Enter a URL to shorten',
        }
        widgets = {
            'original_url': forms.URLInput(attrs={
                'placeholder': 'https://example.com/very/long/path',
            }),
        }

    def clean_original_url(self):
        url = self.cleaned_data['original_url']
        if is_url_from_another_shortener(url):
            raise forms.ValidationError(
                "Shortening a link that's already from another URL shortener isn't allowed."
            )
        if is_internationalized_domain(url):
            raise forms.ValidationError(
                "Internationalized domain names (punycode / non-ASCII) aren't allowed."
            )
        if is_url_flagged_unsafe(url):
            raise forms.ValidationError(
                "This URL has been flagged as unsafe and can't be shortened."
            )
        return url
