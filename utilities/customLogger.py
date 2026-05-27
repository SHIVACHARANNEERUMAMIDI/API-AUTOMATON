import inspect
import logging
import time
import os

def customLogger():
    # Get the class/method name from where the logger method is called
    logName = inspect.stack()[1][3]
    logger = logging.getLogger(logName)
    logger.setLevel(logging.DEBUG)
    
    # Dynamically resolve root path and ensure Logs/ directory exists
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(root_dir, "Logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        
    # File handler to save log to Logs/DD-MM-YY.text
    log_file = os.path.join(logs_dir, f'{time.strftime("%d-%m-%y")}.text')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setLevel(logging.DEBUG)
    
    # Standard logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s : %(message)s",
        datefmt='%d/%m/%y %I:%M:%S %p %A'
    )
    fileHandler.setFormatter(formatter)
    
    # Avoid duplicate handlers being added to the logger
    if not logger.handlers:
        logger.addHandler(fileHandler)
        
    return logger
