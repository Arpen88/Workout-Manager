import SwiftUI

// 1. Data Models to hold our structures
struct Workout: Identifiable {
    let id = UUID()
    let title: String
    let description: String
    var loggedData: WorkoutLog? // Nil means not completed yet
}

struct WorkoutLog {
    var sets: String
    var reps: String
    var weight: String
    var comment: String
}

struct UserProfile: Identifiable {
    let id = UUID()
    let name: String
    var workouts: [Workout]
}

// 2. Main App View
struct ContentView: View {
    // Fake database setup
    @State private var athletes = [
        UserProfile(name: "Alex", workouts: [Workout(title: "Squats", description: "Keep your back straight. Go low!")]),
        UserProfile(name: "Jordan", workouts: []),
        UserProfile(name: "Taylor", workouts: [])
    ]
    
    @State private var isCreatorMode = true
    @State private var selectedAthleteIndex = 0
    
    // Creator inputs
    @State private var newTitle = ""
    @State private var newDescription = ""
    
    // User inputs
    @State private var userSets = ""
    @State private var userReps = ""
    @State private var userWeight = ""
    @State private var userComment = ""

    var body: some View {
        NavigationView {
            VStyle {
                // Role Toggle Switch
                Picker("Role", selection: $isCreatorMode) {
                    Text("Coach / Creator").tag(true)
                    Text("Athlete / User").tag(false)
                }
                .pickerStyle(.segmented)
                .padding()

                if isCreatorMode {
                    // ================= CREATOR SIDE =================
                    Form {
                        Section(header: Text("Assign New Workout")) {
                            Picker("Select Athlete", selection: $selectedAthleteIndex) {
                                ForEach(0..<athletes.count, id: \.self) { index in
                                    Text(athletes[index].name).tag(index)
                                }
                            }
                            TextField("Exercise Title", text: $newTitle)
                            TextField("Instructions / Description", text: $newDescription)
                            
                            Button("Assign Workout") {
                                if !newTitle.isEmpty && !newDescription.isEmpty {
                                    let newWorkout = Workout(title: newTitle, description: newDescription)
                                    athletes[selectedAthleteIndex].workouts.append(newWorkout)
                                    // Reset inputs
                                    newTitle = ""
                                    newDescription = ""
                                }
                            }
                            .disabled(newTitle.isEmpty || newDescription.isEmpty)
                        }
                        
                        Section(header: Text("Review Athlete Progress")) {
                            ForEach(athletes) { athlete in
                                DisclosureGroup(athlete.name) {
                                    if athlete.workouts.isEmpty {
                                        Text("No workouts assigned.").font(.caption).foregroundColor(.gray)
                                    }
                                    ForEach(athlete.workouts) { wk in
                                        VStack(alignment: .leading, spacing: 5) {
                                            Text(wk.title).font(.headline)
                                            Text(wk.description).font(.subheadline).foregroundColor(.gray)
                                            
                                            if let log = wk.loggedData {
                                                Text("✅ Logged: \(log.sets) sets x \(log.reps) reps @ \(log.weight) lbs").font(.caption).foregroundColor(.green)
                                                Text("Comment: \(log.comment)").font(.caption).italic()
                                            } else {
                                                Text("⏳ Pending athlete submission").font(.caption).foregroundColor(.orange)
                                            }
                                        }
                                        .padding(.vertical, 4)
                                    }
                                }
                            }
                        }
                    }
                } else {
                    // ================= USER SIDE =================
                    // For preview simulation, we assume the user is whoever is selected in the Picker
                    let activeAthlete = athletes[selectedAthleteIndex]
                    
                    VStack(alignment: .leading) {
                        Text("Welcome back, \(activeAthlete.name)!").font(.title2).bold().padding(.horizontal)
                        
                        List {
                            if activeAthlete.workouts.isEmpty {
                                Text("No workouts assigned to you! 🎉")
                            }
                            
                            ForEach(0..<athletes[selectedAthleteIndex].workouts.count, id: \.self) { wIdx in
                                let workout = athletes[selectedAthleteIndex].workouts[wIdx]
                                
                                VStack(alignment: .leading, spacing: 10) {
                                    Text(workout.title).font(.headline)
                                    Text(workout.description).font(.subheadline).foregroundColor(.gray)
                                    
                                    if let log = workout.loggedData {
                                        Text("Logged: \(log.sets) sets x \(log.reps) reps @ \(log.weight) lbs").foregroundColor(.green)
                                    } else {
                                        // 3 Input boxes + Comment Box
                                        HStack {
                                            TextField("Sets", text: $userSets).keyboardType(.numberPad).textFieldStyle(.roundedBorder)
                                            TextField("Reps", text: $userReps).keyboardType(.numberPad).textFieldStyle(.roundedBorder)
                                            TextField("Weight", text: $userWeight).keyboardType(.decimalPad).textFieldStyle(.roundedBorder)
                                        }
                                        TextField("Add comments...", text: $userComment).textFieldStyle(.roundedBorder)
                                        
                                        Button("Submit Log") {
                                            let newLog = WorkoutLog(sets: userSets, reps: userReps, weight: userWeight, comment: userComment)
                                            athletes[selectedAthleteIndex].workouts[wIdx].loggedData = newLog
                                            // Reset active inputs
                                            userSets = ""
                                            userReps = ""
                                            userWeight = ""
                                            userComment = ""
                                        }
                                        .buttonStyle(.borderedProminent)
                                    }
                                }
                                .padding(.vertical, 5)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Workout Manager")
        }
    }
}

// Helper wrapper to cleanly layout views vertically
struct VStyle<Content: View>: View {
    let content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some View { VStack { content } }
}