import os
import json
import pytest
from utilities.api_client import API_CLIENT
from underwriter_api.user_actions import UserActions
from utilities.customLogger import customLogger

logger = customLogger("TestAgentChats")

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
        
        assert res.status_code == 200, f"Failed to fetch agent chats: {res.text}"
        
        data = res.json()
        logger.info(f"Agent Chats Response: {json.dumps(data, indent=2)}")
        
        assert isinstance(data, (dict, list)), "Response should be a JSON list or dictionary"
        
        if isinstance(data, dict):
            assert "content" in data, "Response dictionary missing 'content' key"
            chats = data["content"]
            assert isinstance(chats, list), "Expected 'content' to be a list"
        else:
            chats = data
            assert isinstance(chats, list), "Expected response to be a list"
        logger.info(f"Discovered {len(chats)} agent chats in the current page.")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_agent_chat_by_id(self):
        """Verify fetching an agent chat by a specific ID."""
        logger.info(f"Login as AGENT/UNDERWRITER ({self.user_name})...")
        API_CLIENT.set_credentials(self.user_name, self.user_pass)

        logger.info("Fetching list of chats to extract a dynamic ID...")
        res_list = UserActions.get_agent_chats(page=0, size=5)
        chat_id_to_test = None
        
        if res_list.status_code == 200:
            data = res_list.json()
            chats = data.get("content", []) if isinstance(data, dict) else data
            if chats and len(chats) > 0:
                first_chat = chats[0]
                chat_id_to_test = first_chat.get("id") or first_chat.get("chatId")
                logger.info(f"Found dynamic Chat ID to test: {chat_id_to_test}")

        if not chat_id_to_test:
            chat_id_to_test = "1505816378679222272"
            logger.info(f"No active chats found in list. Falling back to specified Chat ID: {chat_id_to_test}")

        logger.info(f"Fetching agent chat by ID: {chat_id_to_test}...")
        res = UserActions.get_agent_chat_by_id(chat_id_to_test)
        
        assert res.status_code in [200, 404], f"Unexpected status code from get_agent_chat_by_id: {res.status_code} ({res.text})"
        
        if res.status_code == 200:
            chat_detail = res.json()
            assert isinstance(chat_detail, dict), "Expected chat details to be a dictionary object"
            # Business validation
            assert "id" in chat_detail or "chatId" in chat_detail, "Chat detail missing identifier field"
            logger.info(f"Successfully retrieved chat details:\n{json.dumps(chat_detail, indent=2)}")
        else:
            logger.info(f"Chat ID {chat_id_to_test} was not found on server (404), which is a valid API response for a non-existent ID.")
