
import datetime
import logging
from pathlib import Path
from typing import List, Dict, Union, Optional
import sys

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.profile_type import FileType, Manufacturer

# Ensure we can import from the parent package
sys.path.insert(0, str(Path(__file__).parent.parent))
from garmin.weight_scale_message import WeightScaleMessage
_LOGGER = logging.getLogger(__name__)

def create_weight_fit_file(
    weights: List[Dict],
    output_filename: Union[str, Path] = "weights.fit",
    filter_config: Optional[Dict] = None
):
    """
    Creates a FIT file containing the provided weight data.

    Args:
        weights: A list of dicts containing weight data. Expected keys:
                 - 'Date' (datetime or str) or 'Timestamp' (float/int)
                 - 'Weight' (kg)
                 - 'BMI'
                 - 'BodyFat' (%)
                 - 'BodyWater' (%)
                 - 'BoneMass' (kg)
                 - 'MetabolicAge' (years)
                 - 'MuscleMass' (kg)
                 - 'VisceralFat' (rating)
                 - 'BasalMetabolism' (kcal)
        output_filename: The name of the output FIT file.
        filter_config: Optional filter configuration for filtering weight data.
    """
    # Apply filter if configured
    if filter_config is not None:
        from garmin.filter_config import FilterConfigValidator
        from garmin.filter import apply_filter

        try:
            # Validate filter configuration
            FilterConfigValidator.validate(filter_config)

            # Apply filter
            original_count = len(weights)
            weights = apply_filter(weights, filter_config)

            if len(weights) < original_count:
                filtered_out = original_count - len(weights)
                _LOGGER.info(
                    f"Filter reduced records from {original_count} to {len(weights)} "
                    f"({filtered_out} filtered out)"
                )

        except Exception as e:
            _LOGGER.error(f"Filter error: {e}. Continuing without filter.")
            _LOGGER.info("Please check your filter configuration in users.json")
            # Continue with original data on error

    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    # 1. File ID Message
    file_id_mesg = FileIdMessage()
    file_id_mesg.type = FileType.WEIGHT
    file_id_mesg.manufacturer = Manufacturer.GARMIN
    file_id_mesg.product = 2429  # Index Scale
    file_id_mesg.serial_number = 12345
    file_id_mesg.time_created = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    builder.add(file_id_mesg)

    # 2. Add Weight Scale Messages
    added_count = 0
    for w in weights:
        mesg = WeightScaleMessage()
        
        # Handle Timestamp
        ts = None
        if 'Timestamp' in w:
            ts = float(w['Timestamp'])
        elif 'Date' in w:
            dt = w['Date']
            if isinstance(dt, str):
                try:
                    # Try common Xiaomi format: 2026-01-01 08:53:22
                    dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                except ValueError:
                    continue
            if isinstance(dt, datetime.datetime):
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                ts = dt.timestamp()
        
        if ts is None:
            continue
            
        # fit-tool expects milliseconds for timestamp field in some contexts, 
        # but let's see. Library usage in generate_fit_file.py used *1000.
        mesg.timestamp = int(ts * 1000)
        
        # Mappings from Xiaomi data structure to FIT WeightScaleMessage fields
        if w.get('Weight'):
            mesg.weight = float(w['Weight'])
            
        if w.get('BMI'):
            mesg.bmi = float(w['BMI'])
            
        if w.get('BodyFat'):
            mesg.percent_fat = float(w['BodyFat'])
            
        if w.get('BodyWater'):
            mesg.percent_hydration = float(w['BodyWater'])
            
        if w.get('BoneMass'):
            mesg.bone_mass = float(w['BoneMass'])
        
        if w.get('MetabolicAge'):
            mesg.metabolic_age = int(w['MetabolicAge'])

        if w.get('MuscleMass'):
            mesg.muscle_mass = float(w['MuscleMass'])
            
        if w.get('VisceralFat'):
            mesg.visceral_fat_rating = int(w['VisceralFat'])
            
        if w.get('BasalMetabolism'):
            mesg.basal_met = float(w['BasalMetabolism'])
        
        builder.add(mesg)
        added_count += 1

    if added_count == 0:
        _LOGGER.warning("No weight data points were added to the FIT file.")
        return None

    fit_file = builder.build()
    
    # Ensure directory exists
    output_path = Path(output_filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fit_file.to_file(str(output_path))
    _LOGGER.info(f"Generated FIT file with {added_count} records: {output_path}")
    return output_path


