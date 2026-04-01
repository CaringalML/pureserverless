from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Item
from .forms import ItemForm


def index(request):
    items = Item.objects.all()
    return render(request, "core/index.html", {"items": items})


def item_create(request):
    form = ItemForm(request.POST or None)
    if form.is_valid():
        item = form.save()
        if request.headers.get("HX-Request"):
            response = render(request, "core/partials/item_row.html", {"item": item})
            response["HX-Trigger"] = "itemCreated"
            return response
        return redirect("index")
    if request.headers.get("HX-Request"):
        return render(request, "core/partials/create_form.html", {"form": form})
    return render(request, "core/item_form.html", {"form": form, "action": "Create"})


def item_row(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, "core/partials/item_row.html", {"item": item})


def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, "core/item_detail.html", {"item": item})


def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = ItemForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        if request.headers.get("HX-Request"):
            return render(request, "core/partials/item_row.html", {"item": item})
        return redirect("index")
    if request.headers.get("HX-Request"):
        return render(request, "core/partials/item_edit_form.html", {"form": form, "item": item})
    return render(request, "core/item_form.html", {"form": form, "action": "Update", "item": item})


def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == "POST":
        item.delete()
        if request.headers.get("HX-Request"):
            return HttpResponse("")
        return redirect("index")
    return render(request, "core/item_confirm_delete.html", {"item": item})
