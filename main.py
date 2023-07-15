import streamlit as st
import sqlite3
from transformers import pipeline
import hashlib


def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False


# DB Management
conn = sqlite3.connect('data.db')
c = conn.cursor()


def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')


def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username,password) VALUES (?,?)', (username, password))
    conn.commit()


def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    return data


def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
    return data


# @st.cache(allow_output_mutation=True)
@st.cache_resource
def load_summarizer():
    model = pipeline("summarization", device=0)
    return model


def generate_chunks(inp_str):
    max_chunk = 500
    inp_str = inp_str.replace('.', '.<eos>')
    inp_str = inp_str.replace('?', '?<eos>')
    inp_str = inp_str.replace('!', '!<eos>')

    sentences = inp_str.split('<eos>')
    current_chunk = 0
    chunks = []
    for sentence in sentences:
        if len(chunks) == current_chunk + 1:
            if len(chunks[current_chunk]) + len(sentence.split(' ')) <= max_chunk:
                chunks[current_chunk].extend(sentence.split(' '))
            else:
                current_chunk += 1
                chunks.append(sentence.split(' '))
        else:
            chunks.append(sentence.split(' '))

    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = ' '.join(chunks[chunk_id])
    return chunks


if 'isLogin' not in st.session_state:
    # st.session_state['isLogin'] = False
    st.session_state['isLogin'] = True

st.title("Summarize Text")

# menu = ["Login", "SignUp", "Home"]
menu = ["Home"]
choice = st.sidebar.selectbox("Menu", menu)
summarizer = load_summarizer()

if choice == "Login":
    st.subheader("Login Section")

    username = st.sidebar.text_input("User Name")
    password = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Login"):
        create_usertable()
        hashed_pswd = make_hashes(password)
        result = login_user(username, check_hashes(password, hashed_pswd))
        if result:
            menu.append("Home")
            st.session_state.isLogin = True
            st.success("Logged In as {}".format(username))
            st.success("From menu, select Home and enjoy summarization!")
        else:
            st.warning("Incorrect Username/Password")
    if st.sidebar.button("Logout"):
        st.session_state.isLogin = False
        st.success("You have successfully logged out!")
elif choice == "Home":
    st.subheader("Home")
    if st.session_state.isLogin:
        sentence = st.text_area('Please paste your article :', height=30)
        button = st.button("Summarize")

        max = st.sidebar.slider('Select summary maximum length', 50, 500, step=10, value=150)
        min = st.sidebar.slider('Select summary minimum length', 10, 450, step=10, value=50)
        do_sample = st.sidebar.checkbox("Do sample", value=False)
        with st.spinner("Generating Summary.."):
            if button and sentence:
                chunks = generate_chunks(sentence)
                res = summarizer(chunks,
                                 max_length=max,
                                 min_length=min,
                                 do_sample=do_sample)
                text = ' '.join([summ['summary_text'] for summ in res])
                st.write(text)
                st.download_button('Download Summary', text)

    else:
        st.warning("You should login first!")


elif choice == "SignUp":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    if st.button("Signup"):
        create_usertable()
        add_userdata(new_user, make_hashes(new_password))
        st.success("You have successfully created a valid Account")
        st.info("Go to Login Menu to login")
