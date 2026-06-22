import json
import os
from dotenv import load_dotenv

# Load environment variables from root .env
load_dotenv()

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(relative_path):
    """Load a JSON file relative to the project root. Returns empty dict on failure."""
    full_path = os.path.join(_ROOT_DIR, relative_path)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


class _Config:
    """
    Centralized configuration accessor.
    Loads credentials from .env and test data from JSON files under data/.
    Access pattern: Config.PROVIDER_ID, Config.UW_AGENT_USERNAME, etc.
    """

    def __init__(self):
        self._test_users = None
        self._providers = None

    # ------------------------------------------------------------------ #
    # Lazy loaders for JSON data files                                     #
    # ------------------------------------------------------------------ #

    @property
    def _user_data(self):
        if self._test_users is None:
            self._test_users = _load_json(os.path.join("data", "test_users.json"))
        return self._test_users

    @property
    def _provider_data(self):
        if self._providers is None:
            self._providers = _load_json(os.path.join("data", "providers.json"))
        return self._providers

    # ------------------------------------------------------------------ #
    # Credentials (from .env)                                              #
    # ------------------------------------------------------------------ #

    @property
    def UW_USERNAME(self):
        return os.getenv("UW_USERNAME")

    @property
    def UW_PASSWORD(self):
        return os.getenv("UW_PASSWORD")

    @property
    def UNDERWRITER_USERNAME(self):
        return os.getenv("UNDERWRITER_USERNAME")

    @property
    def UNDERWRITER_PASSWORD(self):
        return os.getenv("UNDERWRITER_PASSWORD")

    @property
    def USER_USERNAME(self):
        return os.getenv("USER_USERNAME")

    @property
    def USER_PASSWORD(self):
        return os.getenv("USER_PASSWORD")

    @property
    def TEST_CLIENT_ID(self):
        return os.getenv("TEST_CLIENT_ID")

    @property
    def UW_AGENT_USERNAME(self):
        """Credentials for the RM Callback retail user (separate from the UW agent)."""
        return os.getenv("UW_AGENT_USERNAME")

    @property
    def UW_AGENT_PASSWORD(self):
        return os.getenv("UW_AGENT_PASSWORD")

    # ------------------------------------------------------------------ #
    # Test User Persona (from data/test_users.json)                        #
    # ------------------------------------------------------------------ #

    @property
    def USER_FULL_NAME(self):
        return self._user_data.get("uw_agent", {}).get("name", "")

    @property
    def USER_EMAIL(self):
        return self._user_data.get("uw_agent", {}).get("email", "")

    @property
    def USER_PHONE(self):
        return self._user_data.get("uw_agent", {}).get("phone", "")

    @property
    def USER_INSURANCE_TYPE(self):
        return self._user_data.get("uw_agent", {}).get("insurance_type", "")

    # ------------------------------------------------------------------ #
    # Provider Data (from data/providers.json)                             #
    # ------------------------------------------------------------------ #

    @property
    def PROVIDER_ID(self):
        return self._provider_data.get("default_provider", {}).get("provider_id", "123")

    @property
    def PROVIDER_NAME(self):
        return self._provider_data.get("default_provider", {}).get("provider_name", "AutoTestProvider")


# Singleton instance — import and use directly: from utilities.config import Config
Config = _Config()
