import os
import sys
import pytest
import traceback
from dotenv import load_dotenv
from utilities.customLogger import customLogger

# Add project root directory to python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Load environment variables from Configurations/.env or root .env
env_path = os.path.join(root_dir, "Configurations", ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv(dotenv_path=os.path.join(root_dir, ".env"))

def pytest_sessionstart(session):
    """Monkey-patch TerminalReporter to add _sessionstarttime for pytest-html-reporter compatibility."""
    import time
    terminal_reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminal_reporter:
        terminal_reporter._sessionstarttime = time.time()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Intercept test execution outcomes and log errors/exceptions to logs file."""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        test_name = item.nodeid.split("::")[-1]
        logger = customLogger(test_name)
        logger.error(f"=== TEST FAILURE DETECTED: {item.nodeid} ===")
        if call.excinfo:
            logger.error(f"Exception Type: {call.excinfo.type.__name__ if call.excinfo.type else 'Unknown'}")
            logger.error(f"Exception Value: {call.excinfo.value}")
            tb = "".join(traceback.format_tb(call.excinfo.tb))
            logger.error(f"Traceback:\n{tb}")
        logger.error("==========================================")
