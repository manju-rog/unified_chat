// Application configuration data
export const seedData = {
  // Note: Employee data is now loaded from the backend API

  // Company structure data
  departments: ["Development", "Quality Assurance", "Design", "Human Resources", "Management"],
  locations: ["Bengaluru", "Chennai", "Mumbai", "Hyderabad"],
  roles: ["Senior Developer", "QA Lead", "Tech Lead", "Engineering Manager", "UI Designer", "HR Manager", "Full Stack Developer", "QA Engineer"],
  
  // Absence status types
  absenceTypes: {
    "P": { 
      label: "Present",
      color: "#10b981",
      icon: "check_circle"
    },
    "A": { 
      label: "Absent", 
      color: "#ef4444",
      icon: "cancel" 
    },
    "V": { 
      label: "Vacation", 
      color: "#3b82f6",
      icon: "beach_access" 
    }
  },
};