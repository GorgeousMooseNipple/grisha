import os
import logging


log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
log_fmt = logging.Formatter("%(module)s:%(lineno)s [%(levelname)s]: %(message)s")

logger = logging.getLogger()
logger.setLevel(log_level)
sh = logging.StreamHandler()
sh.setFormatter(log_fmt)
logger.addHandler(sh)


from utils import CONFIG


def main():
    print("Hello from grisha-uberbringer!")


if __name__ == "__main__":
    main()
