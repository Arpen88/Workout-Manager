import streamlit as st

# Initialize session state to act as a temporary database
if "users" not in st.session_state:
    st.session_state.users = ["Alex", "Jordan", "Taylor"]

if "workouts" not in st.session_state:
    st.session_state.workouts = {
        "Alex": [
            {
                "title": "Squats",
                "description": "Keep your back straight and go to parallel.",
                "logged": None,
            }
        ],
        "Jordan": [],
        "Taylor": [],
    }

st.title("🏋️‍♂️ Workout Manager")
st.caption("Assign, track, and review custom workouts.")
st.write("---")

# 1. Login / Profile Selection Side
st.sidebar.header("🔐 Login Profile")
user_type = st.sidebar.radio("Select Role:", ["Creator / Coach", "User / Athlete"])
user_name = st.sidebar.text_input("Enter Your Name:", value="Coach" if user_type == "Creator / Coach" else "Alex")

if not user_name.strip():
    st.warning("Please enter your name in the sidebar to log in.")
else:
    st.sidebar.success(f"Logged in as {user_name} ({user_type})")

    # ================= CREATOR SIDE =================
    if user_type == "Creator / Coach":
        st.header(f"Welcome, Coach {user_name}!")
        
        # Section A: Assign a New Workout
        st.subheader("➕ Assign a New Workout")
        target_user = st.selectbox("Select Athlete:", st.session_state.users)
        workout_title = st.text_input("Exercise Title (e.g., Bench Press):")
        workout_desc = st.text_area("Exercise Description / Instructions:")
        
        if st.button("Assign Workout"):
            if workout_title.strip() and workout_desc.strip():
                new_workout = {
                    "title": workout_title,
                    "description": workout_desc,
                    "logged": None
                }
                st.session_state.workouts[target_user].append(new_workout)
                st.success(f"Successfully assigned {workout_title} to {target_user}!")
            else:
                st.error("Please fill out both the title and description.")

        st.write("---")
        
        # Section B: Review Athlete Progress
        st.subheader("📊 Review Athlete Progress")
        review_user = st.selectbox("View Workouts For:", st.session_state.users, key="review_user")
        
        user_workouts = st.session_state.workouts.get(review_user, [])
        
        if not user_workouts:
            st.info(f"{review_user} has no workouts assigned yet.")
        else:
            for idx, wk in enumerate(user_workouts):
                with st.expander(f"Exercise {idx+1}: {wk['title']}"):
                    st.write(f"**Instructions:** {wk['description']}")
                    
                    if wk["logged"] is None:
                        st.info("Status: ⏳ Pending (Athlete hasn't logged this yet)")
                    else:
                        st.success("Status: ✅ Completed")
                        log = wk["logged"]
                        st.table({
                            "Metric": ["Sets", "Reps", "Weight", "Athlete Comments"],
                            "Submitted Value": [log['sets'], log['reps'], log['weight'], log['comment']]
                        })

    # ================= USER SIDE =================
    else:
        st.header(f"Welcome back, {user_name}!")
        
        if user_name not in st.session_state.workouts:
            st.session_state.workouts[user_name] = []
            if user_name not in st.session_state.users:
                st.session_state.users.append(user_name)

        my_workouts = st.session_state.workouts[user_name]
        
        st.subheader("📋 Your Assigned Workouts")
        if not my_workouts:
            st.info("No workouts assigned to you right now. Grab a rest day! 🎉")
        else:
            for idx, wk in enumerate(my_workouts):
                with st.expander(f"🏋️ {wk['title']} " + ("(✅ Logged)" if wk["logged"] else "(⏳ To Do)")):
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
                            
                        comment = st.text_input("Add Comments / Notes:", key=f"comment_{idx}")
                        
                        if st.button("Submit Workout Log", key=f"btn_{idx}"):
                            wk["logged"] = {
                                "sets": sets,
                                "reps": reps,
                                "weight": weight,
                                "comment": comment
                            }
                            st.success("Workout logged successfully!")
                            st.rerun()
