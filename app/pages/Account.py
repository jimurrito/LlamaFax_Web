from lib.ScalelibWeb import sanitizeInput
from lib.MongoDB import UAuth, MongoDB
import streamlit as st
import logging
import os

# Site State Configuration
st.set_page_config(
    page_title="🦙 Account",
    page_icon="🦙",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

# [Vars from Enviroment]
# DB Host
DBHost = os.getenv("DBHOST", "LFXMongo")
# Build Version #
buildV = os.getenv("BUILDVER", "0.0")

UAuthColNam = "userAuth"
KeyColNam = "alphaKey"
BugRepColNam = "repBugs"
SupportColNam = "support"

# Alpha Key Collection
keyDB = MongoDB(KeyColNam, DBHost, Indexes=["code"])
# Bug Report Collection
BugRepDB = MongoDB(BugRepColNam, DBHost, Indexes="BugID#")
# Support Ticket Collection
SupportDB = MongoDB(SupportColNam, DBHost, Indexes="SrID#")
# Authetication DB
UAuthDB = UAuth(UAuthColNam, Host=DBHost)

# Create Initial Content Objects
PopOut_Signup = st.empty()

# Alpha key Prompt
with PopOut_Signup.container():
    st.title("Signup")
    with st.form("Signup"):
        st.write("Please redeem Alpha Key to sign up.")
        aKey = st.text_input("XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")
        st.form_submit_button("Redeem")


# Alpha key was entered
if aKey:

    # Key was incorrect
    if not keyDB.validate({"code": aKey, "use": {"$exists": "true", "$eq": False}}):
        st.error("Incorrect/Invalid Alpha Key Provided. Please try again.")
        del aKey
    # Key is correct
    else:
        # Clear Initial Popup
        PopOut_Signup.empty()

        # Signup Screen (Primary)
        PopO_Signup2 = st.empty()
        with PopO_Signup2.container():
            st.title("User Creation")
            with st.form("PrimarySignup"):
                Upn = st.text_input("Username", max_chars=40)  # Must be unique
                Email = st.text_input("Email", max_chars=40).lower()  # Must be unique
                st.write(
                    """Password Requirements:
                    \n> 6 - 60 Characters"""
                )
                Pwd = st.text_input("Password", type="password", max_chars=60)
                st.form_submit_button("Next ->")

        # missing input catch
        if Upn or Email or Pwd:
            if not Upn:
                st.error("Please enter a Username")
            if not Email:
                st.error("Please enter an Email Address")
            if not Pwd:
                st.error("Please enter a Password")

        # All Inputs filled
        if Upn and Email and Pwd:

            if not sanitizeInput(Upn) or not sanitizeInput(Email):
                st.error(
                    """Username/Email must not contain:
                \n> " ' ! # $ % ^ & * ( ) : ; > < , { } [ ] \ / """
                )
            else:

                userCreateCode = UAuthDB.addUserSS(Upn, Email, Pwd)

                # Catches User Creation Input Conflicts
                if userCreateCode == 1:
                    st.error("Sorry, Username is taken.")
                elif userCreateCode == 2:
                    st.error(
                        "Sorry, This Email is already has an account. Try and sign in."
                    )
                elif userCreateCode == 3:
                    st.error("Password should be between 6 and 40 characters")
                elif userCreateCode == 4:
                    st.error(
                        "Unknown Error. A Bug Report was automaticly generated. Please refresh and try again."
                    )
                    # Generates Bug report
                    BugRepDB.generateBugRep(
                        Upn, Email, "Unknown User Creation Error Occurred"
                    )

                else:

                    # Attempt Remove Promo code
                    if not keyDB.consumeAlphaKey(aKey):
                        BugRepDB.generateBugRep(
                            Upn, Email, "Error Occured when removing promocode"
                        )
                    # User was Successfully Created
                    PopO_Signup2.empty()

                    st.info("User was Successfully Created. Please Signin!")


# Forgot Password flow
st.markdown("***")

# Password Reset
PopOut_Forgot = st.empty()
with PopOut_Forgot.container():
    st.title("Password Reset")
    with st.form("ForgotPassword"):
        st.write("Please enter a Username and Email to begin password recovery.")
        Upn = st.text_input("Username", max_chars=40)
        Email = st.text_input("Email", max_chars=40).lower()
        st.form_submit_button("Submit")


# Missing Input Catch
if Upn or Email:
    if not Email:
        st.error("Please enter an Email Address")
    elif not Upn:
        st.error("Please enter a Username")

# Both fields entered
if Upn and Email:
    if not sanitizeInput(Upn) or not sanitizeInput(Email):
        st.error(
            """Username/Email must not contain:
        \n> " ' ! # $ % ^ & * ( ) : ; > < , { } [ ] \ / """
        )
    else:

        auth = UAuthDB.valCredsForgotPwd(Upn, Email)

        # Auth failed
        if not auth:
            st.error("Username or Email are Incorrect")

        # Auth was Successful
        else:
            # Clear 1st Popout obj
            PopOut_Forgot.empty()

            # password reset Screen
            PopOut_Forgot2 = st.empty()
            with PopOut_Forgot2.container():
                st.title("Password Reset")
                with st.form("PasswordReset"):
                    st.warning(
                        "If you lost/forgot your password, please open a ticket below to get your account recovered."
                    )
                    oldPwd = st.text_input(
                        "Current Password", type="password", max_chars=60
                    )
                    st.write(
                        """Password Requirements:
                        \n> 6 - 60 Characters"""
                    )

                    NewPwd1 = st.text_input(
                        "New Password", type="password", max_chars=60
                    )
                    NewPwd2 = st.text_input(
                        "Confirm New Password", type="password", max_chars=60
                    )
                    st.form_submit_button("Reset Password")

            # Input validation
            if oldPwd or NewPwd1 or NewPwd2:
                # Missing Inputs
                if not oldPwd:
                    st.error("Please enter your old password to continue.")
                if not NewPwd1:
                    st.error("Please enter your new password to continue.")
                if oldPwd and NewPwd1 and not NewPwd2:
                    st.error("Please confirm your new password to continue.")
                elif NewPwd1 != NewPwd2:
                    st.error("New passwords do not match.")
                elif oldPwd == NewPwd1:
                    st.error("Old and New passwords cant be the same.")

            # Password Reset
            if oldPwd and NewPwd1 and NewPwd2:
                if len(list(NewPwd1)) < 6:
                    st.error("Password should be between 6 and 40 characters")
                elif not UAuthDB.valCreds(Upn, oldPwd):
                    st.error("Old Password is incorrect.")
                else:
                    UAuthDB.updatePwd(Upn, NewPwd1)
                    logging.info(f"[{Upn}] User Password reset")
                    st.success("Password Successfully Reset. Please try and sign in.")


st.markdown("***")


# Support Ticket Submission
with st.container():
    with st.form("Phillip the form"):
        st.subheader("Submit Account Support Ticket")
        st.write(
            """If you experience issues with Signin or Signup, please open a Support ticket."""
        )
        Contact = st.text_input(
            "Contact Email (For faster recovery, please use the email used when the account was created.)"
        ).lower()
        Topic = st.selectbox(
            "Issue",
            [
                "(Select a Topic)",
                "Account Lockout",
                "Forgot/Lost Password",
                "Alpha Key Redeption",
                "Other",
            ],
        )
        Issue = st.text_area(
            "Ensure to include as much detail as possible.", max_chars=500
        )
        st.form_submit_button("Submit")

        if Issue and not Contact:
            st.error(
                "Please enter a Contact Email, so we can reach you when your account is recovered."
            )
        elif not Issue and Topic != "(Select a Topic)":
            st.error("Please enter a decription to the issue you are facing.")
        elif Issue:
            logging.info(f"[{Contact}] User submittied a Support Ticket")
            st.info("Submitted. We will reach back to you, via your email contacct")

            # Structure Data into Dict && Push to SupportDB
            SupportDB.generateSupport(Contact, Topic, Issue)

            # Wipe Support Object
            st.empty()

            # Clear Bug-Var
            del Issue, Topic

st.write(f"Build v{buildV}")
