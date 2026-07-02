"""
import json
from typing import Dict, List

import requests

from certificate import certificate_to_dict
from models import Certificate

def send_certificates_to_zabbix(
    certificates: List[Certificate],
    trapper_url: str,
    host: str,
    key: str = "cert.data"
) -> bool:

    certs_data = [certificate_to_dict(cert) for cert in certificates]
    json_payload = json.dumps(certs_data, ensure_ascii=False)

    payload = {
        "request": "sender data",
        "data": [
            {
                "host": host,
                "key": key,
                "value": json_payload
            }
        ]
    }
    try:
        resp = requests.post(trapper_url, json=payload, timeout=10)
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json.get("response") == "success":
                print("Данные успешно отправлены через HTTP Trapper.")
                return True
            else:
                print(f"Zabbix вернул ошибку: {resp_json}")
                return False
        else:
            print(f"HTTP ошибка: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"Ошибка при отправке через HTTP Trapper: {e}")
        return False

"""