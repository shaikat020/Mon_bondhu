from django import forms


class ChatForm(forms.Form):
    message = forms.CharField(
        label="",
        max_length=1000,
        widget=forms.TextInput(attrs={
            "id": "chatInput",
            "name": "userMessage",
            "placeholder": "আপনি কেমন আছেন? আমাকে বলুন...",
            "autocomplete": "off",
        }),
    )
