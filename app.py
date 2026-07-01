import streamlit as st
import json
import os

DB_FILE = "workout_db.json"

# Load data from the JSON file database
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                # Ensure structure compatibility
                if "users" not in data:
                    data["users"] = []
                if "workouts" not in data:
                    data["workouts"] = {}
                return data
        except:
            pass
    return {"users": [], "workouts": {}}

# Save data back to the JSON file database
def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

# Initialize authentication session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "current_role" not in st.session_state:
    st.session_state.current_role = None

# ================= WELCOME SCREEN (NOT LOGGED IN) =================
if not st.session_state.logged_in:
    st.title("🏋️‍♂️ Workout Manager")
    st.subheader("Welcome! Please sign in or register below.")
    
    tab1, tab2 = st.tabs(["🔐 Log In", "📝 Sign Up"])
    
    with tab1:
        st.write("### Sign In to Your Profile")
        login_first = st.text_input("First Name:", key="login_first").strip()
        login_last = st.text_input("Last Name:", key="login_last").strip()
        
        if st.button("Log In", type="primary"):
            full_name = f"{login_first} {login_last}".strip()
            if not login_first or not login_last:
                st.error("Please enter both your first and last name.")
            elif full_name == "Coach Admin":  # Quick bypass for master coach if needed
                st.session_state.logged_in = True
                st.session_state.current_user = "Coach Admin"
                st.session_state.current_role = "Creator / Coach / Trainer"
                st.rerun()
            elif full_name in db["users"] or any(u.get("name") == full_name for u in db["users"] if isinstance(u, dict)):
                # Find user role
                user_record = next((u for u in db["users"] if isinstance(u, dict) and u["name"] == full_name), None)
                if user_record:
                    role = user_record.get("role", "User / Athlete")
                else:
                    role = "User / Athlete" # fallback for legacy flat names
                
                st.session_state.logged_in = True
                st.session_state.current_user = full_name
                st.session_state.current_role = role
                st.success(f"Welcome back, {full_name}!")
                st.rerun()
            else:
                st.error("Profile not found. Please sign up if you don't have an account.")
                
    with tab2:
        st.write("### Create a New Account")
        reg_first = st.text_input("First Name:", key="reg_first").strip()
        reg_last = st.text_input("Last Name:", key="reg_last").strip()
        reg_role = st.selectbox("Select Your Role:", ["User / Athlete", "Creator / Coach / Trainer"])
        
        if st.button("Sign Up"):
            full_name = f"{reg_first} {reg_last}".strip()
            if not reg_first or not reg_last:
                st.error("Please provide both your first and last name.")
            else:
                # Check duplication safely
                existing_names = [u["name"] if isinstance(u, dict) else u for u in db["users"]]
                if full_name in existing_names:
                    st.error("An account with this name already exists.")
                else:
                    new_user = {"name": full_name, "role": reg_role}
                    db["users"].append(new_user)
                    if full_name not in db["workouts"]:
                        db["workouts"][full_name] = []
                    save_data(db)
                    st.success(f"Account created successfully for {full_name}! You can now log in.")

# ================= APP WINDOW (LOGGED IN) =================
else:
    # Header bar with sign out option
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("🏋️‍♂️ Workout Manager")
        st.caption(f"Logged in as: **{st.session_state.current_user}** ({st.session_state.current_role})")
    with col_logout:
        st.write("")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.current_role = None
            st.rerun()
            
    st.write("---")

    # Filter out valid athletes for drop-downs
    athlete_list = []
    for u in db["users"]:
        if isinstance(u, dict):
            if u.get("role") == "User / Athlete":
                athlete_list.append(u["name"])
        else:
            athlete_list.append(u) # fallback for legacy data strings

    # ================= COACH PORTAL =================
    if st.session_state.current_role == "Creator / Coach / Trainer" or st.session_state.current_user == "Coach Admin":
        st.header("Coach Workspace")
        
        st.subheader("➕ Assign a Multi-Exercise Workout")
        if athlete_list:
            target_user = st.selectbox("Select Athlete:", athlete_list)
            routine_title = st.text_input("Routine Name (e.g., Upper Body, Leg Day):")
            
            if "temp_exercises" not in st.session_state:
                st.session_state.temp_exercises = []
                
            st.write("#### Add Exercises to this Routine:")
            ex_title = st.text_input("Exercise Name (e.g., Bench Press, Pull Ups):")
            ex_desc = st.text_area("Instructions:")
            
            if st.button("Add Exercise to List"):
                if ex_title.strip():
                    st.session_state.temp_exercises.append({
                        "title": ex_title,
                        "description": ex_desc,
                        "logged": None
                    })
                    st.success(f"Added {ex_title} to list!")
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
                        if target_user not in db["workouts"]:
                            db["workouts"][target_user] = []
                        db["workouts"][target_user].append(new_routine)
                        save_data(db)
                        st.session_state.temp_exercises = []
                        st.success(f"Assigned '{routine_title}' to {target_user}!")
                        st.rerun()
                    else:
                        st.error("Please provide a Routine Name.")
        else:
            st.info("No registered athletes available to assign routines to.")

        st.write("---")
        
        st.subheader("📊 Review Athlete Progress")
        if athlete_list:
            review_user = st.selectbox("View Workouts For:", athlete_list, key="review_user")
            user_routines = db["workouts"].get(review_user, [])
            
            if not user_routines:
                st.info(f"{review_user} has no routines assigned.")
            else:
                for idx, rt in enumerate(user_routines):
                    # Safe check for routine name key to avoid KeyErrors
                    r_name = rt.get("routine_name", "Untitled Routine")
                    with st.expander(f"📋 Routine: {r_name}"):
                        for ex in rt.get("exercises", []):
                            st.write(f"🏋️ **{ex.get('title', 'Unknown Exercise')}**")
                            st.write(f"Instructions: {ex.get('description', '')}")
                            if ex.get("logged") is None:
                                st.info("Status: ⏳ Pending Submission")
                            else:
                                st.success("Status: ✅ Completed")
                                log = ex["logged"]
                                st.table({
                                    "Metric": ["Sets", "Reps", "Weight", "Notes"],
                                    "Submitted": [log.get('sets', 0), log.get('reps', 0), log.get('weight', 0.0), log.get('comment', '')]
                                })
                            st.write("---")
        else:
            st.info("No athlete records found.")

    # ================= ATHLETE PORTAL =================
    else:
        st.header(f"Welcome back, {st.session_state.current_user}!")
        my_routines = db["workouts"].get(st.session_state.current_user, [])
        
        st.subheader("📋 Your Assigned Routines")
        if not my_routines:
            st.info("No workouts assigned to you right now!")
        else:
            for r_idx, rt in enumerate(my_routines):
                r_name = rt.get("routine_name", "Untitled Routine")
                with st.expander(f"🧱 Routine Group: {r_name}"):
                    for e_idx, wk in enumerate(rt.get("exercises", [])):
                        st.write(f"### {wk.get('title', 'Unknown Exercise')}")
                        st.write(f"**Instructions:** {wk.get('description', '')}")
                        
                        if wk.get("logged") is not None:
                            st.success("✅ Logged")
                            st.write(f"- **Sets:** {wk['logged'].get('sets')} | **Reps:** {wk['logged'].get('reps')} | **Weight:** {wk['logged'].get('weight')}")
                            st.write(f"- **Your Comment:** {wk['logged'].get('comment')}")
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
                                db["workouts"][st.session_state.current_user][r_idx]["exercises"][e_idx]["logged"] = {
                                    "sets": sets,
                                    "reps": reps,
                                    "weight": weight,
                                    "comment": comment
                                }
                                save_data(db)
                                st.success("Exercise logged!")
                                st.rerun()
                        st.write("---")
