import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse

from .decorators import cognito_login_required
from .forms import SignUpForm, VerifyForm, SignInForm


def _cognito():
    return boto3.client("cognito-idp", region_name=settings.AWS_REGION)


def signup(request):
    form = SignUpForm(request.POST or None)
    if form.is_valid():
        try:
            _cognito().sign_up(
                ClientId=settings.COGNITO_CLIENT_ID,
                Username=form.cleaned_data["email"],
                Password=form.cleaned_data["password"],
                UserAttributes=[{"Name": "email", "Value": form.cleaned_data["email"]}],
            )
            url = reverse("verify") + f'?email={form.cleaned_data["email"]}'
            return redirect(url)
        except ClientError as e:
            form.add_error(None, e.response["Error"]["Message"])
    return render(request, "accounts/signup.html", {"form": form})


def verify(request):
    email = request.GET.get("email", "")
    form = VerifyForm(request.POST or None, initial={"email": email})
    if form.is_valid():
        try:
            _cognito().confirm_sign_up(
                ClientId=settings.COGNITO_CLIENT_ID,
                Username=form.cleaned_data["email"],
                ConfirmationCode=form.cleaned_data["code"],
            )
            return redirect("signin")
        except ClientError as e:
            form.add_error(None, e.response["Error"]["Message"])
    return render(request, "accounts/verify.html", {"form": form, "email": email})


def signin(request):
    if request.session.get("access_token"):
        return redirect("dashboard")
    form = SignInForm(request.POST or None)
    if form.is_valid():
        try:
            resp = _cognito().initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": form.cleaned_data["email"],
                    "PASSWORD": form.cleaned_data["password"],
                },
                ClientId=settings.COGNITO_CLIENT_ID,
            )
            tokens = resp["AuthenticationResult"]
            request.session["access_token"]  = tokens["AccessToken"]
            request.session["refresh_token"] = tokens["RefreshToken"]
            return redirect("dashboard")
        except ClientError as e:
            form.add_error(None, e.response["Error"]["Message"])
    return render(request, "accounts/signin.html", {"form": form})


@cognito_login_required
def dashboard(request):
    try:
        resp = _cognito().get_user(AccessToken=request.session["access_token"])
        attrs = {a["Name"]: a["Value"] for a in resp["UserAttributes"]}
        user = {
            "email":          attrs.get("email", ""),
            "email_verified": attrs.get("email_verified", "false") == "true",
            "sub":            attrs.get("sub", ""),
            "username":       resp["Username"],
        }
    except ClientError:
        # Token expired or revoked — force re-login
        request.session.flush()
        return redirect("signin")
    return render(request, "accounts/dashboard.html", {"user": user})


def signout(request):
    access_token = request.session.get("access_token")
    if access_token:
        try:
            _cognito().global_sign_out(AccessToken=access_token)
        except ClientError:
            pass
    request.session.flush()
    return redirect("signin")
