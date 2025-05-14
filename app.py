import streamlit as st
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import io
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

# # Load your CSV
# df = pd.read_csv("temp.csv")

# # Split it into 3 parts
# chunks = []
# chunk_size = len(df) // 3
# for i in range(2):
#     chunks.append(df.iloc[i*chunk_size:(i+1)*chunk_size])
# chunks.append(df.iloc[2*chunk_size:])

# # Save each chunk
# for i, part in enumerate(chunks):
#     db_name = f"data_part{i+1}.db"
#     conn = sqlite3.connect(db_name)
#     part.to_sql("data_table", conn, if_exists="replace", index=False)
#     conn.close()

# User -> DB mapping
USER_DB_MAP = {
    "Yash": "data_part1.db",
    "Gagan": "data_part2.db",
    "Amit": "data_part3.db"
}

TABLE_NAME = "data_table"
IMAGE_FOLDER = "images"

# ---------- Database Helpers ----------

def get_db_connection(user):
    return sqlite3.connect(USER_DB_MAP[user])

def get_data(user):
    conn = get_db_connection(user)
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()
    return df

def update_row(user, row_id, updates):
    conn = get_db_connection(user)
    set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
    values = list(updates.values()) + [row_id]
    conn.execute(f"UPDATE {TABLE_NAME} SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_row(user, row_id):
    conn = get_db_connection(user)
    conn.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

# ---------- Progress Tracking ----------

def get_user_index(user):
    conn = get_db_connection(user)
    conn.execute("CREATE TABLE IF NOT EXISTS progress_tracker (user TEXT PRIMARY KEY, question_index INTEGER)")
    cursor = conn.execute("SELECT question_index FROM progress_tracker WHERE user = ?", (user,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def set_user_index(user, index):
    conn = get_db_connection(user)
    conn.execute("""
        INSERT INTO progress_tracker (user, question_index)
        VALUES (?, ?)
        ON CONFLICT(user) DO UPDATE SET question_index=excluded.question_index
    """, (user, index))
    conn.commit()
    conn.close()

# ---------- UI Panel Per User ----------

def show_distribution_charts(df, user):
    st.subheader("📊 Category Distribution")
    if "category" in df.columns:
        cat_counts = df["category"].value_counts()
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        bars1 = ax1.bar(cat_counts.index, cat_counts.values)
        ax1.set_ylabel("Count")
        ax1.set_title(f"{user} - Category Distribution")
        ax1.tick_params(axis='x', rotation=90)
        
        # Add labels on top of bars
        for bar in bars1:
            height = bar.get_height()
            ax1.annotate(f'{int(height)}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),  # 3 points vertical offset
                         textcoords="offset points",
                         ha='center', va='bottom')
        plt.tight_layout()
        st.pyplot(fig1)
    else:
        st.info("No 'category' data available.")

    st.subheader("📊 Subcategory Distribution")
    if "Subcategory" in df.columns:
        subcat_counts = df["Subcategory"].value_counts()
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        bars2 = ax2.bar(subcat_counts.index, subcat_counts.values)
        ax2.set_ylabel("Count")
        ax2.set_title(f"{user} - Subcategory Distribution")
        ax2.tick_params(axis='x', rotation=90)
        
        # Add labels on top of bars
        for bar in bars2:
            height = bar.get_height()
            ax2.annotate(f'{int(height)}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),
                         textcoords="offset points",
                         ha='center', va='bottom')
        plt.tight_layout()
        st.pyplot(fig2)
    else:
        st.info("No 'Subcategory' data available.")


def download_csv_button(user):
    df = get_data(user)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"{user}_data.csv",
        mime="text/csv",
        key=f"{user}_download"
    )

def display_user_panel(user):
    st.header(f"{user}'s Questions")
    
    df = get_data(user)

    if df.empty:
        st.warning("No questions available.")
        return

    # Get question index (from session or DB)
    if f"{user}_index" not in st.session_state:
        st.session_state[f"{user}_index"] = get_user_index(user)
    idx = st.session_state[f"{user}_index"]
    row = df.iloc[idx]

    st.markdown(f"**Question ID: {row['id']}**")

    # Progress bar
    st.markdown(f"**Question {idx + 1} of {len(df)}**")
    st.progress((idx + 1) / len(df))

    # Editable fields
    st.subheader("Category and Subcategory")
    
    category = st.text_input("Category", value=row["category"], key=f"{user}_cat")
    subcategory = st.text_input("Subcategory", value=row["Subcategory"], key=f"{user}_subcat")

    st.subheader("Question")
    question = st.text_area("Edit Question", value=row["question"], key=f"{user}_question")

    # Image
    img_path = os.path.join(IMAGE_FOLDER, f"{row['id']}.jpg")
    try:
        st.image(img_path, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load image: {e}")

    # Options + Comments
    options = {}
    for opt in ["A", "B", "C", "D", "E", "F"]:
        opt_key = f"option{opt}"
        comment_key = f"comment{opt}"
        options[opt_key] = st.text_input(f"Option {opt}", value=row.get(opt_key, ""), key=f"{user}_{opt_key}")
        st.caption(f"Comment {opt}: {row.get(comment_key, '')}")

    # Buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Previous", key=f"{user}_prev") and idx > 0:
            idx -= 1
            st.session_state[f"{user}_index"] = idx
            set_user_index(user, idx)
            st.rerun()
    with col2:
        if st.button("Next", key=f"{user}_next") and idx < len(df) - 1:
            idx += 1
            st.session_state[f"{user}_index"] = idx
            set_user_index(user, idx)
            st.rerun()
    with col3:
        if st.button("Delete Question", key=f"{user}_del"):
            delete_row(user, row["id"])
            st.success("Question deleted.")
            idx = max(0, idx - 1)
            st.session_state[f"{user}_index"] = idx
            set_user_index(user, idx)
            st.rerun()
    with col4:
        if st.button("Save Edits", key=f"{user}_save"):
            update_row(user, row["id"], {
                "question": question,
                "category": category,
                "Subcategory": subcategory,
                **options
            })
            st.success("Edits saved.")
    
    # Download button
    st.markdown("### 💾 Export")
    download_csv_button(user)
    show_distribution_charts(df, user)

# ---------- Main ----------

def main():
    st.title("Question Review Interface")
    for user in USER_DB_MAP.keys():
        with st.expander(user, expanded=True):
            display_user_panel(user)

if __name__ == "__main__":
    main()
