from django.forms import ModelForm

from catalog.models import Review

class ReviewForm(ModelForm):

    class Meta:
        model = Review
        fields = 'text',
