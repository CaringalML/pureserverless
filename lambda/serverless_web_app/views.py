from django.http import HttpResponse


def index(request):
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Serverless Web App</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f172a;
            color: #f8fafc;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .card {
            text-align: center;
            padding: 3rem 4rem;
            background: #1e293b;
            border-radius: 1rem;
            border: 1px solid #334155;
            box-shadow: 0 25px 50px rgba(0,0,0,0.4);
        }
        h1 { font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; }
        p  { color: #94a3b8; font-size: 1.1rem; margin-top: 0.75rem; }
        .badge {
            display: inline-block;
            margin-top: 1.5rem;
            padding: 0.35rem 1rem;
            background: #0ea5e9;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.05em;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Hello, World!</h1>
        <p>Powered by Django on AWS Lambda</p>
        <span class="badge">Serverless Web App</span>
    </div>
</body>
</html>
"""
    return HttpResponse(html)
