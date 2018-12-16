# FMFriends

[![Build Status](https://travis-ci.org/Coronon/FMFriends.svg?branch=master)](https://travis-ci.org/Coronon/fmfriends)

FMFriends is an API for icloud.com that enables easy Find-My-Friends location quarrys with contact names or ids and is powered by the fantastic [requests] library. It saves all locations in a database by default for later use.

# Authentication

At the moment this API only works with icloud accounts that have **2FA enabled**, the 2FA code must be supplied at runtime. iStalk will reuse an older authentication if possible, therefore you dont need to 2FAuthenticate every time.

Authentication works as follows and returns an FMF object that holds the functionality of this api.

```py
api = FMF('email', 'password')
```

&nbsp;
If the session is still valid can be tested by getting back a Boolean from the following function:

```py
api.test_auth()
```

&nbsp;
You can also reauthenticate using the credentials used when creating the api with:

```py
api.authentictae()
```

# Usage

After getting an FMF object the following functions can be called:

#### Location functions

```py
api.getLocationByID(ContactID, database=True)
api.getLocationByName(ContactName, database=True)
```

Both functions accept either one ID/Name as a string or multiple in a list.
The database option specifies if the result should be saved in the 'FMFriends.db' database for further use.

#### Contact functions

```py
api.getContactsID()
api.getContactsName()
```

These will return a list and a dictionary with Names:IDs respectivley.

#### Enviroment functions

```py
api.saveEnv()
api.getEnv()
```

These will save/load the current login data into/from the database 'FMFriends.db'.

#### Misc

```py
api.requestFMFData()
```

This will return a raw json response from the FMF refresh action call.

# Installation

```py
pip install FMFriends
```

## License

MIT

[requests]: https://github.com/requests/requests
