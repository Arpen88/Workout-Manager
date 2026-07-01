import streamlit as st
import json
import os
import numpy as np
from datetime import datetime
from PIL import Image

# Dynamic import helper for the OCR scanner
@st.cache_resource
def get_ocr_reader():
    import easyocr
    # Initializes the reader for English language processing
    return easyocr.Reader(['en'], gpu=False)

DB_FILE = "workout_db.json"

def load_data():
    default_structure = {
        "users": [
            {"name": "Anders Schilling", "role": "User / Athlete"},
            {"name": "Anders Coach", "role": "Creator / Coach / Trainer"}
        ],
        "workouts": {
            "Anders Schilling": [
                {
                    "routine_name": "Day 1: Lower Body Power",
                    "due_date": "No Due Date",
                    "exercises": [
                        {"title": "Warm-Up", "description": "3 Rounds of: 10 Bodyweight Squats, 10 Banded Good Mornings, 20-second Plank, 50-foot Bear Crawl.", "video_url": None, "image_data": None, "logged": None},
                        {"title": "A1. Trap Bar Deadlift or Heavy Kettlebell Deadlift", "description": "4 sets x 5 reps. Rest 90 seconds.", "video_url": None, "image_data": None, "logged": None},
                        {"title": "B1. Rear-Foot Elevated Split Squats (Bulgarian Split Squats)", "description": "3 sets x 8 reps per leg.", "video_url": None, "image_data": None, "logged": None},
                        {"title": "B2. Hanging Leg Raises or lying leg raise", "description": "3 sets x 10 reps.", "video_url": None, "image_data": None, "logged": None},
                        {"title": "C1. Kettlebell Swings", "description": "3 sets x 15 reps (Explosive, snapping the hips).", "video_url": None, "image_data": None, "logged": None},
                        {"title": "C2. Single-Leg Calf Raises (Deficit)", "description": "3 sets x 15 reps per leg (Slow down, explosive up to protect the Achilles).", "video_url": None, "image_data": None, "logged": None}
                    ]
                }
            ]
        }
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict) and "users" in data and "workouts" in data:
                    return data
        except:
            pass
    return default_structure

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "current_role" not in st.session_state:
    st.session_state.current_role = None

# Smart Scan transient helper state variables
if "scanned_text" not in st.session_state:
    st.session_state.scanned_text = ""

# ================= WELCOME SCREEN =================
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
            if full_name in [u["name"] if isinstance(u, dict) else u for u in db["users"]]:
                user_record = next((u for u in db["users"] if isinstance(u, dict) and u["name"] == full_name), None)
                st.session_state.logged_in = True
                st.session_state.current_user = full_name
                st.session_state.current_role = user_record.get("role", "User / Athlete") if user_record else "User / Athlete"
                st.rerun()
            else:
                st.error("Profile not found.")
    with tab2:
        st.write("### Create a New Account")
        reg_first = st.text_input("First Name:", key="reg_first").strip()
        reg_last = st.text_input("Last Name:", key="reg_last").strip()
        reg_role = st.selectbox("Select Your Role:", ["User / Athlete", "Creator / Coach / Trainer"])
        if st.button("Sign Up"):
            full_name = f"{reg_first} {reg_last}".strip()
            db["users"].append({"name": full_name, "role": reg_role})
            db["workouts"][full_name] = []
            save_data(db)
            st.success("Account created!")

# ================= MAIN APP REGION =================
else:
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("🏋️‍♂️ Workout Manager")
        st.caption(f"Logged in as: **{st.session_state.current_user}** ({st.session_state.current_role})")
    with col_logout:
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
    st.write("---")
    athlete_list = [u["name"] if isinstance(u, dict) else u for u in db["users"] if not isinstance(u, dict) or u.get("role") == "User / Athlete"]

    # ================= COACH INTERFACE =================
    if st.session_state.current_role == "Creator / Coach / Trainer":
        menu_tab1, menu_tab2, menu_tab3 = st.tabs(["➕ Assign Routine", "✏️ Manage / Delete Workouts", "📊 Athlete Progress Tracker"])
        
        with menu_tab1:
            st.subheader("Assign a Multi-Exercise Workout")
            if athlete_list:
                target_user = st.selectbox("Select Target Athlete:", athlete_list, key="assign_target")
                routine_title = st.text_input("Routine Name (e.g., Upper Body Circuit):")
                
                has_due_date = st.checkbox("Set a specific due date for this routine?", value=False)
                due_date_str = "No Due Date"
                if has_due_date:
                    chosen_date = st.date_input("Target Due Date:")
                    due_date_str = chosen_date.strftime("%B %d, %Y")
                
                st.write("---")
                # --- SMART SCAN MODULE ---
                with st.expander("🧠 Use Smart Scan Tool (Extract text from photo sheet)", expanded=False):
                    st.info("Upload a photo or paper document snippet. The system will extract the text line-by-line.")
                    scan_file = st.file_uploader("Upload Workout Paper Image:", type=["png", "jpg", "jpeg"], key="scanner_upload")
                    
                    if scan_file is not None:
                        if st.button("⚙️ Process Document text"):
                            with st.spinner("Analyzing handwriting/text lines..."):
                                try:
                                    img = Image.open(scan_file)
                                    img_np = np.array(img)
                                    reader = get_ocr_reader()
                                    result = reader.readtext(img_np, detail=0)
                                    if result:
                                        st.session_state.scanned_text = "\n".join(result)
                                        st.success("Text successfully extracted!")
                                    else:
                                        st.warning("No readable alphanumeric text discovered in this frame.")
                                except Exception as e:
                                    st.error(f"Scan module failed: {str(e)}")
                    
                    if st.session_state.scanned_text:
                        st.text_area("Extracted text preview container:", value=st.session_state.scanned_text, height=150, disabled=True)
                        if st.button("Clear Extracted Scan Buffer"):
                            st.session_state.scanned_text = ""
                            st.rerun()
                st.write("---")

                if "temp_exercises" not in st.session_state:
                    st.session_state.temp_exercises = []
                    
                st.write("#### Add Item/Exercise Details:")
                # Populate default values automatically if smart scan contains findings
                ex_title = st.text_input("Exercise Name:", value="" if not st.session_state.scanned_text else "Scanned Workout Section")
                ex_desc = st.text_area("Instructions or Notes:", value=st.session_state.scanned_text)
                ex_video = st.text_input("Demo Video URL (Optional):")
                
                if st.button("Add Exercise Item to Routine"):
                    if ex_title.strip():
                        st.session_state.temp_exercises.append({
                            "title": ex_title, 
                            "description": ex_desc, 
                            "video_url": ex_video.strip() if ex_video.strip() else None,
                            "image_data": None,
                            "logged": None
                        })
                        # Clear scan text state upon success
                        st.session_state.scanned_text = ""
                        st.success(f"Added {ex_title} to routine!")
                        st.rerun()
                
                if st.session_state.temp_exercises:
                    st.write("**Routine Build List:**")
                    for i, ex in enumerate(st.session_state.temp_exercises):
                        st.text(f"  {i+1}. {ex['title']}")
                        
                    if st.button("🚀 Assign Final Routine to Athlete", type="primary"):
                        if routine_title.strip():
                            new_rt = {
                                "routine_name": routine_title, 
                                "due_date": due_date_str,
                                "exercises": st.session_state.temp_exercises
                            }
                            db["workouts"].setdefault(target_user, []).append(new_rt)
                            save_data(db)
                            st.session_state.temp_exercises = []
                            st.success("Routine assigned successfully!")
                            st.rerun()
            else:
                st.info("No registered athletes available.")

        # TAB 2: MANAGE ROUTINES
        with menu_tab2:
            st.subheader("Manage Existing Routines")
            if athlete_list:
                source_athlete = st.selectbox("Select Athlete to Manage:", athlete_list, key="src_athlete")
                routines = db["workouts"].get(source_athlete, [])
                if not routines:
                    st.info(f"{source_athlete} has no assigned routines.")
                else:
                    r_options = [f"{r.get('routine_name', 'Untitled')} ({r.get('due_date', 'No Due Date')})" for r in routines]
                    selected_r_idx = st.selectbox("Select Routine:", range(len(r_options)), format_func=lambda x: r_options[x])
                    selected_routine = routines[selected_r_idx]
                    
                    st.write("---")
                    col_action1, col_action2 = st.columns(2)
                    with col_action1:
                        reassign_target = st.selectbox("Clone Routine to:", athlete_list, key="reassign_tgt")
                        if st.button("➡️ Copy & Assign", use_container_width=True):
                            cloned_routine = json.loads(json.dumps(selected_routine))
                            for ex in cloned_routine.get("exercises", []): ex["logged"] = None
                            db["workouts"].setdefault(reassign_target, []).append(cloned_routine)
                            save_data(db)
                            st.success("Routine copied!")
                            st.rerun()
                    with col_action2:
                        if st.button("🗑️ Delete Full Routine", type="primary", use_container_width=True):
                            db["workouts"][source_athlete].pop(selected_r_idx)
                            save_data(db)
                            st.success("Routine deleted!")
                            st.rerun()
            else:
                st.info("No athlete data available.")

        # TAB 3: ORGANIZED PROGRESS TRACKER
        with menu_tab3:
            st.subheader("📋 Athlete Performance Directory")
            if athlete_list:
                for athlete in athlete_list:
                    with st.expander(f"👤 User: {athlete}"):
                        ath_routines = db["workouts"].get(athlete, [])
                        if not ath_routines:
                            st.info("No routines assigned to this user yet.")
                        else:
                            for rt in ath_routines:
                                d_target = rt.get('due_date', 'No Due Date')
                                st.write(f"#### 📅 Routine: {rt.get('routine_name', 'Untitled')} *(Target: {d_target})*")
                                for ex in rt.get("exercises", []):
                                    st.write(f"- **{ex.get('title')}**")
                                    if ex.get("logged") is None:
                                        st.caption("Status: ⏳ Pending Submission")
                                    else:
                                        log = ex["logged"]
                                        st.success(f"Status: ✅ Completed | Sets: {log.get('sets')} | Reps: {log.get('reps')} | Wt: {log.get('weight')} lbs")
                                st.write("---")

    # ================= ATHLETE INTERFACE =================
    else:
        st.header(f"Welcome back, {st.session_state.current_user}!")
        my_routines = db["workouts"].get(st.session_state.current_user, [])
        st.subheader("📋 Your Assigned Routines")
        if not my_routines:
            st.info("No workouts assigned to you right now!")
        else:
            for r_idx, rt in enumerate(my_routines):
                d_target = rt.get('due_date', 'No Due Date')
                with st.expander(f"🧱 Routine Group: {rt.get('routine_name', 'Untitled')} *(Due: {d_target})*"):
                    for e_idx, wk in enumerate(rt.get("exercises", [])):
                        st.write(f"### {wk.get('title')}")
                        st.write(f"**Instructions:** {wk.get('description')}")
                        
                        if wk.get("video_url"):
                            st.write("**🎥 Exercise Demo Video:**")
                            st.video(wk.get("video_url"))
                        
                        if wk.get("logged") is not None:
                            st.success("✅ Logged")
                            st.write(f"- **Sets:** {wk['logged'].get('sets')} | **Reps:** {wk['logged'].get('reps')} | **Weight:** {wk['logged'].get('weight')}")
                        else:
                            col1, col2, col3 = st.columns(3)
                            with col1: sets = st.number_input("Sets Completed", min_value=0, step=1, key=f"s_{r_idx}_{e_idx}")
                            with col2: reps = st.number_input("Reps per Set", min_value=0, step=1, key=f"r_{r_idx}_{e_idx}")
                            with col3: weight = st.number_input("Weight Used", min_value=0.0, step=2.5, key=f"w_{r_idx}_{e_idx}")
                            comment = st.text_input("Add Comments:", key=f"c_{r_idx}_{e_idx}")
                            
                            if st.button("Submit Exercise Log", key=f"b_{r_idx}_{e_idx}"):
                                db["workouts"][st.session_state.current_user][r_idx]["exercises"][e_idx]["logged"] = {
                                    "sets": sets, "reps": reps, "weight": weight, "comment": comment
                                }
                                save_data(db)
                                st.success("Exercise logged!")
                                st.rerun()
                        st.write("---")
