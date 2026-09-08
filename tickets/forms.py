from django import forms


class TicketVerificationForm(forms.Form):

    ticket_code = forms.CharField(
        label="Ticket Code",
        max_length=40,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter or scan ticket code",
                "autocomplete": "off",
            }
        ),
    )

    def clean_ticket_code(self):
        ticket_code = self.cleaned_data["ticket_code"].strip()

        if not ticket_code:
            raise forms.ValidationError(
                "Please enter a ticket code."
            )

        return ticket_code