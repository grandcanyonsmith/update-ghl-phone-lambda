import json
import requests
import boto3
import logging
import os
import time
import hmac
import hashlib
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    """
    AWS Lambda handler for processing Stripe webhook events.
    Updates phone numbers in GoHighLevel for contacts and users.
    """
    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Validate environment variables
    required_env_vars = {
        'REGION_NAME': os.environ.get('REGION_NAME', 'us-west-2'),
        'GHL_SECRET_NAME': os.environ.get('GHL_SECRET_NAME', 'GHLAccessKey'),
        'GHL_COMPANY_ID': os.environ.get(
            'GHL_COMPANY_ID', 'Cbjwl9dRdmiskYlzh8Oo'
        ),
        'STRIPE_WEBHOOK_SECRET': os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    }
    
    REGION_NAME = required_env_vars['REGION_NAME']
    DEFAULT_LOCATION_ID = 'c2DjRsOo4e13Od6ZTU6S'
    
    def verify_stripe_signature(payload, signature, secret):
        """Verify Stripe webhook signature if secret is provided"""
        if not secret:
            logger.warning(
                "Stripe webhook secret not configured, skipping verification"
            )
            return True
            
        try:
            # Extract timestamp and signature from header
            elements = signature.split(',')
            timestamp = None
            signatures = []
            
            for element in elements:
                key, value = element.split('=')
                if key == 't':
                    timestamp = value
                elif key == 'v1':
                    signatures.append(value)
            
            if not timestamp or not signatures:
                return False
            
            # Construct signed payload
            signed_payload = f"{timestamp}.{payload}"
            
            # Compute expected signature
            expected_sig = hmac.new(
                secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Check if any signature matches
            return any(
                hmac.compare_digest(expected_sig, sig) for sig in signatures
            )
            
        except Exception as e:
            logger.error(f"Error verifying Stripe signature: {e}")
            return False

    def get_secret(secret_name):
        """Retrieve secret from AWS Secrets Manager"""
        client = boto3.client('secretsmanager', region_name=REGION_NAME)
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
            secret = get_secret_value_response['SecretString']
            logger.info("Retrieved secret successfully")
            return secret
        except ClientError as e:
            logger.error(f"Unable to retrieve secret: {e}")
            raise e

    class GoHighLevelClient:
        """Client for interacting with GoHighLevel API"""
        
        def __init__(self, company_id, agency_access_token):
            self.company_id = company_id
            self.agency_access_token = agency_access_token

        def get_locations_by_stripe_customer_with_retry(
            self, customer_id, subscription_id=None,
            max_retries=6, initial_delay=10
        ):
            """
            Get location IDs with retry logic.
            Retries: 10s, 20s, 40s, 80s, 160s, 320s (total ~10 minutes)
            """
            delay = initial_delay
            
            for attempt in range(max_retries):
                locations = self.get_locations_by_stripe_customer(
                    customer_id, subscription_id
                )
                
                if locations:
                    logger.info(
                        f"Found locations on attempt {attempt + 1}"
                    )
                    return locations
                
                if attempt < max_retries - 1:
                    logger.info(
                        f"No locations found yet, waiting {delay} seconds "
                        f"before retry (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
            
            logger.warning(
                f"No locations found after {max_retries} attempts"
            )
            return []

        def get_locations_by_stripe_customer(
            self, customer_id, subscription_id=None
        ):
            """Get location IDs by Stripe customer ID"""
            url = (
                "https://services.leadconnectorhq.com/saas-api/"
                "public-api/locations"
            )
            headers = {
                "Authorization": f"Bearer {self.agency_access_token}",
                "Version": "2021-04-15",
                "Accept": "application/json"
            }
            params = {
                "companyId": self.company_id,
                "customerId": customer_id
            }
            if subscription_id:
                params["subscriptionId"] = subscription_id
            
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    response_data = response.json()
                    locations = response_data.get('data', [])
                    logger.info(
                        f"Found {len(locations)} locations for "
                        f"Stripe customer {customer_id}"
                    )
                    return locations
                else:
                    logger.error(
                        f"Failed to get locations: "
                        f"{response.status_code} {response.text}"
                    )
                    return []
            except Exception as e:
                logger.error(f"Error getting locations: {e}")
                return []

        def get_location_access_token(self, location_id):
            """Get location-specific access token"""
            url = "https://services.leadconnectorhq.com/oauth/locationToken"
            payload = {
                "companyId": self.company_id,
                "locationId": location_id
            }
            headers = {
                "Version": "2021-07-28",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.agency_access_token}"
            }
            
            # Retry logic for rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                response = requests.post(url, data=payload, headers=headers)
                
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 2
                    logger.info(
                        f"Rate limited, waiting {wait_time} seconds"
                    )
                    time.sleep(wait_time)
                    continue
                
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    logger.info(
                        f"Retrieved location access token for {location_id}"
                    )
                    return response_data.get("access_token", "")
                else:
                    logger.error(
                        f"Failed to get location token: "
                        f"{response.status_code} {response.text}"
                    )
                    return None
            
            logger.error("Failed to get location token after retries")
            return None

        def search_contacts_by_email(
            self, location_id, email, location_access_token
        ):
            """Search for contacts by email"""
            url = "https://services.leadconnectorhq.com/contacts/"
            headers = {
                "Authorization": f"Bearer {location_access_token}",
                "Version": "2021-07-28",
                "Accept": "application/json"
            }
            params = {
                "locationId": location_id,
                "query": email,
                "limit": 100
            }
            
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    contacts = data.get("contacts", [])
                    # Filter for exact email match
                    matching_contacts = [
                        c for c in contacts if c.get('email') == email
                    ]
                    logger.info(
                        f"Found {len(matching_contacts)} contacts "
                        f"with email {email}"
                    )
                    return matching_contacts
                else:
                    logger.error(
                        f"Failed to search contacts: "
                        f"{response.status_code} {response.text}"
                    )
                    return []
            except Exception as e:
                logger.error(f"Error searching contacts: {e}")
                return []

        def update_contact_phone_and_tags(
            self, contact_id, phone, location_access_token,
            tags_to_add=None
        ):
            """Update contact phone and add tags if not already present"""
            # First, get the contact to check existing tags
            get_url = (
                f"https://services.leadconnectorhq.com/contacts/{contact_id}"
            )
            headers = {
                "Authorization": f"Bearer {location_access_token}",
                "Version": "2021-07-28",
                "Accept": "application/json"
            }
            
            try:
                # Get current contact data
                get_response = requests.get(get_url, headers=headers)
                if get_response.status_code != 200:
                    logger.error(
                        f"Failed to get contact: "
                        f"{get_response.status_code} {get_response.text}"
                    )
                    return False
                    
                contact_data = get_response.json()
                existing_tags = contact_data.get('tags', [])
                
                # Prepare update payload
                payload = {"phone": phone}
                
                # Add tags if provided and not already present
                if tags_to_add:
                    if isinstance(tags_to_add, list):
                        tags_to_add_list = tags_to_add
                    else:
                        tags_to_add_list = [tags_to_add]
                    new_tags = []
                    
                    for tag in tags_to_add_list:
                        if tag not in existing_tags:
                            new_tags.append(tag)
                    
                    if new_tags:
                        # Combine existing tags with new tags
                        payload['tags'] = existing_tags + new_tags
                        logger.info(
                            f"Adding tags to contact {contact_id}: {new_tags}"
                        )
                
                # Update contact
                update_url = (
                    f"https://services.leadconnectorhq.com/contacts/"
                    f"{contact_id}"
                )
                headers["Content-Type"] = "application/json"
                
                response = requests.put(
                    update_url, headers=headers, json=payload
                )
                if response.status_code == 200:
                    logger.info(
                        f"Updated contact {contact_id} with phone {phone} "
                        f"and tags"
                    )
                    return True
                else:
                    logger.error(
                        f"Failed to update contact: "
                        f"{response.status_code} {response.text}"
                    )
                    return False
            except Exception as e:
                logger.error(f"Error updating contact: {e}")
                return False

        def update_contact_phone(
            self, contact_id, phone, location_access_token
        ):
            """Update contact phone number"""
            return self.update_contact_phone_and_tags(
                contact_id, phone, location_access_token, tags_to_add=None
            )

        def get_users_by_location(self, location_id, location_access_token):
            """Get all users for a location"""
            url = "https://services.leadconnectorhq.com/users/"
            headers = {
                "Authorization": f"Bearer {location_access_token}",
                "Version": "2021-07-28",
                "Accept": "application/json"
            }
            params = {"locationId": location_id}
            
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    users = data.get("users", [])
                    logger.info(
                        f"Found {len(users)} users for location {location_id}"
                    )
                    return users
                else:
                    logger.error(
                        f"Failed to get users: "
                        f"{response.status_code} {response.text}"
                    )
                    return []
            except Exception as e:
                logger.error(f"Error getting users: {e}")
                return []

        def update_user_phone(self, user_id, phone, location_access_token):
            """Update user phone number"""
            url = f"https://services.leadconnectorhq.com/users/{user_id}"
            headers = {
                "Authorization": f"Bearer {location_access_token}",
                "Version": "2021-07-28",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            payload = {
                "phone": phone,
                "isEjectedUser": False
            }
            
            try:
                response = requests.put(url, headers=headers, json=payload)
                if response.status_code == 200:
                    logger.info(
                        f"Updated user {user_id} with phone {phone}"
                    )
                    return True
                else:
                    logger.error(
                        f"Failed to update user: "
                        f"{response.status_code} {response.text}"
                    )
                    return False
            except Exception as e:
                logger.error(f"Error updating user: {e}")
                return False

    # Main handler logic
    try:
        # Verify Stripe webhook signature
        stripe_signature = event.get('headers', {}).get('stripe-signature', '')
        stripe_secret = required_env_vars['STRIPE_WEBHOOK_SECRET']
        
        if stripe_secret and not verify_stripe_signature(
            event.get('body', ''), stripe_signature, stripe_secret
        ):
            logger.error("Invalid Stripe webhook signature")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid webhook signature'})
            }
        
        # Parse event
        event_body = json.loads(event['body'])
        logger.info(f"Processing event: {event_body.get('type', 'unknown')}")
        
        # Only process checkout.session.completed events
        if event_body.get('type') != 'checkout.session.completed':
            logger.info(f"Ignoring event type: {event_body.get('type')}")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Event type not processed'})
            }
        
        # Extract customer data
        checkout_data = event_body.get('data', {}).get('object', {})
        customer_details = checkout_data.get('customer_details', {})
        
        customer_email = customer_details.get('email')
        customer_phone = customer_details.get('phone')
        stripe_customer_id = checkout_data.get('customer')
        stripe_subscription_id = checkout_data.get('subscription')
        
        # Validate required fields
        if not customer_email:
            logger.error("No customer email found")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No customer email found'})
            }
        
        if not customer_phone:
            logger.error("No customer phone found")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No customer phone found'})
            }
        
        if not stripe_customer_id:
            logger.error("No Stripe customer ID found")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No Stripe customer ID found'})
            }
        
        logger.info(
            f"Processing customer: {customer_email} "
            f"with phone: {customer_phone} "
            f"Stripe customer: {stripe_customer_id}"
        )
        
        # Initialize GHL client
        secret_name = required_env_vars['GHL_SECRET_NAME']
        company_id = required_env_vars['GHL_COMPANY_ID']
        agency_access_token = get_secret(secret_name)
        ghl_client = GoHighLevelClient(company_id, agency_access_token)
        
        # STEP 1: Update contact in default location
        logger.info(
            f"Step 1: Updating contact in default location: "
            f"{DEFAULT_LOCATION_ID}"
        )
        
        default_location_token = ghl_client.get_location_access_token(
            DEFAULT_LOCATION_ID
        )
        
        contacts_updated_default = 0
        tags_added_default = 0
        if default_location_token:
            contacts = ghl_client.search_contacts_by_email(
                DEFAULT_LOCATION_ID, customer_email, default_location_token
            )
            logger.info(
                f"Found {len(contacts)} contacts in default location"
            )
            
            for contact in contacts:
                contact_id = contact.get('id')
                existing_tags = contact.get('tags', [])
                
                if not contact.get('phone'):
                    # Update phone and add tags
                    if ghl_client.update_contact_phone_and_tags(
                        contact_id, customer_phone, default_location_token,
                        tags_to_add=['close', 'closed']
                    ):
                        contacts_updated_default += 1
                        logger.info(
                            f"Updated contact {contact_id} in "
                            f"default location with phone and tags"
                        )
                else:
                    # Phone exists, check if we need to add tags
                    needs_close = 'close' not in existing_tags
                    needs_closed = 'closed' not in existing_tags
                    
                    if needs_close or needs_closed:
                        if ghl_client.update_contact_phone_and_tags(
                            contact_id, contact.get('phone'), 
                            default_location_token,
                            tags_to_add=['close', 'closed']
                        ):
                            tags_added_default += 1
                            logger.info(
                                f"Added tags to contact {contact_id} "
                                f"in default location"
                            )
                    else:
                        logger.info(
                            f"Contact {contact.get('id')} already has "
                            f"phone: {contact.get('phone')} and tags"
                        )
        else:
            logger.error("Failed to get token for default location")
        
        # STEP 2: Update user in new subaccount
        logger.info(
            f"Step 2: Looking for new subaccount for Stripe customer: "
            f"{stripe_customer_id}"
        )
        
        new_location_ids = (
            ghl_client.get_locations_by_stripe_customer_with_retry(
                stripe_customer_id, stripe_subscription_id
            )
        )
        
        total_users_updated = 0
        processed_locations = []
        
        for location_id in new_location_ids:
            logger.info(f"Processing new subaccount: {location_id}")
            
            location_access_token = ghl_client.get_location_access_token(
                location_id
            )
            if not location_access_token:
                logger.error(f"Failed to get token for {location_id}")
                continue
            
            users = ghl_client.get_users_by_location(
                location_id, location_access_token
            )
            
            users_updated = 0
            for user in users:
                if user.get('email') == customer_email:
                    if not user.get('phone'):
                        user_id = user.get('id')
                        if ghl_client.update_user_phone(
                            user_id, customer_phone, location_access_token
                        ):
                            users_updated += 1
                            logger.info(
                                f"Updated user {user_id} in new subaccount"
                            )
                    else:
                        logger.info(
                            f"User {user.get('id')} already has phone: "
                            f"{user.get('phone')}"
                        )
            
            total_users_updated += users_updated
            processed_locations.append({
                'location_id': location_id,
                'users_updated': users_updated
            })
        
        # Return response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Phone numbers updated successfully',
                'default_location': {
                    'location_id': DEFAULT_LOCATION_ID,
                    'contacts_updated': contacts_updated_default,
                    'tags_added': tags_added_default
                },
                'new_subaccounts': {
                    'total_users_updated': total_users_updated,
                    'locations': processed_locations
                },
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'stripe_customer_id': stripe_customer_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


if __name__ == "__main__":
    from test_lambda import test_event
    lambda_handler(test_event, {}) 