
import argparse
import sys
import logging
import json
import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from xiaomi.config import ConfigManager
from xiaomi.client import XiaomiClient, unmarshal_fitness_data
from garmin.fit_generator import create_weight_fit_file
from garmin.client import GarminClient

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
        weights_values = [w.get('Weight') for w in weights if w.get('Weight')]
        if weights_values:
            print(f"{'='*80}")
            print(f"📈 Statistics")
            print(f"{'='*80}")
            print(f"  Latest Weight: {weights_values[0]} kg")
            print(f"  Average Weight: {sum(weights_values) / len(weights_values):.2f} kg")
            print(f"  Min Weight: {min(weights_values)} kg")
            print(f"  Max Weight: {max(weights_values)} kg")
            print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Xiaomi Weight Sync")
    parser.add_argument("--config", default="users.json", help="Path to users.json config file")
    parser.add_argument("--limit", type=int, default=10, help="Number of records to display")
    parser.add_argument("--fit", action="store_true", help="Generate FIT files for Garmin")
    parser.add_argument("--sync", action="store_true", help="Upload weight data to Garmin Connect")
    parser.add_argument("--output-dir", default="data/garmin-fit", help="Directory for generated FIT files")
    args = parser.parse_args()

    # If --sync is requested, we must also have --fit
    if args.sync:
        args.fit = True

    config_mgr = ConfigManager(args.config)
    users = config_mgr.get_users()

    if not users:
        logger.warning(f"No users found in {args.config}. Please add users to the configuration file.")
        
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
                    weights =client.get_model_weights(model)
                    logger.info(f"Parsed and obtained {len(weights)} weight records")
                except Exception as e:
                    logger.warning(f"Failed to fetch data with the new API: {e}")
                    logger.info("Falling back to legacy API...")
                
                # If no data from the new API, use the legacy API (for backward compatibility)
                if not weights:
                    fitness_data = client.get_fitness_data_by_time(key="weight")
                    logger.info(f"Using legacy API, model: {model}")
                    # weights = client.get_model_weights(model)
                    weights = unmarshal_fitness_data(fitness_data)
                if weights:
                    logger.info(f"Successfully retrieved {len(weights)} weight records")
                    display_weight_data(weights, limit=args.limit)

                    # Save to JSON file
                    output_file = f"data/weight_data_{username}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(weights, f, indent=2, ensure_ascii=False)
                    logger.info(f"Weight data saved to {output_file}")
                    
                    # Generate FIT file if requested
                    fit_file_path = None
                    if args.fit:
                        # Extract and validate filter configuration
                        filter_config = None
                        if garmin_config:
                            filter_config = garmin_config.get("filter")

                            # If filter is configured, validate and log
                            if filter_config and filter_config.get("enabled"):
                                try:
                                    from garmin.filter_config import FilterConfigValidator
                                    FilterConfigValidator.validate(filter_config)

                                    conditions_count = len(filter_config.get("conditions", []))
                                    logic = filter_config.get("logic", "and")
                                    logger.info(
                                        f"Weight filter enabled: {conditions_count} condition(s) "
                                        f"with '{logic.upper()}' logic"
                                    )
                                except Exception as e:
                                    logger.error(f"Invalid filter configuration: {e}")
                                    logger.warning("Proceeding without filter")
                                    filter_config = None

                        fit_output_dir = Path(args.output_dir)
                        fit_output_dir.mkdir(parents=True, exist_ok=True)
                        fit_file_path = fit_output_dir / f"weight_{username}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.fit"
                        create_weight_fit_file(weights, fit_file_path, filter_config=filter_config)
                    
                    # Sync to Garmin if requested
                    if args.sync and fit_file_path:
                        if garmin_config and garmin_config.get("email") and garmin_config.get("password"):
                            g_client = GarminClient(
                                email=garmin_config["email"],
                                password=garmin_config["password"],
                                auth_domain=garmin_config.get("domain", "CN")
                            )
                            
                            if g_client.login():
                                logger.info("Synchronizing to Garmin Connect...")
                                status = g_client.upload_fit(fit_file_path)
                                if status == "SUCCESS":
                                    logger.info("✅ Successfully synchronized weight data to Garmin Connect!")
                                elif status == "DUPLICATE":
                                    logger.info("ℹ️ Data already exists on Garmin Connect (Duplicate).")
                                else:
                                    logger.error(f"❌ Garmin sync failed: {status}")
                            else:
                                logger.error("❌ Garmin login failed. Synchronization aborted.")
                        else:
                            logger.warning(f"⚠️ Garmin credentials missing for {username}. Skipping sync.")
                else:
                    logger.warning("No weight data found")
                
            except Exception as e:
                logger.error(f"Failed to process data for {username}: {e}")
                logger.exception("Detailed error:")
        else:
             logger.warning(f"No valid token for {username}. Please run the login tool to generate a token.")
             logger.info("Run: python src/xiaomi/login.py --config users.json")


if __name__ == "__main__":
    main()
