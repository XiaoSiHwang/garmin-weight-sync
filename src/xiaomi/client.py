
import requests
import time
import hashlib
import base64
import json
import os
import struct
import logging
import email.utils

# Try to import curlify for debugging, but don't fail if missing
try:
    import curlify
except ImportError:
    curlify = None

_LOGGER = logging.getLogger(__name__)

# Constants
APP_ID = "miothealth"
USER_AGENT = "MisFit/2.0.0 (iPhone; iOS 13.0; Scale/2.0.0)"

def parse_any_float(v):
    if v is None:
        return 0.0
    if isinstance(v, (float, int)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except:
            return 0.0
    return 0.0

def parse_any_int(v):
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        try:
            return int(float(v))
        except:
            return 0
    return 0

def unmarshal_scale_data(items):
    weights = []
    last_create_time = 0
    
    for v1 in items:
        from_source = v1.get("fromSource")
        create_time = v1.get("createTime", 0)
        last_create_time = create_time
        raw_data_str = v1.get("data")
        
        try:
            v2 = json.loads(raw_data_str)
        except:
            continue
            
        w = {}
        # Convert ms timestamp to readable string
        w['Date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(create_time / 1000))
        w['Timestamp'] = create_time / 1000
        w['Source'] = from_source
        
        if from_source == 1:
            w['Weight'] = v2.get("weight")
            w['BMI'] = v2.get("bmi")
            w['BodyFat'] = v2.get("bfp") 
            w['BodyWater'] = v2.get("bwp") 
            w['BoneMass'] = v2.get("bmc")
            w['MetabolicAge'] = v2.get("ma")
            w['MuscleMass'] = v2.get("smm")
            w['VisceralFat'] = v2.get("vfl")
            w['BasalMetabolism'] = v2.get("bmr")
            w['BodyScore'] = v2.get("sbc")
            
        elif from_source == 2:
            w['Weight'] = parse_any_float(v2.get("weight"))
            w['BMI'] = parse_any_float(v2.get("bmi"))
            w['BodyFat'] = parse_any_float(v2.get("bfp"))
            w['BodyWater'] = parse_any_float(v2.get("bwp"))
            w['BoneMass'] = parse_any_float(v2.get("bmc"))
            w['MetabolicAge'] = parse_any_int(v2.get("ma"))
            w['MuscleMass'] = parse_any_float(v2.get("smm"))
            w['VisceralFat'] = parse_any_int(v2.get("vfl"))
            w['BasalMetabolism'] = parse_any_int(v2.get("bmr"))
            w['BodyScore'] = parse_any_int(v2.get("sbc"))
            
        elif from_source == 3:
            w['Weight'] = parse_any_float(v2.get("weight"))
            w['BMI'] = parse_any_float(v2.get("bmi"))
            w['HeartRate'] = v2.get("heartRate")
            
            body_res_data = v2.get("bodyResData")
            if body_res_data:
                try:
                    v3 = json.loads(body_res_data)
                    w['BodyFat'] = parse_any_float(v3.get("bfp"))
                    w['BodyWater'] = parse_any_float(v3.get("bwp"))
                    w['BoneMass'] = parse_any_float(v3.get("bmc"))
                    w['MetabolicAge'] = parse_any_int(v3.get("ma"))
                    w['MuscleMass'] = parse_any_float(v3.get("smm"))
                    w['VisceralFat'] = parse_any_int(v3.get("vfl"))
                    w['BasalMetabolism'] = parse_any_int(v3.get("bmr"))
                    w['BodyScore'] = parse_any_int(v3.get("sbc"))
                except:
                    pass
        
        weights.append(w)

    return weights, last_create_time

class XiaomiClient:
    def __init__(self, username=None, password=None, region="cn"):
        self.username = username
        self.password = password
        self.region = region
        self.sid = APP_ID
        self.session = requests.Session()
        # self.session.headers.update({"User-Agent": USER_AGENT})
        
        # Credentials
        self.user_id = None
        self.ssecurity = None
        self.pass_token = None
        
        self.cookies = {}
        self.time_offset = 0

    def set_credentials(self, user_id, ssecurity_encoded, pass_token):
        self.user_id = user_id
        # ssecurity is usually base64 encoded string when stored
        if isinstance(ssecurity_encoded, str):
            self.ssecurity = base64.b64decode(ssecurity_encoded)
        else:
            self.ssecurity = ssecurity_encoded
        self.pass_token = pass_token

    def _gen_nonce(self):
        rand_bytes = os.urandom(8)
        now = time.time() + self.time_offset
        ts = int(now / 60)
        ts_bytes = struct.pack(">I", ts)
        return rand_bytes + ts_bytes

    def _gen_signed_nonce(self, ssecurity, nonce):
        m = hashlib.sha256()
        m.update(ssecurity)
        m.update(nonce)
        return m.digest()

    def _rc4_encrypt(self, key, data):
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
        
        i = j = 0
        for _ in range(1024):
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            
        out = []
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        for char in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            out.append(char ^ S[(S[i] + S[j]) % 256])
            
        return bytes(out)

    def login_from_token(self):
        """
        Validates the token and sets up the session.
        Needs user_id, pass_token to be set.
        """
        if not self.user_id or not self.pass_token:
             raise Exception("Missing credentials for token login")
             
        _LOGGER.info("Attempting login with token...")
        headers = {
            "Cookie": f"userId={self.user_id}; passToken={self.pass_token}",
            "User-Agent": USER_AGENT
        }
        
        url = f"https://account.xiaomi.com/pass/serviceLogin?_json=true&sid={self.sid}"
        resp = self.session.get(url, headers=headers)
        
        try:
            txt = resp.text
            if txt.startswith("&&&START&&&"):
                txt = txt[11:]
            data = json.loads(txt)
        except Exception as e:
            raise Exception(f"Failed to parse login response: {resp.text}") from e
        
        if data.get("code") != 0:
             raise Exception(f"Login with token failed: {data}")
             
        # Update credentials
        if "ssecurity" in data:
            self.ssecurity = base64.b64decode(data["ssecurity"])
        if "userId" in data:
            self.user_id = data["userId"]
        if "passToken" in data:
            self.pass_token = data["passToken"]
            
        auth_location = data.get("location")
        if auth_location:
            resp2 = self.session.get(auth_location)
            # Calculate time offset
            server_date = resp2.headers.get("Date")
            if server_date:
                server_ts = email.utils.mktime_tz(email.utils.parsedate_tz(server_date))
                self.time_offset = server_ts - time.time()
                _LOGGER.info(f"Synchronized time with server. Offset: {self.time_offset:.2f}s")
        
        _LOGGER.info("Login with token successful!")
        return {
            "userId": self.user_id,
            "passToken": self.pass_token,
            "ssecurity": base64.b64encode(self.ssecurity).decode('utf-8') if self.ssecurity else None
        }

    def request(self, api_url, params):
        base_url = "https://hlth.io.mi.com" if self.region == "cn" else f"https://{self.region}.hlth.io.mi.com"
        
        nonce = self._gen_nonce()
        signed_nonce = self._gen_signed_nonce(self.ssecurity, nonce)
        
        s_hash = f"POST&{api_url}&data={params}&" + base64.b64encode(signed_nonce).decode('utf-8')
        rc4_hash = base64.b64encode(hashlib.sha1(s_hash.encode('utf-8')).digest()).decode('utf-8')
        
        enc_params = base64.b64encode(self._rc4_encrypt(signed_nonce, params)).decode('utf-8')
        enc_rc4_hash = base64.b64encode(self._rc4_encrypt(signed_nonce, rc4_hash)).decode('utf-8')
        
        s_sig = f"POST&{api_url}&data={enc_params}&rc4_hash__={enc_rc4_hash}&" + base64.b64encode(signed_nonce).decode('utf-8')
        signature = base64.b64encode(hashlib.sha1(s_sig.encode('utf-8')).digest()).decode('utf-8')
        
        final_data = {
            "data": enc_params,
            "rc4_hash__": enc_rc4_hash,
            "signature": signature,
            "_nonce": base64.b64encode(nonce).decode('utf-8')
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        cookies_dict = self.session.cookies.get_dict()
        if cookies_dict:
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
            headers["Cookie"] = cookie_str
        
        resp = self.session.post(base_url + api_url, data=final_data, headers=headers)
        if curlify:
            _LOGGER.debug(curlify.to_curl(resp.request))
        
        if resp.status_code != 200:
            raise Exception(f"Request failed: {resp.status_code} {resp.text}")
            
        try:
            resp_bytes = base64.b64decode(resp.text)
            decrypted = self._rc4_encrypt(signed_nonce, resp_bytes)
            return json.loads(decrypted)
        except Exception:
            # Sometimes it might not be encrypted or just error json
            try:
                return json.loads(resp.text)
            except:
                return resp.text

    def get_model_weights(self, model):
        _LOGGER.info(f"Fetching data for model: {model}...")
        ts = int(time.time() * 1000)
        all_weights = []
        
        while ts > 0:
            inner_params = {
                "param": {"endTime": 1, "beginTime": ts},
                "model": model,
                "uid": int(self.user_id),
                "did": 0
            }
            outer_params = {
                "eco_api": "eco/scale/getData",
                "params": json.dumps(inner_params, separators=(',', ':'))
            }
            req_params = json.dumps(outer_params, separators=(',', ':'))
            
            try:
                data = self.request("/app/v1/eco/api_proxy", req_params)
            except Exception as e:
                _LOGGER.error(f"Request failed: {e}")
                break
                
            if isinstance(data, dict) and data.get("code") != 0:
                _LOGGER.error(f"API Error: {data}")
                break
            
            res_result = data.get("result", {})
            resp_str = res_result.get("resp")
            
            if not resp_str:
                break
                
            try:
                inner_resp = json.loads(resp_str)
            except:
                break
                
            if inner_resp.get("code") != 0:
                _LOGGER.error(f"Inner API Error: {inner_resp}")
                break
                
            items = inner_resp.get("result", [])
            if not items:
                break
            
            weights, last_create_time = unmarshal_scale_data(items)
            all_weights.extend(weights)
            
            if len(items) < 20:
                break
                
            ts = last_create_time
            
        return all_weights
