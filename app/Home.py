from lib.ScalelibWeb import sanitizeInput
from lib.ScalelibWeb import (
    STLogin,
    STsidebar,
    STMessagePeristence,
    progBar,
    STdrawOptions,
    rateFaxNew,
)
from lib.MongoDB import MongoDB, Queue, UAuth
import streamlit as st
import logging
import os

# Site State Configuration
st.set_page_config(
    page_title="🦙 LlamaFax",
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
# DBHost = "10.4.18.2"
# Build Version #
buildV = os.getenv("BUILDVER", "0.0")

# Local host works, as its the relation between the service and the server, not the browser :)
RendQNam = "render"
ArchDBNam = "archive"
CorpDBNam = "corpus"
UAuthDBNam = "userAuth"
BugRepDBNam = "repBugs"


rndQueue = Queue(RendQNam, Host=DBHost)
ArchiveDB = MongoDB(ArchDBNam, Indexes="raw", Host=DBHost)
UAuthDB = UAuth(UAuthDBNam, Host=DBHost)
BugRepDB = MongoDB(BugRepDBNam, Host=DBHost, Indexes="BugID#")


# Auth Screen
# returns Login Screen Conatiner Object, and user Input
Popout, Upn, Pwd = STLogin()

# Missing Input Catch
if Upn or Pwd:
    if not Upn:
        st.error("Please enter a Username/Email")
    elif not Pwd:
        st.error("Please enter a Password")

# all inputs submited
if Upn and Pwd:

    if not sanitizeInput(Upn):
        st.error(
            """Input must not contain:
        \n> " ' ! # $ % ^ & * ( ) : ; > < , { } [ ] \ / """
        )

    else:

        auth = UAuthDB.valCreds(Upn, Pwd)

        # If Auth validation fails
        if not auth:
            st.error("Username or Password is incorrect")

        # if Auth validation successeded
        else:
            logging.info(f"User Login: {auth['upn']}")
            # Removes Popout Element when successfully Autheticated
            Popout.empty()

            # Post-Signon side bar
            STsidebar(auth, UAuthDB)

            # Verbose Output user Auth Object
            logging.debug("user Auth object", auth)

            message = STMessagePeristence(rndQueue)

            Buttontxt = "Submit"

            # Main Options Page
            st.info(
                "Application is in Private Preview. If an error occurs, please submit a bug report, and refresh your screen. Thanks in Advance!"
            )

            with st.form(
                "Freddy the form", clear_on_submit=True
            ):  # clear_on_submit=True
                progBar(ArchiveDB)
                st.header("LlamaFax Corpus Generator")
                st.write("Input the ID of the statments that are coherent and/or funny")

                Opts = STdrawOptions(message)

                if Opts:

                    logging.info(f"[{auth['upn']}] User Input Received")
                    logging.debug(f"[{auth['upn']}] : {Opts}")

                    Buttontxt = "Next"
                    st.info("Please select 'Next' to coninue")
                    # Binds ratings with user input, outputs dict with statments and ratings.
                    # replaces the list of unranked statments
                    message["render"] = rateFaxNew(Opts, message["render"])

                    # Add user mark on Archive message
                    message.update({"user": auth["upn"]})

                    # [Pushes]
                    # Push to Archive DB
                    # Archival Data of ALL renders, and components.
                    logging.debug(f"[{auth['upn']}] : {message}")
                    logging.info(f"[{auth['upn']}] Pushing to MongoDB")
                    ArchiveDB.push(message)

                    # Deletes from Render Queue
                    st.session_state["messageState"] = False
                    del Opts

                    # Adds to user score
                    UAuthDB.addtoScore(auth)
                    logging.info(f"[{auth['upn']}] User Score Increased")

                st.form_submit_button(
                    Buttontxt,
                )

        # Line break between forms
        st.markdown("***")

        # Bug Submission
        with st.form("Phillip the form", clear_on_submit=True):
            st.subheader("Submit Feedback / Report a Bug")
            st.write(
                """We always looking for feedback to improve the usability of this platform. 
                \nPlease Submit any Feedback or Bugs encountered.
                """
            )
            # "Example: 'Frozen Screen', 'Score not Updating', 'Repeating Questions'  "
            BugRep = st.text_area(
                "Ensure to include as much detail as possible.", max_chars=500
            )
            st.form_submit_button("Submit")

            if BugRep:
                logging.info(f"[{auth['upn']}] User submittied Feedback/Report")
                st.info("Submitted. Thank you for your Contribution!")

                # Structure Data into Dict && Push to BugReportDB
                BugRepDB.generateBugRep(auth["upn"], auth["email"], BugRep)

                # Clear Bug-Var
                del BugRep

st.write(f"Build v{buildV}")
