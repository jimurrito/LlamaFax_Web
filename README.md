![Logo](https://pbs.twimg.com/profile_images/1550147959379021824/EE1vU4LG_400x400.jpg)

# [LlamaFax](https://github.com/jimurrito/LlamaFax) Scale Web UI
Web-Interface used to manually rate the quality of generated sets, provided by the LlamaFax Core Services. Rated sets will be used to train a Machine learning model being built to automate this process.

## Overview
- Provides a platform to manually process data generated by the Llamafax core services.
- A point-system is used to show number of sets rated by a given user.
- Secured with Local Authentication.
- Simple Self-Service Account Management.
- Ticketing System

## Features
#### Main UI
This UI is what is used to rate the generated sets
- Allows for users to see a set of generations, and rate them
- Rating is done by either providing the Index of the good statements or providing 'all' or 'none', to apply the effect to all statements in the set.
- This UI shows the user's UPN, and current score.
- Messages are saved in cache, until submitted
- users can submit bug reports for issues or feedback

#### Leader Board
This element shows the user the current global leader board.
- Users are listed from highest score to lowest
- Crown Emoji is applied to the user in first place
- refresh button allows users to get latest score, without losing the current state of the page.

#### Authentication
This sections goes over how this app handles user authentication.
- Passwords are saved using a password-specific salt, and using SHA256 hashing.
- Plaintext passwords are never saved to persistent store, or logged
- Username or Email can be used in user sign-in

#### Account Self-Service
This feature allows the user to manage the aspects of their own account.
###### Password Reset
- This process requires the user's: UPN, EMAIL, and original PWD.
- if password is lost, a user support ticket can be created to attempt recovery
###### Self Sign up
- user will have to provide an Alpha key to create the account
- user needs to provide: UPN, EMAIL, and PWD to create the account.

#### Ticketing System
This system allows end users to create a trackable object that represents an issue or feedback they have faced.
- Bug Reports can be submitted for feedback or service related issues or bugs
- Support tickets can be made when the account is locked out