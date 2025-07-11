# GoHighLevel Phone Number Update Lambda

AWS Lambda function that automatically updates phone numbers in GoHighLevel (GHL) when Stripe checkout sessions are completed.

## Overview

This Lambda function performs a two-step update process:

### Step 1: Update Contact in Default Location
- Updates the **contact** in the main/default location (`c2DjRsOo4e13Od6ZTU6S`)
- This handles existing contacts that were created before the new subaccount
- **NEW**: Automatically adds 'close' and 'closed' tags to all contacts while preserving ALL existing tags
- **NEW**: Capitalizes first and last names properly (handles special cases like O'Connor, McDonald, Mary-Jane)
- Only updates phone number if it's different from the existing one
- Always fetches full contact details to ensure all tags are preserved (fixes previous bug where tags could be lost)

### Step 2: Update User in New Subaccount
- Waits for and finds the new subaccount location created from the Stripe customer
- Updates the **user** in that new subaccount with the phone number
- Includes retry logic to handle timing issues with new subaccount creation

## Authentication Flow

The function uses a two-step authentication process:
1. **Agency Access Token**: Retrieved from AWS Secrets Manager, used for:
   - Looking up locations by Stripe customer ID
   - Getting location-specific access tokens
   
2. **Location Access Token**: Generated for each location, used for:
   - Searching and updating contacts (in default location)
   - Searching and updating users (in new subaccount)

## Key Features

### Automatic Retry Logic
Since GHL locations may not be created immediately after a Stripe subscription (up to 5 minutes delay), the function includes retry logic:
- Retries up to 6 times with exponential backoff
- Wait times: 10s, 20s, 40s, 80s, 160s, 320s
- Total wait time: up to ~10 minutes

### Dual-Location Updates
1. **Default Location**: Always updates contacts in `c2DjRsOo4e13Od6ZTU6S`
2. **New Subaccount**: Updates users in the location created from Stripe customer

### Rate Limiting Protection
- Automatic retry with exponential backoff for rate-limited requests
- Handles 429 (Too Many Requests) responses gracefully

## Configuration

### Environment Variables
- `GHL_SECRET_NAME`: AWS Secrets Manager secret name (default: `GHLAccessKey`)
- `GHL_COMPANY_ID`: GoHighLevel company ID (default: `Cbjwl9dRdmiskYlzh8Oo`)

### AWS Secrets Manager
Store your GHL agency access token in AWS Secrets Manager with the name specified in `GHL_SECRET_NAME`.

## API Endpoints Used

### Agency-Level Endpoints (using agency token):
- `GET /saas-api/public-api/locations` - Find locations by Stripe customer ID
- `POST /oauth/locationToken` - Get location-specific access token

### Location-Level Endpoints (using location token):
- `GET /contacts/` - Search contacts by email
- `PUT /contacts/{id}` - Update contact phone
- `GET /users/` - Get users for location
- `PUT /users/{id}` - Update user phone

## Response Format

Success response includes both update results:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Phone numbers updated successfully",
    "default_location": {
      "location_id": "c2DjRsOo4e13Od6ZTU6S",
      "contacts_updated": 1
    },
    "new_subaccounts": {
      "total_users_updated": 1,
      "locations": [
        {
          "location_id": "nHM8w7EuJW8gSyPnKxDF",
          "users_updated": 1
        }
      ]
    },
    "customer_email": "customer@example.com",
    "customer_phone": "+15551234567",
    "stripe_customer_id": "cus_ABC123"
  }
}
```

## Testing

The function includes a test event at the bottom that you can use for local testing:
```bash
python3 update_ghl_phone_numbers.py
```

## Deployment

1. Install dependencies:
```bash
pip install -r requirements.txt -t .
```

2. Create deployment package:
```bash
zip -r lambda-function.zip .
```

3. Upload to AWS Lambda

4. Configure the Lambda function:
   - Runtime: Python 3.x
   - Handler: `update_ghl_phone_numbers.lambda_handler`
   - Timeout: At least 10 minutes (to handle retry logic)
   - Environment variables as needed

5. Set up Stripe webhook to send `checkout.session.completed` events to your Lambda function URL

## Error Handling

The function handles various error scenarios:
- Missing customer details in Stripe event
- Location not found (with retry logic)
- Failed authentication
- Rate limiting
- Network errors

All errors are logged and appropriate HTTP responses are returned.

## Important Notes

1. **Location Creation Delay**: GHL locations may take up to 5 minutes to be created after a Stripe subscription. The retry logic handles this automatically.

2. **Token Usage**: Always use the agency token for agency-level operations and location tokens for location-specific operations.

3. **Phone Format**: The function uses phone numbers as provided by Stripe (typically in E.164 format like `+15551234567` or formatted like `1 (555) 123-4567`).

4. **Dual Updates**: The function updates:
   - **Contacts** in the default location (for existing contacts)
   - **Users** in new subaccounts (for newly created location users)