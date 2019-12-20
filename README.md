# ⚠️ Deprecation warning ⚠️
The current API of FMFriends will be deprecated within the coming weeks/months to make place for a completely new version/service.
You may clone this repo now and do with it whatever the license permits, even after its deprecation.
The current FMFriends codebase will not be available after the new major version is released, which may be provided under a different license.

## Features coming up
- Working session reuse (Log in once, use as often as you like)
- Better 2FA mechanism (not using stdin)
- Cleaner API
- Better Database Integration with MongoDB or any other Database
- Easier use of multiple accounts
- More reliable and efficient code (strongly typed)
- Super extensive docs
- Easy and intuitive data visualisation



# FMFriends

FMFriends is an API for icloud.com that enables easy Find-My-Friends location quarries with contact names or ids and is powered by the fantastic [requests] library. It saves all locations in a database by default for later use.

## Authentication

At the moment this API only works with iCloud accounts that have **2FA enabled**, the 2FA code must be supplied at runtime. FMFriends will reuse an older authentication if possible, therefore you don't need to 2FAuthenticate every time.

Authentication works as follows and returns an FMF object that holds the functionality of this API.

```py
api = fmfriends.FMF('email', 'password')
```

&nbsp;
If the session is still valid can be tested by getting back a Boolean from the following function:

```py
api.test_auth()
```

&nbsp;
You can also re-authenticate using the credentials used when creating the API with:

```py
api.authenticate()
```

## Usage

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

These will return a list and a dictionary with Names/IDs respectively.

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

This will return a raw JSON response from the FMF refresh action call.

## Installation

```py
pip install fmfriends
```

And then import with:

```py
import fmfriends
```

## License

MIT

[requests]: https://github.com/requests/requests
