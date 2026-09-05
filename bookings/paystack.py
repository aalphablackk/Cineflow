import requests

from django.conf import settings


# ============================================================
# PAYSTACK CONFIGURATION
# ============================================================

PAYSTACK_BASE_URL = settings.PAYSTACK_BASE_URL


# ============================================================
# EXCEPTIONS
# ============================================================

class PaystackError(Exception):
    """
    Raised when communication with Paystack fails
    or Paystack returns an unsuccessful response.
    """

    pass


# ============================================================
# HEADERS
# ============================================================

def _get_headers():
    """
    Return the headers required for authenticated
    Paystack API requests.
    """

    if not settings.PAYSTACK_SECRET_KEY:
        raise PaystackError(
            "Paystack secret key is not configured."
        )

    return {
        "Authorization": (
            f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        ),
        "Content-Type": "application/json",
    }


# ============================================================
# INITIALIZE TRANSACTION
# ============================================================

def initialize_transaction(
    *,
    email,
    amount,
    reference,
    callback_url,
    metadata=None,
):
    """
    Initialize a Paystack transaction.

    Parameters:
        email:
            Customer email address.

        amount:
            Amount in Naira as a Decimal or numeric value.

        reference:
            Unique CineFlow payment reference.

        callback_url:
            Fully-qualified URL Paystack should redirect to
            after the customer completes the transaction.

        metadata:
            Optional metadata attached to the transaction.

    Returns:
        Paystack transaction data containing:
            authorization_url
            access_code
            reference
    """

    amount_in_kobo = int(
        round(float(amount) * 100)
    )

    payload = {
        "email": email,
        "amount": str(amount_in_kobo),
        "currency": "NGN",
        "reference": reference,
        "callback_url": callback_url,
    }

    if metadata is not None:
        payload["metadata"] = metadata

    try:

        response = requests.post(
            f"{PAYSTACK_BASE_URL}/transaction/initialize",
            headers=_get_headers(),
            json=payload,
            timeout=30,
        )

    except requests.RequestException as exc:

        raise PaystackError(
            "Unable to connect to Paystack."
        ) from exc

    try:

        data = response.json()

    except ValueError as exc:

        raise PaystackError(
            "Paystack returned an invalid response."
        ) from exc

    if (
        response.status_code != 200
        or not data.get("status")
    ):

        raise PaystackError(
            data.get(
                "message",
                "Paystack transaction initialization failed.",
            )
        )

    transaction_data = data.get("data")

    if not transaction_data:
        raise PaystackError(
            "Paystack returned no transaction data."
        )

    authorization_url = transaction_data.get(
        "authorization_url"
    )

    access_code = transaction_data.get(
        "access_code"
    )

    returned_reference = transaction_data.get(
        "reference"
    )

    if not authorization_url:
        raise PaystackError(
            "Paystack did not return an authorization URL."
        )

    if not returned_reference:
        raise PaystackError(
            "Paystack did not return a transaction reference."
        )

    return {
        "authorization_url": authorization_url,
        "access_code": access_code,
        "reference": returned_reference,
        "raw": data,
    }


# ============================================================
# VERIFY TRANSACTION
# ============================================================

def verify_transaction(reference):
    """
    Verify a Paystack transaction using its reference.

    Returns the transaction data returned by Paystack.
    """

    if not reference:
        raise PaystackError(
            "A payment reference is required."
        )

    try:

        response = requests.get(
            (
                f"{PAYSTACK_BASE_URL}"
                f"/transaction/verify/{reference}"
            ),
            headers=_get_headers(),
            timeout=30,
        )

    except requests.RequestException as exc:

        raise PaystackError(
            "Unable to connect to Paystack."
        ) from exc

    try:

        data = response.json()

    except ValueError as exc:

        raise PaystackError(
            "Paystack returned an invalid response."
        ) from exc

    if (
        response.status_code != 200
        or not data.get("status")
    ):

        raise PaystackError(
            data.get(
                "message",
                "Paystack transaction verification failed.",
            )
        )

    transaction_data = data.get("data")

    if not transaction_data:
        raise PaystackError(
            "Paystack returned no verification data."
        )

    return transaction_data