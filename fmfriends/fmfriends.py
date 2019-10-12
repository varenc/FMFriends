import requests
import uuid
import datetime
from time import time, sleep
from ast import literal_eval

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


class FMFException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class FMF():

    Base = declarative_base()

    class users(Base):
        __tablename__ = "users"

        id = Column('id', Integer, primary_key=True)
        name = Column('name', String, unique=True)
        cid = Column('cid', String, unique=True)

    class saveenv(Base):
        __tablename__ = "saveenv"
        id = Column('id', Integer, primary_key=True)
        cookie = Column('cookie', String)
        dsid = Column('dsid', Integer)
        fmf_base_url = Column('fmf_base_url', String)

    class location(Base):
        __tablename__ = "loaction"

        id = Column('id', Integer, primary_key=True)
        user_id = Column('user_id', Integer, ForeignKey("users.id"))
        time = Column('time', Integer)
        loctime = Column('loctime', Integer)
        lati = Column('lati', String)
        long = Column('long', String)
        year = Column('year', Integer)
        month = Column('month', Integer)
        day = Column('day', Integer)
        hour = Column('hour', Integer)
        minute = Column('minute', Integer)
        found = Column('found', Boolean)

    class devices(Base):
        __tablename__ = "devices"
        id = Column("id", Integer, primary_key=True)
        device_id = Column("device_id", String)
        name = Column("name", String)
        device_class = Column("class", String)

    engine = create_engine('sqlite:///FMFriends.db', pool_recycle=3600)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    haveenv = True
    session = Session()
    if session.query(saveenv).first() is None:
        cookie = saveenv()
        cookie.cookie = None
        session.add(cookie)
        session.commit()
        haveenv = False
    session.close()

    def __init__(self, appleID, password):
        # user credentials
        self.appleID = str(appleID)
        self.password = str(password)

        # authentication
        self.build_id = "83Cre93160c"
        self.client_id = str(uuid.uuid1()).upper()
        self.dsid = None
        self.idmsaEndPoint = "https://idmsa.apple.com"
        self.idmsaAuthEndPoint = "https://idmsa.apple.com/appleauth/auth"
        self.fm_refresh = "https://p36-fmipweb.icloud.com:443/fmipservice/client/web/refreshClient"
        self.appleIdSessionId = None
        self.scnt = None
        self.authToken = None

        # general
        self.cookies = None
        self.fmf_base_url = None
        self.contactNames = {}
        self.contactIds = []
        self.locations = {}
        self.reasonReuse = None

        # sql alchemy and authentications
        self.Base = declarative_base()
        if self.haveenv:
            self.getEnv()
            if not self.test_auth():
                print(
                    "[FMF] Faild to reuse last login, need to login again..." + str(self.reasonReuse))
                self.authenticate()
        else:
            self.authenticate()
        self.requestFMFData()

    # Authentication
    def _populateIdmsaRequestHeadersParameters(self):
        headers = {
            "Origin": self.idmsaEndPoint,
            "Referer": self.idmsaAuthEndPoint + '/',
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 9_3_4 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13G35 Safari/601.1",
            "X-Apple-Widget-Key": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d"
        }

        if self.appleIdSessionId:
            headers["X-Apple-ID-Session-Id"] = self.appleIdSessionId
        if self.scnt:
            headers["scnt"] = self.scnt

        return headers

    def _sendIdmsaCode(self, code):
        json = {"securityCode": {"code": ''}}
        json["securityCode"]["code"] = code
        headers = self._populateIdmsaRequestHeadersParameters()
        headers["Accept"] = "application/json"
        try:
            r = requests.post(self.idmsaAuthEndPoint +
                              "/verify/trusteddevice/securitycode", json=json, headers=headers)
        except Exception as e:
            raise FMFException("[FMF] Network error: " + str(e))
        if r.status_code >= 300:
            raise FMFException(
                "[FMF] Failed to verify code: " + str(r.status_code))
        return r.headers["X-Apple-Session-Token"]

    def _validateAutomaticVerificationCode(self, code):
        self.authToken = self._sendIdmsaCode(str(code))

    def _get_service_url(self, resp, service):
        if resp:
            if service in resp["webservices"].keys():
                if resp["webservices"][service]["status"] == "active":
                    return resp["webservices"][service]["url"]
        raise FMFException(
            "[FMF] Please check that FMF is enabled on your iCloud account.")

    def _get_dsid(self, resp):
        if resp:
            return resp["dsInfo"]["dsid"]
        else:
            raise FMFException(
                "[FMF] Please check that your login information is correct.")

    def test_auth(self):
        headers = {
            "Origin": "https://www.icloud.com",
            "Referer": "https://www.icloud.com"
        }

        data = {
            "clientContext": {
                "productType": "fmfWeb",
                "appVersion": "1.0",
                "contextApp": "com.icloud.web.fmf",
                "userInactivityTimeInMS": 1,
                "tileServer": "Apple"
            }
        }
        fmfURL = "{0}/fmipservice/client/fmfWeb/refreshClient?clientBuildNumber={1}&clientId={2}&dsid={3}"
        fmfURL = fmfURL.format(self.fmf_base_url,
                               self.build_id, self.client_id, self.dsid)
        try:
            r = requests.post(fmfURL, headers=headers,
                              json=data, cookies=self.cookies)
            self.reasonReuse = r.json()
        except Exception as e:
            raise FMFException("[FMF] Network error: " + str(e))
        if 'error' in r.json():
            return False
        return True

    def authenticate(self):
        params = {
            "accountName": self.appleID,
            "password": self.password,
            "rememberMe": True,
            "trustTokens": []
        }

        headers = self._populateIdmsaRequestHeadersParameters()
        headers["Accept"] = "application/json"
        try:
            r = requests.post(self.idmsaAuthEndPoint + "/signin",
                              json=params, headers=headers)
        except Exception as e:
            raise FMFException("[FMF] Network error: " + str(e))

        if r.headers["X-Apple-Session-Token"] and r.headers["X-Apple-Session-Token"] and r.headers["scnt"]:
            self.authToken = r.headers["X-Apple-Session-Token"]
            self.appleIdSessionId = r.headers["X-Apple-ID-Session-Id"]
            self.scnt = r.headers["scnt"]
        else:
            raise FMFException(
                "[FMF] Please check that your login information is correct.")

        self._validateAutomaticVerificationCode(
            input('[FMF] Please input the 2FA code you recieved: '))

        headers = {
            "Origin": "https://www.icloud.com",
            "Referer": "https://www.icloud.com"
        }

        data = {
            "apple_id": self.appleID,
            "password": self.password,
            "extended_login": True,
            "dsWebAuthToken": self.authToken
        }
        auth_url = "https://setup.icloud.com/setup/ws/1/accountLogin?clientBuildNumber={0}&{1}&clientMasteringNumber={2}".format(
            self.build_id, self.client_id, self.build_id)

        try:
            r = requests.post(auth_url, headers=headers,
                              json=data, cookies=self.cookies)
        except Exception as e:
            raise FMFException("[FMF] Network error: " + str(e))
        auth_resp = r.json()
        self.dsid = self._get_dsid(auth_resp)
        self.fmf_base_url = self._get_service_url(auth_resp, "fmf")
        self._saveCookies(r)
        self._auth()

        self.saveEnv()

    def _auth(self):
        headers = {
            "Origin": "https://www.icloud.com",
            "Referer": "https://www.icloud.com"
        }

        data = {
            "apple_id": self.appleID,
            "password": self.password,
            "extended_login": True,
            "dsWebAuthToken": self.authToken
        }
        auth_url = "https://setup.icloud.com/setup/ws/1/accountLogin?clientBuildNumber={0}&{1}&clientMasteringNumber={2}".format(
            self.build_id, self.client_id, self.build_id)

        try:
            r = requests.post(auth_url, headers=headers,
                              json=data, cookies=self.cookies)
        except Exception as e:
            raise FMFException("[FMF] Network error: " + str(e))
        auth_resp = r.json()
        self.dsid = self._get_dsid(auth_resp)
        self.fmf_base_url = self._get_service_url(auth_resp, "fmf")
        self._saveCookies(r)

    # Save login data
    def saveEnv(self):
        session = self.Session()
        obj = session.query(self.saveenv).get(1)
        obj.cookie = str(requests.utils.dict_from_cookiejar(self.cookies))
        obj.dsid = self.dsid
        obj.fmf_base_url = self.fmf_base_url
        session.commit()
        session.close()

    def getEnv(self):
        session = self.Session()
        t = session.query(self.saveenv).first()
        try:
            self.cookies = requests.cookies.cookiejar_from_dict(
                literal_eval(t.cookie))
        except Exception:
            session.close()
            print("[FMF] Faild to reuse last login, need to login again...")
            self.authenticate()
            return
        self.dsid = str(t.dsid)
        self.fmf_base_url = str(t.fmf_base_url)
        session.close()

    def _saveCookies(self, r):
        self.cookies = r.cookies

    # General FMF
    def requestFMFData(self):
        headers = {
            "Origin": "https://www.icloud.com",
            "Referer": "https://www.icloud.com"
        }

        data = {
            "clientContext": {
                "productType": "fmfWeb",
                "appVersion": "1.0",
                "contextApp": "com.icloud.web.fmf",
                "userInactivityTimeInMS": 1,
                "tileServer": "Apple"
            }
        }
        action = "refresh"
        fmfURL = "{0}/fmipservice/client/fmfWeb/{1}Client?clientBuildNumber={2}&clientId={3}&dsid={4}"
        fmfURL = fmfURL.format(self.fmf_base_url, action,
                               self.build_id, self.client_id, self.dsid)
        try:
            r = requests.post(fmfURL, headers=headers,
                              json=data, cookies=self.cookies)
        except Exception as e:
            raise FMFException("[FMF] Network error: " + str(e))
        self._setContacts(r.json())
        return r.json()

    def _contactDatabaseInsert(self):
        session = self.Session()
        for contactName in self.contactNames.keys():
            if session.query(self.users).filter(self.users.name == contactName).first() is None:
                user = self.users()
                user.name = contactName
                user.cid = self.contactNames[contactName]
                session.add(user)
                session.commit()
        session.close()

    def _setContacts(self, data):
        if "contactDetails" in data:
            for contact in data["contactDetails"]:
                name = contact["firstName"] + " " + contact["lastName"]
                self.contactNames[name] = contact["id"]
                self.contactIds.append(contact["id"])
            self._contactDatabaseInsert()

    def _setLocations(self, Id, database):
        data = self.requestFMFData()
        self.locations = {}
        ntime = int(time())
        now = datetime.datetime.now()
        for person in data['locations']:
            if person['id'] in Id:
                if person['location'] is not None:
                    self.locations[person['id']] = {'time': {'ntime': ntime, 'loctime': person['location']['timestamp'], 'year': now.year, 'month': now.month,
                                                             'day': now.day, 'hour': now.hour, 'minute': now.minute}, 'lati': person['location']['latitude'], 'long': person['location']['longitude'], 'found': True}
                else:
                    self.locations[person['id']] = {'time': {'ntime': ntime, 'loctime': 0, 'year': now.year, 'month': now.month,
                                                             'day': now.day, 'hour': now.hour, 'minute': now.minute}, 'lati': 0, 'long': 0, 'found': False}
        if database:
            self._locationDatabaseInsert(Id)

    def _setDevices(self, devices_dict):
        session = self.Session()
        for device in devices_dict:
            # check whether device exists in database
            if session.query(self.devices).filter(self.devices.device_id == device["id"]).first() is None:
                # create new "device" instance
                d = self.devices()
                d.device_id = device["id"]
                d.name = device["name"]
                d.device_class = device["class"]
                session.add(d)
                session.commit()
        session.close()

    def getLocationByID(self, Id, database=True):
        if type(Id) == str:
            Id = [Id]
        for ids in Id:
            if ids not in self.contactIds:
                raise FMFException("[FMF] Id not in friends list: " + str(ids))
        self._setLocations(Id, database)
        return [self.locations[ids] for ids in Id]

    def getLocationByName(self, name, database=True):
        if type(name) == str:
            name = [name]
        for person in name:
            if person not in self.contactNames:
                raise FMFException(
                    "[FMF] Name not in friends list: " + str(person))
        return self.getLocationByID([self.contactNames[person] for person in name], database)

    def _locationDatabaseInsert(self, Ids):
        session = self.Session()
        data = self.locations
        for Id in Ids:
            try:
                person = data[Id]
                loc = self.location()
                loc.user_id = session.query(self.users).filter(
                    self.users.cid == Id).first().id
                loc.time = person['time']['ntime']
                loc.loctime = person['time']['loctime']
                loc.lati = person['lati']
                loc.long = person['long']
                loc.year = person['time']['year']
                loc.month = person['time']['month']
                loc.day = person['time']['day']
                loc.hour = person['time']['hour']
                loc.minute = person['time']['minute']
                loc.found = person['found']
                session.add(loc)
                session.commit()
            except:
                ntime = int(time())
                now = datetime.datetime.now()
                loc = self.location()
                loc.user_id = session.query(self.users).filter(
                    self.users.cid == Id).first().id
                loc.time = time()
                loc.loctime = 0
                loc.lati = 0
                loc.long = 0
                loc.year = now.year
                loc.month = now.month
                loc.day = now.day
                loc.hour = now.hour
                loc.minute = now.minute
                loc.found = False
                session.add(loc)
                session.commit()
                self.locations[Id] = {'time': {'ntime': ntime, 'loctime': 0, 'year': now.year, 'month': now.month,
                                               'day': now.day, 'hour': now.hour, 'minute': now.minute}, 'lati': 0, 'long': 0, 'found': False}
        session.close()

    def getContactsID(self):
        return self.contactIds

    def getContactsName(self):
        return self.contactNames

    # TODO: Add own location to FMFriends.db
    def requestFindPhoneData(self):
        data = {
            'clientContext': {
                'fmly': True,
                'shouldLocate': True,
                'selectedDevice': 'all',
            }
        }
        headers = {
            "Origin": "https://www.icloud.com",
            "Referer": "https://www.icloud.com"
        }
        raw_url = "{0}/?clientBuildNumber={1}&clientId={2}&dsid={3}"
        url = raw_url.format(self.fm_refresh, self.build_id,
                             self.client_id, self.dsid)
        r = requests.post(self.fm_refresh, headers=headers,
                          json=data, cookies=self.cookies)
        return r.json()

     # returns all devices that are discoverable in find my phone

    def get_FindPhone_devices(self):
        findm_data = self.requestFindPhoneData()
        devices = []
        for content in findm_data["content"]:
            d = {
                "id": content["id"],
                "name": content["name"],
                "class": content["deviceClass"]
            }
            devices.append(d)
        self._setDevices(devices)
        return devices

    def get_own_device_location(self, identifier):
        """
        location data of own device
        identifier must be the unique device name as a String f.ex. "John's iPhone"
        """
        findm_data = self.requestFindMyData()
        for device in findm_data["content"]:
            if device["name"] == identifier:
                #! API returns UNIX timestamp with too many digits at the end
                #! This might be random or change in the next decades ;) so pls spend some further attention here
                time_c = str(device["location"]["timeStamp"])[0:10]
                location = {
                    "time": int(time_c),
                    "la": device["location"]["latitude"],
                    "lo": device["location"]["longitude"]
                }
                return location
        return FMFException("Could not find own device named '%s'" % identifier)
