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
            # match the other text inputs in the templates for consistent UX
            "style": "width: 100%; padding: 1rem; border: 2px solid #000000; border-radius: 10px; font-size: 1rem; margin: 1rem",
        }),
    )
