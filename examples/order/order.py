import json

from typing import Annotated
from jresolve import (
    JqModel,
    Jq,
    Transform,
    Computed,
    JqMode
)


class OrderSummary(JqModel):
    order_id: Annotated[
        str,
        Jq(".id")
    ]

    customer_email: Annotated[
        str,
        Jq(".customer.contact.email"),
        Transform(str.lower)
    ]

    item_count: Annotated[
        int,
        Jq(".items"),
        Transform(len)
    ]

    premium_total: Annotated[
        int,
        Jq(
            ".items[] | select(.category == \"premium\") | .price",
            mode=JqMode.MANY
        ),
        Transform(sum)
    ]

    order_label: Annotated[
        str,
        Computed(lambda d: f"ORDER-{d['id']}")
    ]


# Execute the resolution
with open('orders.json') as f:
    data = json.loads(f.read())
    result = OrderSummary.from_json(data)

    print(result)