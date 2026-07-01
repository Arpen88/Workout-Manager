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
    return {"users": [], "workouts": {}}

# Save data back to the JSON file database
def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

st.title("🏋️‍♂️ Workout Manager")
st.caption("Permanent Cross-Device Workout Sync")
st.write("---")

# Login / Profile Selection Side
st.sidebar.header("🔐 Login Profile")
user_type = st.sidebar.radio("Select Role:", ["Creator / Coach", "User / Athlete"])

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
        
        st.subheader("➕ Assign a Multi-Exercise Workout")
        if db["users"]:
            target_user = st.selectbox("Select Athlete:", db["users"])
            routine_title = st.text_input("Routine Name (e.g., Upper Body, Leg Day):")
            
            # Use Session State to dynamically add exercises to a list before saving
            if "temp_exercises" not in st.session_state:
                st.session_state.temp_exercises = []
                
            st.write("#### Add Exercises to this Routine:")
            ex_title = st.text_input("Exercise Name (e.g., Bench Press, Pull Ups):")
            ex_desc = st.text_area("Instructions (e.g., 4 sets of 8 reps):")
            
            if st.button("Add Exercise to List"):
                if ex_title.strip():
                    st.session_state.temp_exercises.append({
                        "title": ex_title,
                        "description": ex_desc,
                        "logged": None
                    })
                    st.success(f"Added {ex_title} to current build list!")
                else:
                    st.error("Exercise Name is required.")
                    
            if st.session_state.temp_exercises:
                st.write("**Current Build List:**")
                for i, ex in enumerate(st.session_state.temp_exercises):
                    st.text(f"  {i+1}. {ex['title']}")
                    
                if st.button("🚀 Assign Full Routine to Athlete", type="primary"):
                    if routine_title.strip():
                        new_routine = {
                            "routine_name": routine_title,
                            "exercises": st.session_state.temp_exercises
                        }
                        db["workouts"][target_user].append(new_routine)
                        save_data(db)
                        st.session_state.temp_exercises = [] # Reset list
                        st.success(f"Successfully assigned '{routine_title}' to {target_user}!")
                        st.rerun()
                    else:
                        st.error("Please provide a Routine Name before assigning.")
        else:
            st.info("Register an athlete in the sidebar first to assign workouts.")

        st.write("---")
        
        st.subheader("📊 Review Athlete Progress")
        if db["users"]:
            review_user = st.selectbox("View Workouts For:", db["users"], key="review_user")
            user_routines = db["workouts"].get(review_user, [])
            
            if not user_routines:
                st.info(f"{review_user} has no routines assigned.")
            else:
                for idx, rt in enumerate(user_routines):
                    with st.expander(f"📋 Routine: {rt['routine_name']}"):
                        for ex in rt["exercises"]:
                            st.write(f"🏋️ **{ex['title']}**")
                            st.write(f"Target: {ex['description']}")
                            if ex["logged"] is None:
                                st.info("Status: ⏳ Pending Submission")
                            else:
                                st.success("Status: ✅ Completed")
                                log = ex["logged"]
                                st.table({
                                    "Metric": ["Sets", "Reps", "Weight", "Notes"],
                                    "Submitted": [log['sets'], log['reps'], log['weight'], log['comment']]
                                })
                            st.write("---")
        else:
            st.info("No athlete records found.")

    # ================= USER SIDE =================
    else:
        st.header(f"Welcome back, {user_name}!")
        my_routines = db["workouts"].get(user_name, [])
        
        st.subheader("📋 Your Assigned Routines")
        if not my_routines:
            st.info("No workouts assigned to you right now!")
        else:
            for r_idx, rt in enumerate(my_routines):
                with st.expander(f"🧱 Routine Group: {rt['routine_name']}"):
                    for e_idx, wk in enumerate(rt["exercises"]):
                        st.write(f"### {wk['title']}")
                        st.write(f"**Instructions:** {wk['description']}")
                        
                        if wk["logged"] is not None:
                            st.success("✅ Logged")
                            st.write(f"- **Sets:** {wk['logged']['sets']} | **Reps:** {wk['logged']['reps']} | **Weight:** {wk['logged']['weight']}")
                            st.write(f"- **Your Comment:** {wk['logged']['comment']}")
                        else:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                sets = st.number_input("Sets Completed", min_value=0, step=1, key=f"sets_{r_idx}_{e_idx}")
                            with col2:
                                reps = st.number_input("Reps per Set", min_value=0, step=1, key=f"reps_{r_idx}_{e_idx}")
                            with col3:
                                weight = st.number_input("Weight Used", min_value=0.0, step=2.5, key=f"weight_{r_idx}_{e_idx}")
                                
                            comment = st.text_input("Add Comments:", key=f"comment_{r_idx}_{e_idx}")
                            
                            if st.button("Submit This Exercise Log", key=f"btn_{r_idx}_{e_idx}"):
                                db["workouts"][user_name][r_idx]["exercises"][e_idx]["logged"] = {
                                    "sets": sets,
                                    "reps": reps,
                                    "weight": weight,
                                    "comment": comment
                                }
                                save_data(db)
                                st.success("Exercise logged!")
                                st.rerun()
                        st.write("---")
