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
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": _input,
            "placeholder": "Re-enter password",
        })
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned


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


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": _input, "placeholder": "Email address"})
    )


class ResetPasswordForm(forms.Form):
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
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": _input,
            "placeholder": "New password — min 8 chars, upper, lower, number",
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": _input,
            "placeholder": "Re-enter new password",
        })
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password")
        p2 = cleaned.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned
