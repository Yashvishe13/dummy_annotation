import streamlit as st
import pandas as pd
import os

# ---------------------------------
# Load data & basic setup
# ---------------------------------
csv_path = 'temp.csv'
image_folder = 'images'
df = pd.read_csv(csv_path)

members = ["Yash", "Gagan", "Amit", "Junda", "Xin"]
st.sidebar.title("Select Member")
selected_member = st.sidebar.radio("Team Members", options=members)

# Initialise/refresh session state
if 'subset_index' not in st.session_state or st.session_state.get('last_member') != selected_member:
    st.session_state.subset_index = 0
    st.session_state.last_member = selected_member

member_df = df[df['assigned_to'] == selected_member].reset_index(drop=True)
if member_df.empty:
    st.warning(f"No questions remaining for {selected_member}.")
    st.stop()

# 🔄 Navigation (update index then rerun)
nav_prev = st.button("⬅ Previous", key="prev_btn")
nav_next = st.button("Next ➡", key="next_btn")

if nav_prev and st.session_state.subset_index > 0:
    st.session_state.subset_index -= 1
    st.rerun()

if nav_next and st.session_state.subset_index < len(member_df) - 1:
    st.session_state.subset_index += 1
    st.rerun()

# ---------------------------------
# Display the current row *after* any navigation
# ---------------------------------
current_index = st.session_state.subset_index
row = member_df.iloc[current_index]

st.title(f"{selected_member}'s Questions")
st.write(f"**Progress: {current_index + 1} / {len(member_df)}**")
st.progress((current_index + 1) / len(member_df))

# Image
image_id = row['id']
image_path = os.path.join(image_folder, f"{image_id}.jpg")

if os.path.exists(image_path):
    st.image(image_path, caption=f"ID: {image_id}", use_container_width=True)
else:
    st.warning(f"Image not found for ID {image_id}")

# Editable fields
title       = st.text_input("Title",              value=row['title'])
question    = st.text_area ("Question",           value=row['reformatted_question'], height=100)
option_a    = st.text_input("Option A",           value=row.get('option a', ''))
option_b    = st.text_input("Option B",           value=row.get('option b', ''))
option_c    = st.text_input("Option C",           value=row.get('option c', ''))
option_d    = st.text_input("Option D",           value=row.get('option d', ''))
category    = st.text_input("Category",           value=row.get('category', ''))
subcategory = st.text_input("Subcategory",        value=row.get('Subcategory', ''))

# Save edits
if st.button("Save Changes"):
    idx = df[df['id'] == image_id].index[0]
    df.loc[idx, ['title', 'reformatted_question',
                 'option a', 'option b', 'option c', 'option d',
                 'category', 'Subcategory']] = [
        title, question, option_a, option_b, option_c, option_d,
        category, subcategory
    ]
    df.to_csv(csv_path, index=False)
    st.success("Changes saved!")

# Remove
if st.button("Remove Question"):
    df = df[df['id'] != image_id].reset_index(drop=True)
    df.to_csv(csv_path, index=False)
    st.success(f"Removed question ID: {image_id}")
    if st.session_state.subset_index >= len(member_df) - 1 and st.session_state.subset_index > 0:
        st.session_state.subset_index -= 1
    st.experimental_rerun()
