from django.shortcuts import render, get_object_or_404, redirect
from .models import Item
from .forms import ItemForm


def index(request):
    items = Item.objects.all()
    return render(request, "core/index.html", {"items": items})


def item_create(request):
    form = ItemForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("index")
    return render(request, "core/item_form.html", {"form": form, "action": "Create"})


def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, "core/item_detail.html", {"item": item})


def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = ItemForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        return redirect("index")
    return render(request, "core/item_form.html", {"form": form, "action": "Update", "item": item})


def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == "POST":
        item.delete()
        return redirect("index")
    return render(request, "core/item_confirm_delete.html", {"item": item})
