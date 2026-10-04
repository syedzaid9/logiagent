import requests

BASE = 'http://127.0.0.1:8000'
admin_login = requests.post(f'{BASE}/api/v1/auth/login', json={'email': 'admin@logiagent.io', 'password': 'admin123'})
admin_token = admin_login.json()['access_token']

users = requests.get(f'{BASE}/api/v1/users', headers={'Authorization': f'Bearer {admin_token}'}).json()
rajesh = next(u for u in users if u['email'] == 'rajesh@logiagent.io')

reissue = requests.post(f"{BASE}/api/v1/users/{rajesh['id']}/reissue-invitation", headers={'Authorization': f'Bearer {admin_token}'}).json()
print("==================================================")
print("ACTIVE RAJESH INVITATION DETAILS")
print("==================================================")
print(f"URL (Port 5173): http://localhost:5173{reissue['development_invitation_url']}")
print(f"URL (Port 3000): http://localhost:3000{reissue['development_invitation_url']}")
print(f"Token: {reissue['activation_token']}")
print(f"Expires At: {reissue['activation_expires_at']}")
print("==================================================")
