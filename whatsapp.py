import streamlit as st
from datetime import datetime
import json
from pathlib import Path

ONLINE_FILE = Path("online_users.json")

# ------------------ Utilities ------------------

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "current_channel" not in st.session_state:
        st.session_state.current_channel = "general"
    if "channels" not in st.session_state:
        st.session_state.channels = {"general": []}


def add_message(sender, message, channel=None):
    if channel is None:
        channel = st.session_state.current_channel
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_data = {"sender": sender, "message": message, "timestamp": timestamp, "channel": channel}
    st.session_state.messages.append(message_data)
    if channel not in st.session_state.channels:
        st.session_state.channels[channel] = []
    st.session_state.channels[channel].append(message_data)

# ------------------ Online Users (Shared JSON) ------------------

def load_online_users():
    if ONLINE_FILE.exists():
        with open(ONLINE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_online_users(users):
    with open(ONLINE_FILE, "w") as f:
        json.dump(users, f)

def update_online_users(name):
    now = datetime.now().timestamp()
    users = load_online_users()
    # remove inactive users (older than 2 minutes)
    users = {u: t for u, t in users.items() if now - t < 120}
    if name:
        users[name] = now
    save_online_users(users)
    return list(users.keys())


# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="Human Chat App", page_icon="💬", layout="wide")
init_state()

st.title("💬 Human-to-Human Chat App")

# ------------------ Login ------------------
if not st.session_state.user_name:
    st.subheader("Join the Chat")
    name = ""
    channel = "general"

    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input("Enter your name:", value=name, key="login_name")
    with col2:
        channel = st.text_input("Channel name:", value=channel, key="login_channel")

    if st.button("Join Chat", key="join_chat_button") and name.strip():
        st.session_state.user_name = name.strip()
        st.session_state.current_channel = channel.strip().lower()
        if st.session_state.current_channel not in st.session_state.channels:
            st.session_state.channels[st.session_state.current_channel] = []
        add_message("System", f"{name} joined the chat", st.session_state.current_channel)
    st.stop()

# ------------------ Sidebar ------------------
with st.sidebar:
    st.header("Chat Settings")
    st.write(f"Logged in as: **{st.session_state.user_name}**")

    st.subheader("Channels")
    new_channel = st.text_input("Create new channel:", key="new_channel_input")
    if st.button("Create Channel", key="create_channel_button") and new_channel.strip():
        channel_name = new_channel.strip().lower()
        if channel_name not in st.session_state.channels:
            st.session_state.channels[channel_name] = []
            st.session_state.current_channel = channel_name
            add_message("System", f"{st.session_state.user_name} created this channel", channel_name)
        else:
            st.error("Channel already exists")

    st.write("Available channels:")
    for channel in st.session_state.channels.keys():
        if st.button(f"#{channel}", key=f"channel_{channel}_button"):
            st.session_state.current_channel = channel

    st.write("---")
    st.subheader("👥 Online Users")
    online_users = update_online_users(st.session_state.user_name)
    if online_users:
        for user in online_users:
            st.write(f"✅ {user}")
    else:
        st.write("No users online")

    if st.button("Leave Chat", key="leave_chat_button"):
        add_message("System", f"{st.session_state.user_name} left the chat", st.session_state.current_channel)
        st.session_state.user_name = None

# ------------------ Main Chat ------------------
st.header(f"Channel: #{st.session_state.current_channel}")
chat_container = st.container()
with chat_container:
    for msg in st.session_state.channels.get(st.session_state.current_channel, []):
        color = "#1100FA" if msg['sender'] == st.session_state.user_name else "#000000"
        st.markdown(f"""
            <div style='background-color: {color}; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                <strong>{msg['sender']}</strong> <small>{msg['timestamp']}</small>
                <p style='margin: 5px 0;'>{msg['message']}</p>
            </div>
        """, unsafe_allow_html=True)

# ------------------ Chat Input Form ------------------
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        message = st.text_input("Type your message:", key="chat_message_input")
    with col2:
        submitted = st.form_submit_button("Send")

    if submitted and message:
        add_message(st.session_state.user_name, message)

st.write("---")
st.caption("Users will be marked offline after 2 minutes of inactivity.")
