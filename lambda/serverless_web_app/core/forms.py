from django import forms
from .models import Item


class ItemForm(forms.ModelForm):
    class Meta:
        model  = Item
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500",
                "placeholder": "Item name",
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500",
                "placeholder": "Description (optional)",
                "rows": 3,
            }),
        }
