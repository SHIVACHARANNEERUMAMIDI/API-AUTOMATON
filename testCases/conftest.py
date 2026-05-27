import os
import sys
from dotenv import load_dotenv

# Add project root directory to python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Load environment variables from the Configurations folder
env_path = os.path.join(root_dir, "Configurations", ".env")
load_dotenv(dotenv_path=env_path)

def pytest_sessionstart(session):
    """Monkey-patch TerminalReporter to add _sessionstarttime for pytest-html-reporter compatibility."""
    import time
    terminal_reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminal_reporter:
        terminal_reporter._sessionstarttime = time.time()

