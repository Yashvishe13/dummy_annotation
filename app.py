import streamlit as st
import pandas as pd
import os
import requests, json, base64, datetime as dt

# -------------------- CONFIG --------------------
repo = "Yashvishe13/dummy_annotation"     # GitHub repo
branch = "main"                            # Repo branch
csv_filename_in_repo = "temp.csv"          # File in the repo
image_folder = "images"                    # Local image folder
# -------------------------------------------------

# -------- GitHub CSV Read Function --------
@st.cache_data(ttl=60)
def load_csv_from_github():
    token = st.secrets["GH_TOKEN"]
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{csv_filename_in_repo}"
    headers = {"Authorization": f"Bearer {token}"}
    return pd.read_csv(url)

# -------- GitHub CSV Save Function --------
def push_csv_to_github(df, path=csv_filename_in_repo):
    token = st.secrets["GH_TOKEN"]
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    # Get file SHA
    res = requests.get(api_url, headers=headers)
    if res.status_code != 200:
        st.error(f"❌ Failed to get file SHA: {res.status_code} - {res.text}")
        return
    sha = res.json()["sha"]

    # Prepare content
    new_content = base64.b64encode(df.to_csv(index=False).encode()).decode()
    commit_msg = f"Update via Streamlit on {dt.datetime.utcnow().isoformat()}"

    payload = {
        "message": commit_msg,
        "content": new_content,
        "sha": sha,
        "branch": branch
    }

    # Push update
    response = requests.put(api_url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        st.success("✅ CSV updated on GitHub.")
    else:
        st.error(f"❌ Failed to update CSV: {response.status_code} - {response.text}")

# -------- Load Data --------
df = load_csv_from_github()

# -------- UI: Member Selection --------
members = ["Yash", "Gagan", "Amit", "Junda", "Xin"]
st.sidebar.title("Select Member")
selected_member = st.sidebar.radio("Team Members", options=members)

# -------- Session Management --------
if 'subset_index' not in st.session_state or st.session_state.get('last_member') != selected_member:
    st.session_state.subset_index = 0
    st.session_state.last_member = selected_member

# -------- Filter User Data --------
member_df = df[df['assigned_to'] == selected_member].reset_index(drop=True)
if member_df.empty:
    st.warning(f"No questions remaining for {selected_member}.")
    st.stop()

# -------- Navigation --------
col_nav = st.columns([1, 1])
with col_nav[0]:
    if st.button("⬅ Previous") and st.session_state.subset_index > 0:
        st.session_state.subset_index -= 1
        st.rerun()
with col_nav[1]:
    if st.button("Next ➡") and st.session_state.subset_index < len(member_df) - 1:
        st.session_state.subset_index += 1
        st.rerun()

# -------- Display Current Row --------
current_index = st.session_state.subset_index
row = member_df.iloc[current_index]

st.title(f"{selected_member}'s Questions")
st.write(f"**Progress: {current_index + 1} / {len(member_df)}**")
st.progress((current_index + 1) / len(member_df))

# -------- Image Display --------
image_id = row['id']
image_path = os.path.join(image_folder, f"{image_id}.jpg")
if os.path.exists(image_path):
    st.image(image_path, caption=f"ID: {image_id}", use_container_width=True)
else:
    st.warning(f"Image not found for ID {image_id}")

# -------- Editable Fields --------
title       = st.text_input("Title",              value=row['title'])
question    = st.text_area ("Question",           value=row['reformatted_question'], height=100)
option_a    = st.text_input("Option A",           value=row.get('option a', ''))
option_b    = st.text_input("Option B",           value=row.get('option b', ''))
option_c    = st.text_input("Option C",           value=row.get('option c', ''))
option_d    = st.text_input("Option D",           value=row.get('option d', ''))
category    = st.text_input("Category",           value=row.get('category', ''))
subcategory = st.text_input("Subcategory",        value=row.get('Subcategory', ''))

# -------- Save Button --------
if st.button("💾 Save Changes"):
    idx = df[df['id'] == image_id].index[0]
    df.loc[idx, ['title', 'reformatted_question',
                 'option a', 'option b', 'option c', 'option d',
                 'category', 'Subcategory']] = [
        title, question, option_a, option_b, option_c, option_d,
        category, subcategory
    ]
    push_csv_to_github(df)
    st.success("Changes saved and pushed to GitHub.")

# -------- Remove Button --------
if st.button("🗑️ Remove Question"):
    df = df[df['id'] != image_id].reset_index(drop=True)
    push_csv_to_github(df)
    st.success(f"Question ID {image_id} removed.")
    if st.session_state.subset_index >= len(member_df) - 1 and st.session_state.subset_index > 0:
        st.session_state.subset_index -= 1
    st.rerun()
