import requests
import logging
from datetime import datetime

logging.basicConfig(
    filename="hemis_errors.log",
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

class HemisAPI:
    def __init__(self):
        self.base_url = "https://student.tsue.uz/rest/v1"
        self.session = requests.Session()

    # ---------------- AUTH ----------------
    def login(self, username, password):
        try:
            print(f"DEBUG: Attempting login for {username}...")
            r = self.session.post(
                f"{self.base_url}/auth/login",
                json={"login": username, "password": password},
                timeout=10
            )
            print(f"DEBUG: Login status code: {r.status_code}")
            print(f"DEBUG: Login response: {r.text[:200]}") # Print first 200 chars

            if r.status_code == 200:
                data = r.json().get("data")
                if not data:
                     print("DEBUG: No 'data' in response!")
                     return {"success": False}
                
                return {
                    "success": True,
                    "access": data["access_token"],
                    "refresh": data["refresh_token"],
                    "student": data.get("student", {})
                }
            return {"success": False, "error": f"HTTP {r.status_code}"}
        except Exception as e:
            logging.error(f"LOGIN ERROR: {e}")
            print(f"DEBUG: Login Exception: {e}")
            return {"success": False, "error": str(e)}

    def refresh(self, refresh_token):
        try:
            r = self.session.post(
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": refresh_token},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()["data"]
                return {
                    "success": True,
                    "access": data["access_token"],
                    "refresh": data["refresh_token"]
                }
            return {"success": False}
        except Exception as e:
            logging.error(f"REFRESH ERROR: {e}")
            return {"success": False}

    # ---------------- SAFE GET ----------------
    def safe_get(self, url, access, refresh):
        headers = {"Authorization": f"Bearer {access}"}
        r = self.session.get(url, headers=headers, timeout=10)

        if r.status_code == 401:
            new = self.refresh(refresh)
            if new["success"]:
                headers["Authorization"] = f"Bearer {new['access']}"
                r = self.session.get(url, headers=headers, timeout=10)
                return r, new
            return None, None

        return r, None

    # ---------------- DATA ----------------
    def student_info(self, access, refresh):
        r, new = self.safe_get(
            f"{self.base_url}/student/student-info",
            access, refresh
        )
        return r.json()["data"] if r else None, new
