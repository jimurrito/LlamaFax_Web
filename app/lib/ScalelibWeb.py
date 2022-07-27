try:
    from lib.MongoDB import MongoDB, UAuth
except:
    from MongoDB import MongoDB, UAuth
from operator import contains
import pymongo
import streamlit as st
import logging


def getPhrases(Message):
    out = []
    for Phrase in Message["render"]:
        out.append(f"{Phrase}")  # (f"    [{ct}] - {Phrase}")
    return out  # "\n".join(out)


def rateFaxNew(opts: list, message: list, Mod="Good"):
    def autoComplete(Array: list = message, Options: list = opts):
        ct = 0
        out = []
        while ct <= (len(Array) - 1):
            if str(ct) not in Options:
                out.append(ct)
            ct += 1
        return out

    out = {}

    # If all is provided
    if str(opts).find("all") != -1:
        for phrase in message:
            out.update({phrase: Mod})
        return out

    # If all is provided
    if str(opts).find("none") != -1:
        for phrase in message:
            out.update({phrase: "Bad"})
        return out

    # individual input
    for opt in opts:  # Opts being a list of inputs from the UI
        # Out of range index catch
        if int(opt) < len(message):
            out.update({message[int(opt)]: Mod})
    # Auto Label leftovers as bad
    for opt in autoComplete():
        out.update({message[int(opt)]: "Bad"})
    return out


def clearInput():
    st.session_state["Uput"] = ""


def progBar(DBObj: MongoDB, target=5000):
    cCT = DBObj.count()
    prog = cCT / target
    st.progress(0).progress(prog)
    st.write(f"{prog}% ({cCT}) to a goal of {target}")


def ScoreBoard(AuthDBObj: UAuth, Limit: int = 10):
    # <Might not be needed> Get the sum of all points in DB ($Total)
    # get first 5 highest scoring users
    #   > Show Rank, Score, and UserName

    # Convert to using a form, where you can use the submit button to refresh the table.
    # table looks ugly, need to find better layout!!
    with st.container():
        with st.form("ScoreBoard", clear_on_submit=True):
            ct = 1
            st.subheader("Leader Board (Top - 10)")
            for x in list(
                AuthDBObj.Col.find(
                    projection={"_id": False, "upn": True, "score": True}
                )
                .sort("score", pymongo.DESCENDING)
                .limit(Limit)
            ):
                if ct == 1:
                    Icon = "👑"
                else:
                    Icon = ""
                st.write(
                    f"[ {ct} ] - {x['upn']} - {x['score']} {Icon}",
                )
                ct += 1
            st.write("_" * 3)
            st.form_submit_button("Refresh")


def sanitizeInput(Input: str):
    for Bl in list(""""'!#$%^&*():;><,{}[]\/"""):
        if Input.__contains__(Bl):
            return False
    return True


# Streamlit Objects


def STMessagePeristence(RendQ):
    if "messageState" not in st.session_state:
        st.session_state["messageState"] = True
        message = RendQ.pull()
        st.session_state["messageStore"] = message
    elif st.session_state["messageState"] == False:
        st.session_state["messageState"] = True
        message = RendQ.pull()
        st.session_state["messageStore"] = message
    else:
        message = st.session_state["messageStore"]
    return message


def STLogin(Image: str = "assets/lfx_profile_pic.jpg"):
    Popout = st.empty()  # AuthScreen Container Object
    with Popout.container():
        st.image(Image, width=250)
        st.title("LlamaFax Corpus Generator")
        with st.form("AuthScreen"):  # , clear_on_submit=True
            st.info(
                """This app is in Private Preview, thus has no self-service signup. 
            \nPlease contact https://github.com/jimurrito to get access, and help contribute! 😊"""
            )
            st.write("Please Sign-in to Continue")
            Upn = st.text_input("Username/Email", max_chars=40)
            Pwd = st.text_input("Password", type="password", max_chars=60)
            st.form_submit_button("Login")
        logging.info(f"Client Connection Achieved")
    return Popout, Upn, Pwd


def STsidebar(UserAuthObj, UAuthDB, Image: str = "assets/lfx_profile_pic.jpg"):
    """Sidebar Object. Sidebar is a var, and cant be removed one called.
    \nOnly Modified."""
    with st.sidebar:
        st.image(Image, width=125)
        with st.container():
            st.title("Hello, " + UserAuthObj["upn"])
            st.subheader("Score: " + str(UserAuthObj["score"]))
        st.markdown("***")
        ScoreBoard(UAuthDB)


def STdrawOptions(message):
    with st.container():
        st.table(getPhrases(message))
        st.write("Type 'all' or 'none', if all statments fit that assignment.")
        st.write("Enter multiple values seperated with a space.")
    return str(
        st.text_input("Examples: (0 1 2 ...) ; (all) ; (none) ", max_chars=20)
    ).split()


def STClearOptions(EmptyObj, Opts):
    if Opts == []:
        return
    EmptyObj.empty()


def main():

    print(sanitizeInput("yes"))


if __name__ == "__main__":
    main()
