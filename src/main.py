
from garmin.client import GarminClient
from garmin.fit_generator import create_weight_fit_file
from xiaomi.client import XiaomiClient, unmarshal_fitness_data
from xiaomi.config import ConfigManager
import argparse
import sys
import logging
import json
import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))


# Configure logging - force reconfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)


def display_weight_data(weights, limit=10):
    """Display weight data in a formatted way"""
    if not weights:
        print("No weight data found.")
        return

    print(f"\n{'='*80}")
    print(f"📊 Weight Data Summary - Total Records: {len(weights)}")
    print(f"{'='*80}\n")

    # Show latest records
    display_count = min(limit, len(weights))
    print(f"Showing latest {display_count} records:\n")

    for i, w in enumerate(weights[:display_count], 1):
        print(f"Record #{i} - {w.get('Date', 'N/A')}")
        print(f"  Weight: {w.get('Weight', 'N/A')} kg")
        print(f"  BMI: {w.get('BMI', 'N/A')}")

        if w.get('BodyFat'):
            print(f"  Body Fat: {w.get('BodyFat')}%")
        if w.get('BodyWater'):
            print(f"  Body Water: {w.get('BodyWater')}%")
        if w.get('MuscleMass'):
            print(f"  Muscle Mass: {w.get('MuscleMass')} kg")
        if w.get('BoneMass'):
            print(f"  Bone Mass: {w.get('BoneMass')} kg")
        if w.get('VisceralFat'):
            print(f"  Visceral Fat: {w.get('VisceralFat')}")
        if w.get('BasalMetabolism'):
            print(f"  Basal Metabolism: {w.get('BasalMetabolism')} kcal")
        if w.get('MetabolicAge'):
            print(f"  Metabolic Age: {w.get('MetabolicAge')} years")
        if w.get('BodyScore'):
            print(f"  Body Score: {w.get('BodyScore')}")
        if w.get('HeartRate'):
            print(f"  Heart Rate: {w.get('HeartRate')} bpm")

        print()

    # Statistics
    if len(weights) > 0:
        weights_values = [float(w.get('Weight'))
                          for w in weights if w.get('Weight')]
        if weights_values:
            print(f"{'='*80}")
            print(f"📈 Statistics")
            print(f"{'='*80}")
            print(f"  Latest Weight: {weights_values[0]} kg")
            print(
                f"  Average Weight: {sum(weights_values) / len(weights_values):.2f} kg")
            print(f"  Min Weight: {min(weights_values)} kg")
            print(f"  Max Weight: {max(weights_values)} kg")
            print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Xiaomi Weight Sync")
    parser.add_argument("--config", default="users.json",
                        help="Path to users.json config file")
    parser.add_argument("--limit", type=int, default=10,
                        help="Number of records to display")
    parser.add_argument("--fit", action="store_true",
                        help="Generate FIT files for Garmin")
    parser.add_argument("--sync", action="store_true",
                        help="Upload weight data to Garmin Connect")
    parser.add_argument("--output-dir", default="data/garmin-fit",
                        help="Directory for generated FIT files")
    args = parser.parse_args()

    # If --sync is requested, we must also have --fit
    if args.sync:
        args.fit = True

    config_mgr = ConfigManager(args.config)
    users = config_mgr.get_users()

    if not users:
        logger.warning(
            f"No users found in {args.config}. Please add users to the configuration file.")

        # Create a template if it doesn't exist/empty
        if not users:
            template = {
                "users": [
                    {
                        "username": "your_xiaomi_username",
                        "password": "your_xiaomi_password",
                        "model": "yunmai.scales.ms103",
                        "token": {
                            "userId": "",
                            "passToken": "",
                            "ssecurity": ""
                        },
                        "garmin": {
                            "email": "your_garmin_email",
                            "password": "your_garmin_password",
                            "domain": "CN"
                        }
                    }
                ]
            }
            with open(args.config, 'w') as f:
                json.dump(template, f, indent=4)
            logger.info(f"Created template {args.config}")
            return

    for user in users:
        username = user.get("username")
        token = user.get("token")
        model = user.get("model", "yunmai.scales.ms103")
        garmin_config = user.get("garmin")

        if not username:
            continue

        logger.info(f"Processing user: {username}")

        client = XiaomiClient(username=username)

        if token and token.get("userId") and token.get("passToken"):
            # Set credentials from token
            client.set_credentials(
                user_id=token["userId"],
                ssecurity_encoded=token.get("ssecurity"),
                pass_token=token["passToken"]
            )

            try:
                # Validate/refresh token
                logger.info("Logging in with saved Xiaomi token...")
                new_token_data = client.login_from_token()

                # Update the token in config if changed
                if new_token_data:
                    config_mgr.update_user_token(username, new_token_data)
                    logger.info("Xiaomi token refreshed and saved")

                # Fetch weights - prefer using the new API (supports imported data from zeeplife)
                weights = []

                # First attempt to use the new API endpoint
                logger.info("Trying to fetch weight data using the new API...")
                try:
                    weights = client.get_model_weights(model)
                    logger.info(
                        f"Parsed and obtained {len(weights)} weight records")
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch data with the new API: {e}")
                    logger.info("Falling back to legacy API...")

                # If no data from the new API, use the legacy API (for backward compatibility)
                if not weights:
                    fitness_data = client.get_fitness_data_by_time(
                        key="weight")
                    logger.info(f"Using legacy API, model: {model}")
                    # weights = client.get_model_weights(model)
                    weights = unmarshal_fitness_data(fitness_data)
                if weights:
                    logger.info(
                        f"Successfully retrieved {len(weights)} weight records")
                    display_weight_data(weights, limit=args.limit)

                    # Save to JSON file
                    output_file = f"data/weight_data_{username}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(weights, f, indent=2, ensure_ascii=False)
                    logger.info(f"Weight data saved to {output_file}")

                    # Generate FIT file if requested
                    if args.fit:
                        # Extract and validate filter configuration
                        filter_config = None
                        if garmin_config:
                            filter_config = garmin_config.get("filter")

                            # If filter is configured, validate and log
                            if filter_config and filter_config.get("enabled"):
                                try:
                                    from garmin.filter_config import FilterConfigValidator
                                    FilterConfigValidator.validate(
                                        filter_config)

                                    conditions_count = len(
                                        filter_config.get("conditions", []))
                                    logic = filter_config.get("logic", "and")
                                    logger.info(
                                        f"Weight filter enabled: {conditions_count} condition(s) "
                                        f"with '{logic.upper()}' logic"
                                    )
                                except Exception as e:
                                    logger.error(
                                        f"Invalid filter configuration: {e}")
                                    logger.warning("Proceeding without filter")
                                    filter_config = None

                        # Chunked upload logic
                        CHUNK_SIZE = 500
                        fit_output_dir = Path(args.output_dir)
                        fit_output_dir.mkdir(parents=True, exist_ok=True)
                        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

                        # Split weights into chunks
                        weight_chunks = [weights[i:i+CHUNK_SIZE]
                                        for i in range(0, len(weights), CHUNK_SIZE)]
                        total_chunks = len(weight_chunks)

                        logger.info(
                            f"体重数据共 {len(weights)} 条，将分为 {total_chunks} 个批次处理")

                        # Initialize upload results tracking
                        upload_results = {
                            'success': 0,
                            'failed': 0,
                            'duplicate': 0,
                            'failed_chunks': []
                        }

                        # Process each chunk
                        for idx, chunk in enumerate(weight_chunks, 1):
                            # Generate filename with chunk number
                            chunk_filename = fit_output_dir / \
                                f"weight_{username}_{timestamp}_{idx}.fit"

                            logger.info(
                                f"处理第 {idx}/{total_chunks} 批: {len(chunk)} 条数据")

                            # Generate FIT file for this chunk
                            created_path = create_weight_fit_file(
                                chunk, chunk_filename, filter_config=filter_config
                            )

                            if created_path is None:
                                logger.warning(
                                    f"批次 {idx}/{total_chunks} 没有生成有效数据，跳过")
                                continue

                            # Sync to Garmin if requested
                            if args.sync:
                                # Initialize Garmin client on first sync
                                if 'g_client' not in locals():
                                    if garmin_config and garmin_config.get("email") and garmin_config.get("password"):
                                        g_client = GarminClient(
                                            email=garmin_config["email"],
                                            password=garmin_config["password"],
                                            auth_domain=garmin_config.get(
                                                "domain", "CN")
                                        )

                                        if not g_client.login():
                                            logger.error(
                                                "❌ Garmin login failed. Synchronization aborted.")
                                            g_client = None
                                    else:
                                        logger.warning(
                                            f"⚠️ Garmin credentials missing for {username}. Skipping sync.")
                                        g_client = None

                                # Upload if client is available
                                if g_client:
                                    logger.info(
                                        f"正在上传批次 {idx}/{total_chunks} 到 Garmin Connect...")
                                    status = g_client.upload_fit(
                                        chunk_filename)

                                    if status == "SUCCESS":
                                        logger.info(
                                            f"✅ 批次 {idx}/{total_chunks} 上传成功")
                                        upload_results['success'] += 1
                                    elif status == "DUPLICATE":
                                        logger.info(
                                            f"ℹ️ 批次 {idx}/{total_chunks} 数据已存在（重复）")
                                        upload_results['duplicate'] += 1
                                    else:
                                        logger.error(
                                            f"❌ 批次 {idx}/{total_chunks} 上传失败: {status}")
                                        upload_results['failed'] += 1
                                        upload_results['failed_chunks'].append({
                                            'chunk': idx,
                                            'filename': str(chunk_filename),
                                            'error': status,
                                            'records': len(chunk)
                                        })

                        # Print upload summary
                        if args.sync and total_chunks > 0:
                            logger.info("=" * 80)
                            logger.info(f"📊 上传汇总 - {username}")
                            logger.info(f"  总批次数: {total_chunks}")
                            logger.info(
                                f"  ✅ 成功: {upload_results['success']}")
                            logger.info(
                                f"  ℹ️ 重复: {upload_results['duplicate']}")
                            logger.info(
                                f"  ❌ 失败: {upload_results['failed']}")

                            if upload_results['failed_chunks']:
                                logger.info("\n失败的批次详情:")
                                for fail in upload_results['failed_chunks']:
                                    logger.info(
                                        f"  - 批次 {fail['chunk']}: {fail['filename']} "
                                        f"({fail['records']} 条记录) - 错误: {fail['error']}"
                                    )
                            logger.info("=" * 80)
                else:
                    logger.warning("No weight data found")

            except Exception as e:
                logger.error(f"Failed to process data for {username}: {e}")
                logger.exception("Detailed error:")
        else:
            logger.warning(
                f"No valid token for {username}. Please run the login tool to generate a token.")
            logger.info("Run: python src/xiaomi/login.py --config users.json")


if __name__ == "__main__":
    main()
