from django import forms

from .models import SupportTicket,SupportMessage


class SupportTicketForm(forms.ModelForm):

    message = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": (
                    "Describe your issue or question..."
                ),
            }
        ),
    )

    class Meta:

        model = SupportTicket

        fields = [
            "subject",
            "priority",
        ]

        widgets = {

            "subject": forms.TextInput(
                attrs={
                    "placeholder": (
                        "What can we help you with?"
                    ),
                }
            ),

            "priority": forms.Select(),
        }

        labels = {
            "subject": "Subject",
            "priority": "Priority",
        }

class SupportReplyForm(forms.ModelForm):

    class Meta:

        model = SupportMessage

        fields = [
            "message",
        ]

        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Type your message...",
                    "rows": 5,
                }
            ),
        }

        labels = {
            "message": "Reply",
        }