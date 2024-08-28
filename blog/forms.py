from django import forms
from .models import Blogs
from ckeditor.widgets import CKEditorWidget

class BlogForm(forms.ModelForm):
    title = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title'}))
    author = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author'}))
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    content = forms.CharField(widget=CKEditorWidget(attrs={'class': 'form-control', 'placeholder': 'Enter content'}))
    image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    # is_highlight = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Blogs
        fields = ['title', 'author', 'date', 'content', 'image']
    