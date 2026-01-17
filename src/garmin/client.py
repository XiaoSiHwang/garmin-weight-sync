
import logging
import os
import sys
import json
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Union
import requests

from garth.http import Client

# Ensure we can import from the parent package
sys.path.insert(0, str(Path(__file__).parent.parent))
from garmin.url_dict import GARMIN_URL_DICT

logger = logging.getLogger(__name__)

class ActivityUploadFormat(Enum):
    FIT = auto()
    GPX = auto()
    TCX = auto()

class GarminClient:
    def __init__(self, email, password, auth_domain="CN", session_dir="data/.garth"):
        self.email = email
        self.password = password
        self.auth_domain = auth_domain
        self.session_dir = Path(session_dir) / email  # Segregate sessions by email
        # Create independent Client instance to avoid conflicts with global garth singleton
        self._client = Client()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "origin": GARMIN_URL_DICT.get("SSO_URL_ORIGIN", "https://sso.garmin.com"),
            "nk": "NT"
        }

    def login(self):
        """Log in to Garmin Connect and handle session persistence"""
        return self._login_impl(lambda: input("Enter Garmin MFA code: "))

    def login_for_ui(self, mfa_callback):
        """
        Log in to Garmin Connect with MFA callback for UI integration.

        Args:
            mfa_callback: A callable that returns the MFA code when invoked.
                         This allows the UI to prompt the user for input.

        Returns:
            bool: True if login successful, False otherwise.
        """
        return self._login_impl(mfa_callback)

    def _login_impl(self, mfa_provider):
        """
        Internal login implementation with configurable MFA provider.

        Args:
            mfa_provider: A callable that returns the MFA code when invoked.

        Returns:
            bool: True if login successful, False otherwise.
        """
        try:
            # Try to resume from saved session
            if self.session_dir.exists() and any(self.session_dir.iterdir()):
                logger.info(f"Attempting to resume Garmin session for {self.email} from {self.session_dir}")
                try:
                    self._client.load(str(self.session_dir))
                    # Check if session is still valid by accessing username
                    username = self._client.username
                    logger.info(f"Garmin session resumed successfully for user: {username}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to resume session: {e}. Performing fresh login.")

            # Perform fresh login
            logger.info(f"Logging in to Garmin for {self.email}...")
            domain = "garmin.cn" if self.auth_domain and self.auth_domain.upper() == "CN" else "garmin.com"
            self._client.configure(domain=domain)

            logger.info(f"[DEBUG] 开始调用 garth login, mfa_provider={mfa_provider}")
            self._client.login(self.email, self.password, prompt_mfa=mfa_provider)
            logger.info(f"[DEBUG] garth login 调用完成")

            # Save session
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self._client.dump(str(self.session_dir))
            logger.info(f"Garmin session saved to {self.session_dir}")

            # Clean up headers as required by some Garmin versions
            if 'User-Agent' in self._client.sess.headers:
                del self._client.sess.headers['User-Agent']

            return True
        except Exception as e:
            logger.error(f"Garmin login failed for {self.email}: {e}")
            return False

    def upload_fit(self, fit_path: Union[str, Path]):
        """Upload FIT file to Garmin Connect."""
        fit_path = Path(fit_path)
        if not fit_path.exists():
            logger.error(f"FIT file not found: {fit_path}")
            return "FILE_NOT_FOUND"

        file_base_name = fit_path.name
        file_extension = fit_path.suffix[1:].upper()
        
        if file_extension not in ActivityUploadFormat.__members__:
            logger.error(f"Unsupported file format: {file_extension}")
            return "UNSUPPORTED_FORMAT"

        try:
            logger.info(f"Uploading {file_base_name} to Garmin Connect...")
            with open(fit_path, 'rb') as f:
                file_data = f.read()
            
            fields = {
                'file': (file_base_name, file_data, 'application/octet-stream')
            }

            url_path = GARMIN_URL_DICT["garmin_connect_upload"]
            upload_url = f"https://connectapi.{self._client.domain}{url_path}"

            # Update headers with dynamic tokens from client
            headers = self.headers.copy()
            headers['Authorization'] = str(self._client.oauth2_token)
            
            # Using requests for the upload part as in the original code
            response = requests.post(upload_url, headers=headers, files=fields)
            
            if response.status_code == 202 or response.status_code == 201 :
                logger.info(f"Successfully uploaded {file_base_name}")
                return "SUCCESS"
            elif response.status_code == 409:
                logger.warning(f"Duplicate file detected on Garmin Connect: {file_base_name}")
                return "DUPLICATE"
            else:
                logger.error(f"Upload failed with status {response.status_code}: {response.text}")
                return f"ERROR_{response.status_code}"
                
        except Exception as e:
            logger.error(f"Error during FIT upload: {e}")
            return "UPLOAD_EXCEPTION"
