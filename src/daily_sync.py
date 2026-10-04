import time
import subprocess
import datetime
import argparse
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_sync(config_path, sync_flag):
    """运行同步命令"""
    cmd = ["python", "src/main.py", "--config", config_path]
    if sync_flag:
        cmd.append("--sync")
    try:
        logger.info(f"Starting sync with config: {config_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        logger.info(f"Sync completed at {datetime.datetime.now()}")
        if result.stdout:
            logger.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.warning(f"STDERR: {result.stderr}")
        if result.returncode == 0:
            logger.info("Sync successful")
        else:
            logger.error(f"Sync failed with return code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running sync: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Daily Sync Runner")
    parser.add_argument("--config", default="config/users.json",
                        help="Path to users.json config file")
    parser.add_argument("--sync", action="store_true",
                        help="Enable sync to Garmin")
    parser.add_argument("--delay", type=int, default=300,
                        help="Delay in seconds before first sync (default: 300)")
    parser.add_argument("--interval", type=int, default=86400,
                        help="Interval in seconds between syncs (default: 86400 = 24 hours)")
    args = parser.parse_args()

    logger.info(f"Daily Sync Runner started with config: {args.config}")
    logger.info(f"Initial delay: {args.delay}s, Sync interval: {args.interval}s")
    logger.info(f"Sync to Garmin: {'enabled' if args.sync else 'disabled'}")
    
    # 延迟启动（防止容器重启时立即运行）
    logger.info(f"Delaying start for {args.delay} seconds...")
    time.sleep(args.delay)

    while True:
        try:
            success = run_sync(args.config, args.sync)
            if success:
                next_sync = datetime.datetime.now() + datetime.timedelta(seconds=args.interval)
                logger.info(f"Next sync scheduled for {next_sync}")
            else:
                logger.warning("Sync failed, retrying in 1 hour...")
                time.sleep(3600)  # 如果失败，1小时后重试
                continue
            time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Daily Sync Runner stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            logger.info("Retrying in 1 hour...")
            time.sleep(3600)

if __name__ == "__main__":
    main()