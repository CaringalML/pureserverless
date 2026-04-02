from django import forms

_input = "w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500"


class SignUpForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": _input, "placeholder": "Email address"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": _input,
            "placeholder": "Min 8 chars — upper, lower, number",
        })
    )


class VerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "class": _input + " text-center text-2xl tracking-widest",
            "placeholder": "123456",
            "autocomplete": "one-time-code",
            "inputmode": "numeric",
        }),
    )


class SignInForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": _input, "placeholder": "Email address"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": _input, "placeholder": "Password"})
    )
