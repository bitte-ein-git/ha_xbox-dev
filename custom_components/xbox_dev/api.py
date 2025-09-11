# api.py

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class XboxOneDevmodeApi:
    """Wrapper for the Xbox One Dev Mode API."""
    PORT = 11443

    def __init__(self, ip_addr, username, password):
        self.ip_addr = ip_addr
        self.base_url = f"https://{self.ip_addr}:{self.PORT}"
        self.session = requests.session()
        self.session.verify = False
        self.session.auth = (username, password)

    def _get_csrf_token(self):
        """Get a fresh CSRF token."""
        self.session.cookies.clear()
        try:
            self.session.get(f"{self.base_url}/", timeout=5)
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get CSRF token: {e}") from e
        
        token = self.session.cookies.get('CSRF-Token')
        if not token:
            raise ConnectionError("CSRF-Token not found in cookies")
        return token

    def _get(self, endpoint, *args, **kwargs):
        return self.session.get(f"{self.base_url}{endpoint}", *args, **kwargs)

    def _post(self, endpoint, *args, **kwargs):
        token = self._get_csrf_token()
        headers = {'X-CSRF-Token': token}
        return self.session.post(f"{self.base_url}{endpoint}", headers=headers, *args, **kwargs)

    def _put(self, endpoint, *args, **kwargs):
        token = self._get_csrf_token()
        headers = {'X-CSRF-Token': token}
        return self.session.put(f"{self.base_url}{endpoint}", headers=headers, *args, **kwargs)

    def _delete(self, endpoint, *args, **kwargs):
        token = self._get_csrf_token()
        headers = {'X-CSRF-Token': token}
        return self.session.delete(f"{self.base_url}{endpoint}", headers=headers, *args, **kwargs)

    def test_connection(self):
        """Test the connection and authentication."""
        response = self._get('/', timeout=5)
        response.raise_for_status()
        return True

    def reboot(self):
        """Reboot the console."""
        return self._post('/api/control/restart')

    def shutdown(self):
        """Shutdown the console."""
        return self._post('/api/control/shutdown')

    def disconnect_controllers(self):
        """Disconnect all controllers."""
        return self._delete('/ext/remoteinput/controllers')

    def get_machinename(self):
        """Get the machine name."""
        return self._get('/api/os/machinename').json().get('ComputerName')

    def _get_info(self):
        """Get general device info."""
        return self._get('/ext/xbox/info').json()

    def get_deviceid(self):
        """Get the device ID."""
        return self._get_info().get('DeviceId')

    def get_serialnumber(self):
        """Get the serial number."""
        return self._get_info().get('SerialNumber')

    def get_language(self):
        """Get the OS language."""
        return self._get('/api/os/info').json().get('Language')

    def get_connectedcontrollercount(self):
        """Get the number of connected controllers."""
        return self._get('/ext/remoteinput/controllers').json().get('ConnectedControllerCount')

    def get_processes(self):
        """Get the list of running processes."""
        return self._get('/api/resourcemanager/processes').json().get('Processes', [])

    def get_system_performance(self):
        """Get system performance data."""
        return self._get('/api/resourcemanager/systemperf').json()

    def get_screenshot(self):
        """Get a screenshot from the console."""
        response = self._get('/ext/screenshot', stream=True)
        response.raise_for_status()
        return response.content