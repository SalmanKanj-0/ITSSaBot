import json
import requests
from requests.auth import HTTPBasicAuth
import logging
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Jira API Configuration
JIRA_DOMAIN = "https://catawiki.atlassian.net"
EMAIL = 
API_TOKEN = 


def get_account_id(email):
    url = f"{JIRA_DOMAIN}/rest/api/3/user/search"
    auth = HTTPBasicAuth(EMAIL, API_TOKEN)
    headers = {"Accept": "application/json"}
    params = {"query": email}

    response = requests.get(url, headers=headers, auth=auth, params=params)
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("emailAddress") == email:
                return user.get("accountId")
    else:
        logger.error(f"Failed to fetch accountId. Status Code: {response.status_code}")
        logger.error(response.text)
    return None

def get_service_desk_id_by_project_key(project_key):
    url = f"{JIRA_DOMAIN}/rest/servicedeskapi/servicedesk"
    auth = HTTPBasicAuth(EMAIL, API_TOKEN)
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        data = response.json()
        for service_desk in data.get("values", []):
            if service_desk.get("projectKey") == project_key:
                return service_desk.get("id")
        logger.error(f"Service desk with project key {project_key} not found.")
    else:
        logger.error(f"Failed to get service desks. Status Code: {response.status_code}")
        logger.error(response.text)
    return None

def get_request_type_id(service_desk_id, request_type_name):
    url = f"{JIRA_DOMAIN}/rest/servicedeskapi/servicedesk/{service_desk_id}/requesttype"
    auth = HTTPBasicAuth(EMAIL, API_TOKEN)
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        data = response.json()
        for request_type in data.get("values", []):
            if request_type.get("name") == request_type_name:
                return request_type.get("id")
        logger.error(f"Request type '{request_type_name}' not found.")
    else:
        logger.error(f"Failed to get request types. Status Code: {response.status_code}")
        logger.error(response.text)
    return None

def create_jira_ticket(summary, description, reporter_email, project_key, request_type_name):
    """
    Creates a Jira Service Desk customer request with the given details.
    Returns the issue key and a constructed URL to the support portal.
    """
    try:
        # Step 1: Get Account ID for the Reporter
        account_id = get_account_id(reporter_email)
        if not account_id:
            logger.error(f"Unable to fetch accountId for email: {reporter_email}")
            return None, None

        # Step 2: Get Service Desk ID by Project Key
        service_desk_id = get_service_desk_id_by_project_key(project_key)
        if not service_desk_id:
            logger.error(f"Unable to fetch service desk ID for project key: {project_key}")
            return None, None

        # Step 3: Get Request Type ID
        request_type_id = get_request_type_id(service_desk_id, request_type_name)
        if not request_type_id:
            logger.error(f"Unable to fetch request type ID for: {request_type_name}")
            return None, None

        # Step 4: Create the Customer Request
        url = f"{JIRA_DOMAIN}/rest/servicedeskapi/request"
        auth = HTTPBasicAuth(EMAIL, API_TOKEN)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = {
            "serviceDeskId": service_desk_id,
            "requestTypeId": request_type_id,
            "requestFieldValues": {"summary": summary, "description": description},
            "raiseOnBehalfOf": account_id,
        }

        response = requests.post(url, headers=headers, auth=auth, data=json.dumps(payload), timeout=10)
        if response.status_code == 201:
            logger.info("Customer request created successfully.")
            request = response.json()
            logger.debug(f"Jira Response: {json.dumps(request, indent=2)}")  # Detailed response

            # Correct retrieval of issue key
            issue_key = request.get("issueKey") or request.get("key")
            if not issue_key:
                logger.error("Issue key not found in Jira response.")
                return None, None

            # Construct the support portal URL with the issue key
            # Assuming the portal can display the ticket based on the issue key appended
            ticket_url = f"https://catawiki.atlassian.net/servicedesk/customer/portal/21/{issue_key}"

            return issue_key, ticket_url
        else:
            logger.error(f"Failed to create customer request. Status Code: {response.status_code}")
            logger.error(response.text)
            return None, None

    except Exception as e:
        logger.error(f"Error creating Jira ticket: {e}")
        return None, None
