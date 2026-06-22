import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.user_actions import UserActions
from utilities.customLogger import customLogger

logger = customLogger("TestAgentChats")

# Known-invalid chat ID used for the negative test (does not exist on the server)
_INVALID_CHAT_ID = "INVALID_CHAT_ID_000000000000"

@pytest.mark.agent
class TestAgentChats:
    @classmethod
    def setup_class(cls):
        cls.user_name = os.getenv("UW_USERNAME")
        cls.user_pass = os.getenv("UW_PASSWORD")
        if not cls.user_name or not cls.user_pass:
            raise ValueError("Mandatory environment variables (UW_USERNAME, UW_PASSWORD) are missing.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_agent_chats_list(self):
        """Verify fetching the list of agent chats with paging parameters."""
        logger.info(f"Login as AGENT/UNDERWRITER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info("Fetching paged agent chats...")
        res = UserActions.get_agent_chats(page=0, size=5)

        # RC3: Business assertions are the primary checks; isinstance is a supporting check
        assert res.status_code == 200, f"Failed to fetch agent chats: {res.text}"

        data = res.json()
        assert "content" in data, "Response dictionary missing 'content' key"

        chats = data["content"]
        assert isinstance(chats, list), "Expected 'content' to be a list"

        logger.info(f"Discovered {len(chats)} agent chats in the current page.")

    # ------------------------------------------------------------------ #
    # RC2: Split positive and negative scenarios into separate test methods
    # ------------------------------------------------------------------ #

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_chat_by_valid_id(self):
        """Positive test — verify fetching an agent chat by a real, dynamically discovered ID."""
        logger.info(f"Login as AGENT/UNDERWRITER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info("Fetching list of chats to extract a dynamic ID...")
        res_list = UserActions.get_agent_chats(page=0, size=5)
        assert res_list.status_code == 200, f"Pre-condition failed: could not list agent chats: {res_list.text}"

        data = res_list.json()
        chats = data.get("content", []) if isinstance(data, dict) else data
        assert len(chats) > 0, "No agent chats found — cannot run positive ID lookup test"

        first_chat = chats[0]
        chat_id = first_chat.get("id") or first_chat.get("chatId")
        assert chat_id is not None, "First chat in list has no 'id' or 'chatId' field"
        logger.info(f"Using dynamic Chat ID: {chat_id}")

        logger.info(f"Fetching agent chat by ID: {chat_id}...")
        res = UserActions.get_agent_chat_by_id(chat_id)

        # RC3: Business assertions first — status, required fields, ID match
        assert res.status_code == 200, f"Expected 200 for valid chat ID {chat_id}, got {res.status_code}: {res.text}"

        chat_detail = res.json()
        assert isinstance(chat_detail, dict), "Expected chat details to be a dictionary object"
        assert "id" in chat_detail or "chatId" in chat_detail, "Chat detail missing identifier field"

        returned_id = str(chat_detail.get("id") or chat_detail.get("chatId"))
        assert returned_id == str(chat_id), \
            f"Returned chat ID {returned_id} does not match requested ID {chat_id}"

        logger.info(f"Successfully retrieved and validated chat details for ID {chat_id}.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_chat_by_invalid_id(self):
        """Negative test — verify the API returns 404 for a non-existent chat ID."""
        logger.info(f"Login as AGENT/UNDERWRITER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info(f"Fetching agent chat with invalid ID: {_INVALID_CHAT_ID}...")
        res = UserActions.get_agent_chat_by_id(_INVALID_CHAT_ID)

        assert res.status_code == 404, \
            f"Expected 404 for invalid chat ID '{_INVALID_CHAT_ID}', got {res.status_code}: {res.text}"
        logger.info(f"Server correctly returned 404 for non-existent chat ID '{_INVALID_CHAT_ID}'.")
