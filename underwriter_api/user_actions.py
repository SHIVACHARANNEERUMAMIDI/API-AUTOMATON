from utilities.api_client import API_CLIENT

def rm_callback_request(name, email, phone, insurance_type):
    """Request a callback from an RM (Relationship Manager)."""
    query = """
    query RmCallbackRequest($name: String!, $email: String!, $phone: String!, $insuranceType: String!) {
      rmCallbackRequest(
        rmCallBackRequest: {
          customerName: $name, 
          customerEmailId: $email, 
          customerMobileNo: $phone, 
          insuranceType: $insuranceType
        }
      ) {
        success
        message
      }
    }
    """
    variables = {
        "name": name,
        "email": email,
        "phone": phone,
        "insuranceType": insurance_type
    }
    return API_CLIENT.post_graphql(query, variables)
def get_personal_policies(client_id, client_type="INDIVIDUAL", expiry_type="ACTIVE", year="", insurance_type="", insurance_sub_type=""):
    """Fetch personal policies for a client."""
    query = """
    {
      getPersonalPolicies(
        clientId: "%s"
        clientType: %s
        expiryType: %s
        year: "%s"
        insuranceType: "%s"
        insuranceSubType: "%s"
      ) {
        totalPolicies
        totalPremiumAmount
        activePolicies
        policies {
          id
          policyNumber
          status
          companyName
          insuranceType
          productSubType
          issuedOn
          expiresOn
        }
      }
    }
    """ % (client_id, client_type, expiry_type, year, insurance_type, insurance_sub_type)
    return API_CLIENT.post_graphql(query)

def get_portfolio_v2(client_id, client_type="RETAIL_INDIVIDUAL"):
    """Fetch client portfolio v2."""
    query = """
    {
      getPortfolioV2(clientId: "%s", clientType: %s) {
        ctc
        overallSuggestions {
          insuranceName
          riskLevel
        }
        data {
          insuranceMainName
          company {
            sumAssured
            premium
          }
          personal {
            sumAssured
            premium
          }
        }
      }
    }
    """ % (client_id, client_type)
    return API_CLIENT.post_graphql(query)

def get_all_claims_by_client_id(client_id):
    """Fetch all claims for a client."""
    return API_CLIENT.get_rest("claims/getAllClaimsByClientId", params={"clientId": client_id})

def get_risk_score(client_id):
    """
    Fetches risk score using getPortfolioV2 GraphQL query as the REST endpoint is 404.
    """
    query = """
    query getPortfolioV2($clientId: String!, $clientType: ClientType!) {
      getPortfolioV2(clientId: $clientId, clientType: $clientType) {
        riskScore {
          healthInsurance { score status }
          lifeInsurance { score status }
          motorInsurance { score status }
          homeInsurance { score status }
        }
      }
    }
    """
    variables = {
        "clientId": client_id,
        "clientType": "RETAIL_INDIVIDUAL"
    }
    return API_CLIENT.post_graphql(query, variables)
def get_expired_policies_year_limit(client_id):
    """Fetch expired policies year limit."""
    query = """
    {
      getExpiredPoliciesYearLimit(clientId: "%s") {
        success
        message
        data {
          expiredPolicyYearLimitMin
          expiredPolicyYearLimitHigh
        }
      }
    }
    """ % client_id
    return API_CLIENT.post_graphql(query)

def get_child_and_parent_company_details(client_id):
    """Fetch child and parent company details."""
    query = """
    query GetChildAndParentCompanyDetails($clientId: String!) {
      getChildAndParentCompanyDetails(clientId: $clientId) {
        parentCompanyDetails {
          id
          clientId
          companyName
        }
        childCompanyDetailsList {
          id
          clientId
          companyName
        }
      }
    }
    """
    variables = {"clientId": client_id}
    return API_CLIENT.post_graphql(query, variables)

def get_smart_advisory_tips():
    """Fetch smart advisory tips."""
    return API_CLIENT.get_rest("smart-advisory-tips")

def update_login_time(user_name):
    """Update login time for a user."""
    query = """
    mutation UpdateLoginTime($userName: String!) {
      updateLoginTime(userName: $userName) {
        loggedInAtLeastOnce
      }
    }
    """
    variables = {"userName": user_name}
    return API_CLIENT.post_graphql(query, variables)
def get_logged_in_user_roles():
    """Fetch logged in user roles access."""
    return API_CLIENT.get_mt_rest("getLoggedInUserRolesAccess")

def get_insurance_type_data(client_type=None):
    """Fetch insurance type data."""
    query = """
    query GetInsuranceTypeData($clientType: String) {
      getInsuranceTypeData(clientType: $clientType) {
        id
        productType
        insuranceType
        subType
        category
      }
    }
    """
    variables = {"clientType": client_type}
    return API_CLIENT.post_graphql(query, variables)

def get_master_data(data_types=["INSURANCETYPEDATA"]):
    """Fetch master data."""
    query = """
    query GetMasterData($input: [MasterDataType]!) {
      getMasterData(input: $input) {
        response {
          dataType
          data
        }
      }
    }
    """
    variables = {"input": data_types}
    return API_CLIENT.post_graphql(query, variables)

def register_retail_individual(first_name, last_name, email, mobile):
    """Register a new retail individual."""
    data = {
        "firstName": first_name,
        "lastName": last_name,
        "emailId": email,
        "mobileNumber": mobile
    }
    return API_CLIENT.post_rest("register/retailIndividual", data=data)

def get_risk_analysis_report_tickets(page=1, size=10, tabs="ALL"):
    """Fetch RAR tickets."""
    params = {
        "page": page,
        "size": size,
        "tabs": tabs
    }
    return API_CLIENT.get_rest("getRiskAnalysisReportTickets", params=params)

def get_sales():
    """Fetch sales data."""
    return API_CLIENT.get_rest("sales")

def get_mobile_app_info():
    """Fetch mobile app info."""
    return API_CLIENT.get_rest("mobile-app/info", _include_auth=False)

def list_chatbot_sessions():
    """List chatbot sessions."""
    return API_CLIENT.get_rest("chatbot/sessions")

def get_chatbot_request_count():
    """Get chatbot request count."""
    return API_CLIENT.get_rest("chatbot/request-count")

def delete_chatbot_session(session_id):
    """Delete a chatbot session."""
    return API_CLIENT._request("DELETE", f"{API_CLIENT.paisaplan_base.rstrip('/')}/chatbot/session/{session_id}")

def chatbot_chat(message, session_id):
    """Send a message to the chatbot."""
    payload = {
        "message": message,
        "sessionId": session_id
    }
    headers = {"Accept": "text/event-stream"}
    return API_CLIENT._request("POST", f"{API_CLIENT.paisaplan_base.rstrip('/')}/chatbot/chat", json=payload, headers=headers)

def rename_chatbot_session(session_id, title):
    """Rename a chatbot session."""
    payload = {"title": title}
    return API_CLIENT._request("PATCH", f"{API_CLIENT.paisaplan_base.rstrip('/')}/chatbot/session/{session_id}", json=payload)

def get_chatbot_agent_availability():
    """Check availability of free agents."""
    return API_CLIENT.get_rest("chatbot/agent/availability")

def get_chatbot_session_history(session_id):
    """Retrieve chronological chat history for a specific session."""
    return API_CLIENT.get_rest(f"chatbot/session/{session_id}/chats")

def get_tour_details(user_name):
    """Fetch tour details for the user."""
    return API_CLIENT.get_mt_rest("getTourDetails", params={"userName": user_name})

def get_rar_master_data(insurance_type):
    """Fetch RAR master data for a specific insurance type."""
    return API_CLIENT.get_rest(f"rarMasterData/getMasterData/{insurance_type}")

def save_rar_info(ticket_id, policy_id, insurance_type, policy_strengths):
    """Save or update RAR info."""
    params = {
        "riskAnalysisReportTicketId": ticket_id,
        "riskAnalysisReportStatus": "SAVE"
    }
    payload = {
        "rarTicketPolicyIds": [policy_id],
        "policyId": policy_id,
        "insuranceType": insurance_type,
        "policyStrengths": policy_strengths
    }
    return API_CLIENT.post_rest("saveOrUpdateRarInfo", data=payload, params=params)

def download_rar_excel(start_date, end_date):
    """Download RAR excel report."""
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    return API_CLIENT.get_rest("downloadRarExcel", params=params)

def submit_claim(dto, files_dict):
    """Submit a claim with multiple documents."""
    # type and dto are @RequestPart in IndividualClaimsController
    multipart_files = files_dict.copy()
    multipart_files["type"] = (None, "Submit", "application/json")
    multipart_files["dto"] = (None, json.dumps(dto), "application/json")
    
    return API_CLIENT.post_multipart("claims", files=multipart_files, data={})

def download_dms_document(filename, doc_id):
    """Download a document from DMS (Root URL)."""
    url = f"https://api-dev.callmeooo.com/download/dms/{filename}/{doc_id}"
    headers = {"Accept": "application/pdf"}
    return API_CLIENT._request("GET", url, headers=headers)

def upload_image(client_id, file_path):
    """Upload an image for a client."""
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "image/png")}
        data = {"clientId": client_id}
        return API_CLIENT.post_multipart("fileUpload/uploadImage", files=files, data=data)

def upload_personal_documents(user_name, document_type, files_list):
    """Upload personal documents."""
    # files_list should be a list of tuples: (field_name, (filename, content, mime_type))
    data = {
        "userName": user_name,
        "documentType": document_type
    }
    url = f"{API_CLIENT.paisaplan_base.rstrip('/')}/fileUpload/uploadPersonal"
    return API_CLIENT._request("POST", url, files=files_list, data=data, headers={"Content-Type": None})

def download_renewal_policies(start_date, end_date):
    """Download renewal policies (MT/Root URL)."""
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    return API_CLIENT.get_mt_rest("download/renewalPolicies", params=params)

def create_policy_ticket(client_id, policy_number, status, file_path):
    """Create a policy ticket."""
    ticket_payload = {
        "clientId": client_id,
        "policyNumber": policy_number,
        "status": status
    }
    with open(file_path, "rb") as f:
        files = {"policyDocument": (os.path.basename(file_path), f.read(), "application/pdf")}
        data = {
            "form": json.dumps(ticket_payload),
            "isTicketRequired": "true"
        }
        return API_CLIENT.post_multipart("policy/create-ticket", files=files, data=data)

def save_or_update_insurance_profile(profile_dto):
    """Save or update insurance profile."""
    return API_CLIENT.post_rest("profile/saveOrUpdateInsuranceProfile", data=profile_dto)

def get_insurance_profile(client_id=None):
    """Fetch insurance profile (uses logged-in user context)."""
    return API_CLIENT.get_rest("profile")

def upload_document(client_id, client_type, request_type, insurance_type, sub_type, file_path):
    """Upload a document with metadata."""
    metadata = {
        "clientId": client_id,
        "clientType": client_type,
        "requestType": request_type,
        "otherInformation": json.dumps({
            "insuranceType": insurance_type,
            "productSubType": sub_type
        })
    }
    with open(file_path, "rb") as f:
        # metadata is @RequestPart, documentType is @RequestParam
        files = {
            "file": (os.path.basename(file_path), f.read(), "application/pdf"),
            "metadata": (None, json.dumps(metadata), "application/json")
        }
        data = {
            "documentType": "POLICY_DOCUMENT"
        }
        return API_CLIENT.post_multipart("fileUpload/uploadDocument", files=files, data=data)

def get_agent_chats(page=0, size=5):
    """Fetch paged agent chats."""
    params = {
        "page": page,
        "size": size
    }
    headers = {"Accept": "application/json"}
    return API_CLIENT.get_rest("agent-chats", params=params, headers=headers)

def get_agent_chat_by_id(chat_id):
    """Fetch a specific agent chat by ID."""
    headers = {"Accept": "application/json"}
    return API_CLIENT.get_rest(f"agent-chats/{chat_id}", headers=headers)

def check_pwned_password_range(hash_prefix):
    """
    GET https://api.pwnedpasswords.com/range/{hash_prefix}
    Queries Have I Been Pwned passwords API using standard k-Anonymity SHA-1 prefix.
    """
    url = f"https://api.pwnedpasswords.com/range/{hash_prefix.upper()}"
    headers = {
        "Accept": "text/plain",
        "add-padding": "true",
        "sec-ch-ua-platform": '"Windows"',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
    }
    return API_CLIENT._request("GET", url, headers=headers, _include_auth=False)


