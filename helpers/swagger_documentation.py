from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
signup_post = [
    openapi.Parameter("full_name", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING),
    openapi.Parameter("email", openapi.IN_QUERY, required=True, format=openapi.FORMAT_EMAIL, type=openapi.TYPE_STRING),
    openapi.Parameter("contact", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING),
    openapi.Parameter("password", openapi.IN_QUERY, format=openapi.FORMAT_PASSWORD, required=True, type=openapi.TYPE_STRING),
    
]

orderlist_post = [
    openapi.Parameter(
        'order_uid', openapi.IN_PATH, description="Unique ID of the order", type=openapi.TYPE_STRING, required=True
    )
]

login_post = [
    openapi.Parameter(
        "email",
        openapi.IN_FORM,
        description="Email",
        required=True,
        format=openapi.FORMAT_EMAIL,
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter(
        "password",
        openapi.IN_FORM,
        description="Password",
        format=openapi.FORMAT_PASSWORD,
        required=True,
        type=openapi.TYPE_STRING,
    ),
]

logout_get = [
    openapi.Parameter(
        "confirm",
        openapi.IN_QUERY,
        description="Set to 'true' to confirm logout",
        required=False,
        type=openapi.TYPE_STRING,
    ),
    openapi.Parameter(
        "cancel",
        openapi.IN_QUERY,
        description="Set to 'true' to cancel logout",
        required=False,
        type=openapi.TYPE_STRING,
    ),
]

send_otp_parameters = [
        openapi.Parameter("contact", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING),

]
validate_otp_parameters = [
    openapi.Parameter(
        "otp",
        openapi.IN_QUERY,
        description="OTP to validate",
        required=True,
        type=openapi.TYPE_STRING,
    ),
]

forgot_password = [
    openapi.Parameter(
        "email",
        openapi.IN_FORM,
        description="User Email",
        type=openapi.TYPE_STRING,
        required=True,
    ),
]

reset_password = [
    openapi.Parameter(
        "new_password",
        openapi.IN_FORM,
        description="Password",
        type=openapi.TYPE_STRING,
        required=True,
    ),
    openapi.Parameter(
        "confirm_password",
        openapi.IN_FORM,
        description="Confirm Password",
        type=openapi.TYPE_STRING,
        required=True,
    ),
]


update_profile = [
            openapi.Parameter(
                "full_name",
                openapi.IN_FORM,
                description="Full Name",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "email",
                openapi.IN_FORM,
                description="Email",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "contact",
                openapi.IN_FORM,
                description="Contact Number",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            
        ]

add_address_post = [
    openapi.Parameter(
        "Address1",
        openapi.IN_FORM,
        description="Primary address line 1",
        type=openapi.TYPE_STRING,
        required=True,
    ),
    openapi.Parameter(
        "Address2",
        openapi.IN_FORM,
        description="Secondary address line 2",
        type=openapi.TYPE_STRING,
        required=False,
    ),
    openapi.Parameter(
        "country",
        openapi.IN_FORM,
        description="Country of residence",
        type=openapi.TYPE_STRING,
        required=True,
    ),
    openapi.Parameter(
        "state",
        openapi.IN_FORM,
        description="State or province",
        type=openapi.TYPE_STRING,
        required=True,
    ),
    openapi.Parameter(
        "city",
        openapi.IN_FORM,
        description="City or town",
        type=openapi.TYPE_STRING,
        required=True,
    ),
    openapi.Parameter(
        "contact",
        openapi.IN_FORM,
        description="Contact number",
        type=openapi.TYPE_STRING,
        required=True,
    ),
    openapi.Parameter(
        "pincode",
        openapi.IN_FORM,
        description="Postal or ZIP code",
        type=openapi.TYPE_STRING,
        required=True,
    ),
]
