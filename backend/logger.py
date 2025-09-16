import logging
from logging.handlers import TimedRotatingFileHandler
import os
import glob
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Save log file with date in the name
LOG_FILE = os.path.join(LOG_DIR, f'app_{datetime.now().strftime("%Y-%m-%d")}.log')

logger = logging.getLogger('EcoVisionLogger')
logger.setLevel(logging.INFO)

handler = TimedRotatingFileHandler(LOG_FILE, when='midnight', backupCount=7)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def cleanup_old_logs():
    log_files = sorted(glob.glob(os.path.join(LOG_DIR, 'app_*.log*')))
    if len(log_files) > 7:
        for old_file in log_files[:-7]:
            try:
                os.remove(old_file)
            except Exception as e:
                logger.error(f"Failed to remove old log file {old_file}: {e}")