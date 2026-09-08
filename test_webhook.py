import os
import json
import hmac
import hashlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")

import django
django.setup()

from django.conf import settings
from django.test import Client
from django.urls import reverse


payload = {
    "event": "refund.processing",
    "data": {
        "status": "jbef",
        "transaction_reference": "PAY-25E77FD066324166880C5D82D6391972",
        # "transaction_reference": "FAKE-TRANSACTION-9999999",
        # "refund_reference": "9999999",
        "refund_reference": "18182742",
        "amount": 1500000,
        "currency": "NGN",
        "expected_at": None,
    },
}

body = json.dumps(
    payload,
    separators=(",", ":"),
).encode("utf-8")

signature = hmac.new(
    settings.PAYSTACK_SECRET_KEY.encode(),
    body,
    hashlib.sha512,
).hexdigest()

# signature = "invalid-signature"

client = Client()

response = client.post(
    reverse("bookings:paystack_webhook"),
    data=body,
    content_type="application/json",
    HTTP_X_PAYSTACK_SIGNATURE=signature,
)

print("STATUS CODE:", response.status_code)
print("RESPONSE:", response.json())