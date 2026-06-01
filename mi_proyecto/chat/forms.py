from django import forms


class ChatMessageForm(forms.Form):
    message = forms.CharField(
        label='Mensaje',
        max_length=4000,
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'placeholder': 'Escribe tu mensaje...',
                'class': 'textarea textarea-bordered w-full',
            }
        ),
    )