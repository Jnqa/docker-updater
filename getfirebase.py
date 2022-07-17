import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import os
from werkzeug.security import generate_password_hash, check_password_hash

class Fire:
    def __init__(self, credential_json, realtime_database_name, FIREBASE_URL):
        self.realtime_database_name = realtime_database_name
        # firebase_admin.initialize_app(credentials.Certificate(credential_json), {
        #     'databaseURL': f'https://{FIREBASE_URL}'
        # })
        firebase_admin.initialize_app(credentials.Certificate(credential_json),
            {'databaseURL': f'{FIREBASE_URL}'})
        self.ref = db.reference(f'{self.realtime_database_name}')
        self.users_ref = self.ref.child('users')
        self.all_users = self.get_users_base()

    def get_users_base(self):
        self.all_users = self.users_ref.get()
        return self.all_users
    
    def get_users_list(self):
        userslist = {}
        for id in self.get_users_base():
            userslist[id["username"]] = id["password"]
        return userslist

    def add_user(self, username, password):
        if not self.get_users_base() or not [True for elem in list(filter(None, self.all_users)) if username in elem.values()]:
            id = len(self.all_users) if self.get_users_base() else 0
            self.users_ref.update({f"{id}": {
                'id': id,
                'username': username,
                'password': generate_password_hash(password)
            }})
            return True
        return False

def Connect():
    try:
        firebaseToken = os.environ['FIREBASE']
        firebaseURL = os.environ['FIREBASE_URL']
        firebaseName = os.environ['FNAME']
    except:
        print("where is my key?")
        from dotenv import load_dotenv
        load_dotenv('secrets/jnqafun.env') # .env in secrets folder
        firebaseToken = os.getenv('FIREBASE')
        firebaseURL = os.getenv('FIREBASE_URL')
        firebaseName = os.environ['FNAME']
    with open('ftoken.pass', 'w', encoding='utf-8') as f:
            f.write(firebaseToken)
    firebank = Fire('ftoken.pass', firebaseName, firebaseURL)
    os.remove('ftoken.pass')
    return firebank

if __name__ == '__main__':
    firebank = Connect()
    if firebank.get_users_base():
        print(f'\x1b[1;32;40m{firebank.get_users_base()}\x1b[0m')