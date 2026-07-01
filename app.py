import streamlit as st
import json
import os

DB_FILE = "workout_db.json"

# Load data from the JSON file database
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Default blank structure if file doesn't exist or is corrupted
    return {"users": [], "workouts": {}}

# Save data back to the JSON file database
def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load database into session state
db = load_data()

st.title("🏋️‍♂️ Workout Manager")
st.caption("Permanent Cross-Device Workout Sync")
st.write("---")

# 1. Login / Profile Selection Side
st.sidebar.header("🔐 Login Profile")
user_type = st.sidebar.radio("Select Role:", ["Creator / Coach", "User / Athlete"])

# Manage User Accounts List dynamically
st.sidebar.subheader("Manage Accounts")
new_user_reg = st.sidebar.text_input("Register New Athlete Name:")
if st.sidebar.button("Register Athlete"):
    if new_user_reg.strip() and new_user_reg not in db["users"]:
        db["users"].append(new_user_reg)
        db["workouts"][new_user_reg] = []
        save_data(db)
        st.sidebar.success(f"Registered {new_user_reg}!")
        st.rerun()

user_name = st.sidebar.selectbox("Log in as:", ["Coach"] + db["users"] if user_type == "Creator / Coach" else db["users"])

if user_name == "Coach" and user_type == "User / Athlete":
    st.warning("Coaches must use the Creator profile layout. Change role in sidebar.")
elif not db["users"] and user_type == "User / Athlete":
    st.info("No athletes registered yet! Use the sidebar to add a profile.")
else:
    # ================= CREATOR SIDE =================
    if user_type == "Creator / Coach":
        st.header(f"Welcome, Coach!")
        
        # Section A: Assign a New Workout
        st.subheader("➕ Assign a New Workout")
        if db["users"]:
            target_user = st.selectbox("Select Athlete:", db["users"])
            workout_title = st.text_input("Exercise Title (e.g., Squat):")
            workout_desc = st.text_area("Instructions:")
            
            if st.button("Assign Workout"):
                if workout_title.strip() and workout_desc.strip():
                    new_workout = {
                        "title": workout_title,
                        "description": workout_desc,
                        "logged": None
                    }
                    db["workouts"][target_user].append(new_workout)
                    save_data(db)
                    st.success(f"Assigned {workout_title} to {target_user}!")
                    st.rerun()
                else:
                    st.error("Please fill out both the title and instructions.")
        else:
            st.info("Register an athlete in the sidebar first to assign workouts.")

        st.write("---")
        
        # Section B: Review Athlete Progress
        st.subheader("📊 Review Athlete Progress")
        if db["users"]:
            review_user = st.selectbox("View Workouts For:", db["users"], key="review_user")
            user_workouts = db["workouts"].get(review_user, [])
            
            if not user_workouts:
                st.info(f"{review_user} has no workouts assigned.")
            else:
                for idx, wk in enumerate(user_workouts):
                    with st.expander(f"Exercise {idx+1}: {wk['title']}"):
                        st.write(f"**Instructions:** {wk['description']}")
                        if wk["logged"] is None:
                            st.info("Status: ⏳ Pending Submission")
                        else:
                            st.success("Status: ✅ Completed")
                            log = wk["logged"]
                            st.table({
                                "Metric": ["Sets", "Reps", "Weight", "Athlete Comments"],
                                "Submitted Value": [log['sets'], log['reps'], log['weight'], log['comment']]
                            })
        else:
            st.info("No athlete records found.")

    # ================= USER SIDE =================
    else:
        st.header(f"Welcome back, {user_name}!")
        my_workouts = db["workouts"].get(user_name, [])
        
        st.subheader("📋 Your Assigned Workouts")
        if not my_workouts:
            st.info("No workouts assigned to you right now!")
        else:
            for idx, wk in enumerate(my_workouts):
                status_label = "(✅ Logged)" if wk["logged"] else "(⏳ To Do)"
                with st.expander(f"🏋️ {wk['title']} {status_label}"):
                    st.write(f"**Coach's Instructions:** {wk['description']}")
                    st.write("---")
                    
                    if wk["logged"] is not None:
                        st.write("**You logged:**")
                        st.write(f"- **Sets:** {wk['logged']['sets']} | **Reps:** {wk['logged']['reps']} | **Weight:** {wk['logged']['weight']}")
                        st.write(f"- **Your Comment:** {wk['logged']['comment']}")
                    else:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            sets = st.number_input("Sets Completed", min_value=0, step=1, key=f"sets_{idx}")
                        with col2:
                            reps = st.number_input("Reps per Set", min_value=0, step=1, key=f"reps_{idx}")
                        with col3:
                            weight = st.number_input("Weight Used", min_value=0.0, step=2.5, key=f"weight_{idx}")
                            
                        comment = st.text_input("Add Comments:", key=f"comment_{idx}")
                        
                        if st.button("Submit Workout Log", key=f"btn_{idx}"):
                            db["workouts"][user_name][idx]["logged"] = {
                                "sets": sets,
                                "reps": reps,
                                "weight": weight,
                                "comment": comment
                            }
                            save_data(db)
                            st.success("Workout logged successfully!")
                            st.rerun()
