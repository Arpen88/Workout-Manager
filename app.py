import streamlit as st
import json
import os
import numpy as np
from PIL import Image

# Initialize the text scanner engine
@st.cache_resource
def get_ocr_reader() :
    import easyocr
    return easyocr.Reader(['en'], gpu=False)

DB_FILE = "my_workouts.json"

# Load local saved workouts
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"history": {}}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

st.title("🏋️‍♂️ Simple Workout Tracker")
st.write("Scan your workout sheets, track your progress, and log your sets.")

st.write("---")

# ================= STEP 1: SCAN A NEW SHEET =================
st.header("📸 Step 1: Scan a New Workout Sheet")
uploaded_sheet = st.file_uploader("Upload a photo of your workout paper:", type=["png", "jpg", "jpeg"])

if uploaded_sheet is not None:
    routine_name = st.text_input("Name this workout (e.g., Day 1: Upper Body):", value="My Scanned Workout")
    
    if st.button("⚙️ Scan & Extract Exercises", type="primary"):
        with st.spinner("Reading lines from the paper..."):
            try:
                img = Image.open(uploaded_sheet)
                img_np = np.array(img)
                reader = get_ocr_reader()
                raw_lines = reader.readtext(img_np, detail=0)
                
                # Filter out empty or super short lines
                cleaned_exercises = [line.strip() for line in raw_lines if len(line.strip()) > 3]
                
                if cleaned_exercises:
                    # Save the new routine structure into our history tracking database
                    db["history"][routine_name] = {
                        "date_scanned": "".join(str(st.date_input("Today's Date"))),
                        "exercises": {ex: [] for ex in cleaned_exercises}
                    }
                    save_data(db)
                    st.success(f"🎉 Created '{routine_name}' with {len(cleaned_exercises)} exercises! See it below.")
                    st.rerun()
                else:
                    st.warning("Could not clearly read any text. Try a clearer or brighter photo!")
            except Exception as e:
                st.error(f"Scanner error: {str(e)}")

st.write("---")

# ================= STEP 2: TRACK & LOG WORKOUTS =================
st.header("📋 Step 2: Select & Log Your Workout")

if not db["history"]:
    st.info("No workouts scanned yet. Upload a photo above to get started!")
else:
    # Dropdown selector for all your scanned workouts
    workout_options = list(db["history"].keys())
    selected_workout = st.selectbox("Choose a scanned workout layout:", workout_options)
    
    st.write(f"### Current Routine: {selected_workout}")
    workout_data = db["history"][selected_workout]
    
    # Loop through every single exercise found inside that specific workout dropdown
    for ex_name, logs in workout_data["exercises"].items():
        with st.container():
            st.write(f"#### 🛑 {ex_name}")
            
            # If logs already exist for this exercise, show them nicely
            if logs:
                st.write("**Completed Sets:**")
                for i, set_data in enumerate(logs):
                    st.caption(f"Set {i+1}: {set_data['sets']} sets x {set_data['reps']} reps @ {set_data['weight']} lbs")
            
            # Input boxes to log a brand new set for this exercise
            col1, col2, col3 = st.columns(3)
            with col1:
                sets_input = st.number_input("Sets", min_value=1, max_value=10, step=1, key=f"sets_{selected_workout}_{ex_name}")
            with col2:
                reps_input = st.number_input("Reps", min_value=1, max_value=100, step=1, key=f"reps_{selected_workout}_{ex_name}")
            with col3:
                weight_input = st.number_input("Weight (lbs)", min_value=0.0, step=5.0, key=f"weight_{selected_workout}_{ex_name}")
                
            if st.button("✅ Save Log for this Exercise", key=f"btn_{selected_workout}_{ex_name}"):
                # Add the stats directly to this specific exercise array
                db["history"][selected_workout]["exercises"][ex_name].append({
                    "sets": sets_input,
                    "reps": reps_input,
                    "weight": weight_input
                })
                save_data(db)
                st.success("Set saved!")
                st.rerun()
                
            st.write("---")

    # Clear button to wipe out data if you want to start fresh
    if st.button("🗑️ Delete This Entire Workout Layout", type="secondary"):
        del db["history"][selected_workout]
        save_data(db)
        st.success("Deleted successfully!")
        st.rerun()
