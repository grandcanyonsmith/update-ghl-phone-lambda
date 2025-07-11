#!/usr/bin/env python3
"""
Test script for the update_ghl_phone_numbers Lambda function.
This script simulates a Lambda invocation with a Stripe webhook event.
"""

import json
from update_ghl_phone_numbers import lambda_handler

# Test event from Stripe webhook
test_event = {
    'version': '2.0',
    'routeKey': '$default',
    'rawPath': '/',
    'rawQueryString': '',
    'headers': {
        'content-length': '3789',
        'x-amzn-tls-version': 'TLSv1.3',
        'x-forwarded-proto': 'https',
        'x-forwarded-port': '443',
        'x-forwarded-for': '54.187.174.169',
        'accept': '*/*; q=0.5, application/json',
        'x-amzn-tls-cipher-suite': 'TLS_AES_128_GCM_SHA256',
        'x-amzn-trace-id': 'Root=1-687069ae-6095e5c4531c4cf46f973aba',
        'stripe-signature': (
            't=1752197550,v1=297aec9c1ddb1a36f08117d266df53488d872ddc'
            'dcbee75fde6c14b8ce5c5baf'
        ),
        'host': 'hdhbt2vmkop35asckzu3v37rue0nwfji.lambda-url.us-west-2.on.aws',
        'content-type': 'application/json; charset=utf-8',
        'cache-control': 'no-cache',
        'user-agent': 'Stripe/1.0 (+https://stripe.com/docs/webhooks)'
    },
    'requestContext': {
        'accountId': 'anonymous',
        'apiId': 'hdhbt2vmkop35asckzu3v37rue0nwfji',
        'domainName': (
            'hdhbt2vmkop35asckzu3v37rue0nwfji.lambda-url.us-west-2.on.aws'
        ),
        'domainPrefix': 'hdhbt2vmkop35asckzu3v37rue0nwfji',
        'http': {
            'method': 'POST',
            'path': '/',
            'protocol': 'HTTP/1.1',
            'sourceIp': '54.187.174.169',
            'userAgent': 'Stripe/1.0 (+https://stripe.com/docs/webhooks)'
        },
        'requestId': '5315feb3-236d-4d74-b95a-8ff97662ab54',
        'routeKey': '$default',
        'stage': '$default',
        'time': '11/Jul/2025:01:32:30 +0000',
        'timeEpoch': 1752197550282
    },
    'body': json.dumps({
        "id": "evt_1RjVpCBnnqL8bKFQgW5utjkx",
        "object": "event",
        "api_version": "2025-04-30.basil",
        "created": 1752197549,
        "data": {
            "object": {
                "id": (
                    "cs_live_a1TXYlVGuvm6EpHVvPN2CNvZkOJm8wdLDsEbWL2H1dXM"
                    "LyqDNWbwOusbSS"
                ),
                "object": "checkout.session",
                "adaptive_pricing": None,
                "after_expiration": None,
                "allow_promotion_codes": False,
                "amount_subtotal": 0,
                "amount_total": 0,
                "automatic_tax": {
                    "enabled": False,
                    "liability": None,
                    "provider": None,
                    "status": None
                },
                "billing_address_collection": "required",
                "cancel_url": "https://stripe.com",
                "client_reference_id": None,
                "client_secret": None,
                "collected_information": {
                    "shipping_details": None
                },
                "consent": {
                    "promotions": None,
                    "terms_of_service": "accepted"
                },
                "consent_collection": {
                    "payment_method_reuse_agreement": None,
                    "promotions": "none",
                    "terms_of_service": "required"
                },
                "created": 1752194191,
                "currency": "usd",
                "currency_conversion": None,
                "custom_fields": [],
                "custom_text": {
                    "after_submit": None,
                    "shipping_address": None,
                    "submit": None,
                    "terms_of_service_acceptance": None
                },
                "customer": "cus_SepUMjr1Ui3rQY",
                "customer_creation": "if_required",
                "customer_details": {
                    "address": {
                        "city": "Norwalk",
                        "country": "US",
                        "line1": "11125",
                        "line2": "Foster Rd.",
                        "postal_code": "90650",
                        "state": "CA"
                    },
                    "email": "anthony.ortiz0921@gmail.com",
                    "name": "Anthony Paul Ortiz",
                    "phone": "+15629641339",
                    "tax_exempt": "none",
                    "tax_ids": []
                },
                "customer_email": None,
                "discounts": [],
                "expires_at": 1752280590,
                "invoice": "in_1RjVpABnnqL8bKFQRaUFE7oi",
                "invoice_creation": None,
                "livemode": True,
                "locale": "auto",
                "metadata": {},
                "mode": "subscription",
                "origin_context": None,
                "payment_intent": None,
                "payment_link": "plink_1PbpdsBnnqL8bKFQTO9tsEgM",
                "payment_method_collection": "always",
                "payment_method_configuration_details": {
                    "id": "pmc_1Mxv0PBnnqL8bKFQwzdDhYTe",
                    "parent": None
                },
                "payment_method_options": {
                    "card": {
                        "request_three_d_secure": "automatic"
                    },
                    "us_bank_account": {
                        "verification_method": "automatic"
                    }
                },
                "payment_method_types": [
                    "card",
                    "us_bank_account"
                ],
                "payment_status": "paid",
                "permissions": None,
                "phone_number_collection": {
                    "enabled": True
                },
                "recovered_from": None,
                "saved_payment_method_options": {
                    "allow_redisplay_filters": [
                        "always"
                    ],
                    "payment_method_remove": "disabled",
                    "payment_method_save": None
                },
                "setup_intent": None,
                "shipping_address_collection": None,
                "shipping_cost": None,
                "shipping_options": [],
                "status": "complete",
                "submit_type": "auto",
                "subscription": "sub_1RjVp9BnnqL8bKFQkw80ddG7",
                "success_url": (
                    "https://www.coursecreator360.com/"
                    "change-password-page-5760"
                    "?session_id={CHECKOUT_SESSION_ID}"
                    "&action=purchase_completed&plan=premium&term=monthly"
                ),
                "total_details": {
                    "amount_discount": 0,
                    "amount_shipping": 0,
                    "amount_tax": 0
                },
                "ui_mode": "hosted",
                "url": None,
                "wallet_options": None
            }
        },
        "livemode": True,
        "pending_webhooks": 3,
        "request": {
            "id": None,
            "idempotency_key": None
        },
        "type": "checkout.session.completed"
    }),
    'isBase64Encoded': False
}


def test_with_location_id():
    """Test with location_id in metadata"""
    # Create a copy of the test event
    test_event_with_location = test_event.copy()
    body = json.loads(test_event_with_location['body'])
    
    # Add location_id to metadata
    body['data']['object']['metadata'] = {
        'location_id': 'test_location_123'
    }
    
    test_event_with_location['body'] = json.dumps(body)
    
    print("Testing with location_id in metadata...")
    print("=" * 60)
    
    # Mock context
    context = {}
    
    try:
        result = lambda_handler(test_event_with_location, context)
        print(f"Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def test_without_location_id():
    """Test without location_id (as in the original event)"""
    print("\nTesting without location_id...")
    print("=" * 60)
    
    # Mock context
    context = {}
    
    try:
        result = lambda_handler(test_event, context)
        print(f"Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    print("Lambda Function Test Script")
    print("=" * 60)
    print("Customer Email: anthony.ortiz0921@gmail.com")
    print("Customer Phone: +15629641339")
    print("Stripe Customer ID: cus_SepUMjr1Ui3rQY")
    print("Stripe Subscription ID: sub_1RjVp9BnnqL8bKFQkw80ddG7")
    print("=" * 60)
    
    # Test without location_id (will use Stripe customer ID lookup)
    print("\nTest 1: Using Stripe customer ID lookup")
    test_without_location_id()
    
    # Test with location_id in metadata
    print("\nTest 2: Using location_id from metadata")
    test_with_location_id()


if __name__ == "__main__":
    main() 