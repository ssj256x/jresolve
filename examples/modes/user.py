import json

from jresolve import JqModel, Jq, Transform
from jresolve.core.types import ResolutionMode
from typing import Annotated, Optional


class User(JqModel):
    user_id: Annotated[
        str,
        Jq(".id"),
        Transform(str.upper)
    ]

    email: Annotated[
        str,
        Jq(".profile.contact.email")
    ]

    phone_verified: Annotated[
        bool,
        Jq(".profile.contact.phone.verified")  # ❌ invalid type
    ]

    premium_price: Annotated[
        Optional[float],
        Jq('.subscriptions[] | selects(.plan == "PREMIUM") | .billing.price')
    ]


data = {
    "id": "usr_123",
    "profile": {
        "contact": {
            "email": "valid@email.com",
            "phone": {
                "verified": "Yo"  # ❌ should be bool
            }
        }
    },
    "subscriptions": [
        {
            "plan": "PREMIUM",
            "billing": {
                "price": "not_a_number"  # ❌ should be float
            }
        }
    ]
}

result = User.from_json(data, mode=ResolutionMode.PARTIAL)

# print("Model Dump")
# print(result.value.model_dump())

if result.is_success:
    print("✅ Full success:", result)

elif result.is_partial:
    print("⚠️ Partial success:", result.value)
    print("Errors:", result.errors)

elif result.is_failure:
    print("❌ Failure:", result)
    for key, val in result.errors.items():
        print(f"Field : {key}")
        print(f"Error: {val}")
        print("---")
