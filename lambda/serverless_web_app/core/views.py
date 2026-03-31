from django.shortcuts import render


def index(request):
    context = {
        "title": "Serverless Web App",
        "message": "Hello, World!",
        "framework": "Django on AWS Lambda",
    }
    return render(request, "core/index.html", context)
