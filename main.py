
from auto_config_save import get_run
from network_report_and_remediator_generator import report_and_remediate
from network_status_collector import collector
from network_remediator import remediate
from time import sleep
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('network.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
while True:

    try:
        logger.info("COLLECTION STARTED")
        collector()
        logger.info("COLLECTING DONE")
        report_and_remediate()
        logger.info("REPORTING DONE")
        get_run()
        logger.info("RUNNING CONFIG COLLECTION DONE")
        remediate()
        logger.info("REMEDIATING DONE")
        sleep(300)
    except Exception as e:
        logger.exception(e)