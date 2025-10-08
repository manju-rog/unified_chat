# 🚀 Complete Beginner's Guide to Deploy AI Absence & SOW System



## ⚠️ **IMPORTANT: Read This First!**

**Why are we doing this step by step?**
- Each step builds on the previous one
- If you skip steps, things will break
- If something goes wrong, you'll know exactly where
- This prevents hours of debugging later

**What if something goes wrong?**
- Don't panic! Every error has a solution
- Read the error message carefully
- Check the "Common Problems" section for each step
- Ask for help if you're stuck

**Time needed:**
- First time: 2-3 hours (with breaks)
- After you know it: 15 minutes
--
-

## 📋 **Before We Start: Check Your Computer**

### **Step 1: Check Your Ubuntu Version**

**Why do this?** Different Ubuntu versions need different commands. We need to know which one you have.

**What to do:**
```bash
lsb_release -a
```

**Copy this command exactly, paste it in terminal, press Enter**

**What you should see:**
```
Distributor ID: Ubuntu
Description:    Ubuntu 20.04.6 LTS
Release:        20.04
Codename:       focal
```

**✅ Good if you see:** Ubuntu 18.04, 20.04, 22.04, or newer  
**❌ Problem if you see:** Ubuntu 16.04 or older  

**If you have problems:**
- **Error "command not found"**: You might not be on Ubuntu. Try: `cat /etc/os-release`
- **Very old version**: Ask Venkat if you can upgrade or use a different computer

### **Step 2: Check Available Space**

**Why do this?** Our system needs space to store code, databases, and Docker images.

**What to do:**
```bash
df -h
```

**What you should see:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   15G   32G  32% /
```

**✅ Good if you see:** At least 20GB available (Avail column)  
**❌ Problem if you see:** Less than 10GB available  

**If you have problems:**
- **Not enough space**: Clean up files or ask for a bigger disk
- **Command not working**: Try `du -sh ~` to check your home folder

### **Step 3: Check Internet Connection**

**Why do this?** We need to download lots of software and code.

**What to do:**
```bash
ping -c 3 google.com
```

**What you should see:**
```
PING google.com (142.250.191.14) 56(84) bytes of data.
64 bytes from google.com: icmp_seq=1 ttl=117 time=23.4 ms
64 bytes from google.com: icmp_seq=2 ttl=117 time=24.1 ms
64 bytes from google.com: icmp_seq=3 ttl=117 time=22.8 ms
```

**✅ Good if you see:** Numbers and "time=" messages  
**❌ Problem if you see:** "Network is unreachable" or "Name or service not known"  

**If you have problems:**
- **No internet**: Check your WiFi/ethernet connection
- **Slow internet**: This will work but downloads will take longer
-
--

## 🔧 **Phase 1: Install Required Software**

**Why do we need to install software?** Think of it like cooking - you need the right tools before you can make a meal. Each tool has a specific job.

### **Step 4: Update Your System (Very Important!)**

**Why do this?** This gets the latest security updates and makes sure other installations work properly.

**What to do:**
```bash
sudo apt update
```

**What this command means:**
- `sudo` = "Do this as administrator" (like being the boss)
- `apt` = "Package manager" (like an app store for Ubuntu)
- `update` = "Get the latest list of available software"

**What you should see:**
```
Hit:1 http://archive.ubuntu.com/ubuntu focal InRelease
Get:2 http://archive.ubuntu.com/ubuntu focal-updates InRelease [114 kB]
...
Reading package lists... Done
```

**✅ Good if you see:** Lots of "Hit" and "Get" messages, ends with "Done"  
**❌ Problem if you see:** "Permission denied" or "Could not get lock"  

**If you have problems:**
- **"Permission denied"**: Make sure you typed `sudo` at the beginning
- **"Could not get lock"**: Another update is running. Wait 5 minutes and try again
- **Password prompt**: Type your Ubuntu password (you won't see the letters as you type)

**Now upgrade the system:**
```bash
sudo apt upgrade -y
```

**What this does:** Actually installs the updates (like clicking "Install Updates")

**This might take 5-15 minutes. You'll see lots of text. This is normal!**

**✅ Good if you see:** Ends with something like "Processing triggers..." and returns to command prompt  
**❌ Problem if you see:** "E: " followed by error messages  

### **Step 5: Install Docker (The Container System)**

**Why do we need Docker?** Docker is like having multiple computers inside your computer. Each part of our system runs in its own "container" so they don't interfere with each other.

**What to do:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
```

**What this command means:**
- `curl` = "Download a file from the internet"
- `-fsSL` = "Download quietly and follow redirects"
- `https://get.docker.com` = "The website with Docker installer"
- `-o get-docker.sh` = "Save it as a file called get-docker.sh"

**What you should see:**
```
(Nothing visible, but the command completes)
```

**✅ Good if you see:** Command finishes and you get a new prompt  
**❌ Problem if you see:** "curl: command not found" or "Failed to connect"  

**If you have problems:**
- **"curl: command not found"**: Install curl first: `sudo apt install curl`
- **"Failed to connect"**: Check your internet connection

**Now run the installer:**
```bash
sudo sh get-docker.sh
```

**What this does:** Runs the Docker installation script

**This will take 2-5 minutes and show lots of text. This is normal!**

**What you should see at the end:**
```
================================================================================

To run Docker as a non-privileged user, consider adding your user to the "docker" group with a command like:

  sudo usermod -aG docker your-username

Remember to log out and back in for this to take effect!
```

**✅ Good if you see:** Message about adding user to docker group  
**❌ Problem if you see:** "E: " error messages or "Installation failed"  

**If you have problems:**
- **Installation failed**: Try running `sudo apt update` again and retry
- **Permission errors**: Make sure you used `sudo`### **St
ep 6: Add Yourself to Docker Group (Critical!)**

**Why do this?** By default, only the administrator can use Docker. This lets your regular user account use Docker without typing `sudo` every time.

**What to do:**
```bash
sudo usermod -aG docker $USER
```

**What this command means:**
- `sudo` = "Do this as administrator"
- `usermod` = "Modify user account"
- `-aG docker` = "Add to group called 'docker'"
- `$USER` = "Your current username"

**What you should see:**
```
(Nothing visible, but the command completes)
```

**✅ Good if you see:** Command finishes silently  
**❌ Problem if you see:** "usermod: user 'username' does not exist"  

**IMPORTANT: You MUST log out and log back in now!**

**Why?** Ubuntu needs to refresh your permissions. Until you do this, Docker won't work.

**How to log out and back in:**
1. Click the power button icon in top-right corner
2. Click "Log Out"
3. Log back in with your username and password

**After logging back in, test Docker:**
```bash
docker --version
```

**What you should see:**
```
Docker version 24.0.7, build afdd53b
```

**✅ Good if you see:** "Docker version" followed by numbers  
**❌ Problem if you see:** "docker: command not found" or "permission denied"  

**If you have problems:**
- **"command not found"**: Docker didn't install properly. Go back to Step 5
- **"permission denied"**: You didn't log out and back in. Do that now
- **Still not working**: Try `sudo docker --version`. If that works, the group addition didn't work

**Test Docker is really working:**
```bash
docker run hello-world
```

**What this does:** Downloads and runs a tiny test program

**What you should see:**
```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
...
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

**✅ Good if you see:** "Hello from Docker!" message  
**❌ Problem if you see:** "permission denied" or "Cannot connect to Docker daemon"  

**If you have problems:**
- **"permission denied"**: The group addition didn't work. Try: `sudo usermod -aG docker $USER` and log out/in again
- **"Cannot connect"**: Docker service isn't running. Try: `sudo systemctl start docker`##
# **Step 7: Install Docker Compose (The Orchestrator)**

**Why do we need Docker Compose?** Docker runs one container at a time. Docker Compose lets us run multiple containers together (like our website, brain, database manager, and database all at once).

**What to do:**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

**What this command means:**
- `sudo` = "Do this as administrator"
- `curl -L` = "Download file and follow redirects"
- `$(uname -s)-$(uname -m)` = "Automatically detect your system type"
- `-o /usr/local/bin/docker-compose` = "Save it in the system programs folder"

**This downloads a file. You won't see much output.**

**✅ Good if you see:** Command completes without errors  
**❌ Problem if you see:** "curl: command not found" or "Permission denied"  

**Make it executable:**
```bash
sudo chmod +x /usr/local/bin/docker-compose
```

**What this does:** Tells Ubuntu this file is a program that can be run

**Test Docker Compose:**
```bash
docker-compose --version
```

**What you should see:**
```
Docker Compose version v2.21.0
```

**✅ Good if you see:** "Docker Compose version" followed by numbers  
**❌ Problem if you see:** "command not found"  

**If you have problems:**
- **"command not found"**: The download or chmod didn't work. Try the commands again
- **Old version**: That's okay as long as it's version 1.25 or newer

### **Step 8: Install Git (Code Download Tool)**

**Why do we need Git?** Git downloads code from GitHub (like downloading a ZIP file, but smarter).

**What to do:**
```bash
sudo apt install -y git
```

**What this does:** Installs Git from Ubuntu's software repository

**What you should see:**
```
Reading package lists... Done
Building dependency tree       
...
Setting up git (1:2.25.1-1ubuntu3.11) ...
```

**Test Git:**
```bash
git --version
```

**What you should see:**
```
git version 2.25.1
```

**✅ Good if you see:** "git version" followed by numbers  
**❌ Problem if you see:** "command not found"  

### **Step 9: Install Node.js (JavaScript Runtime)**

**Why do we need Node.js?** Our website is built with React (JavaScript). Node.js lets us build and run JavaScript programs.

**What to do:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
```

**What this does:** Adds Node.js 18 to Ubuntu's software list

**You'll see lots of text. This is normal!**

**Now install Node.js:**
```bash
sudo apt install -y nodejs
```

**Test Node.js:**
```bash
node --version
npm --version
```

**What you should see:**
```
v18.18.2
9.8.1
```

**✅ Good if you see:** Version numbers for both node and npm  
**❌ Problem if you see:** "command not found" for either  

**If you have problems:**
- **"command not found"**: The installation failed. Try the curl command again##
# **Step 10: Install Python (Programming Language)**

**Why do we need Python?** Our AI brain is written in Python. We need Python to run it.

**What to do:**
```bash
sudo apt install -y python3 python3-pip python3-venv
```

**What this installs:**
- `python3` = The Python programming language
- `python3-pip` = Tool to install Python packages
- `python3-venv` = Tool to create isolated Python environments

**Test Python:**
```bash
python3 --version
pip3 --version
```

**What you should see:**
```
Python 3.8.10
pip 20.0.2 from /usr/lib/python3/dist-packages/pip (python 3.8)
```

**✅ Good if you see:** Version numbers for both python3 and pip3  
**❌ Problem if you see:** "command not found" for either  

### **Step 11: Install Java (Programming Language)**

**Why do we need Java?** Our database manager is written in Java (Spring Boot). We need Java to run it.

**What to do:**
```bash
sudo apt install -y openjdk-17-jdk maven
```

**What this installs:**
- `openjdk-17-jdk` = Java Development Kit version 17
- `maven` = Tool to build Java programs

**This might take 5-10 minutes to download and install.**

**Test Java:**
```bash
java -version
mvn --version
```

**What you should see:**
```
openjdk version "17.0.8" 2023-07-18
OpenJDK Runtime Environment (build 17.0.8+7-Ubuntu-1ubuntu2.20.04)
...

Apache Maven 3.6.3
Maven home: /usr/share/maven
Java version: 17.0.8, vendor: Private Build
```

**✅ Good if you see:** Version information for both java and mvn  
**❌ Problem if you see:** "command not found" for either  

---

## 🎉 **Checkpoint 1: All Software Installed!**

**Let's verify everything is working:**

```bash
echo "=== Checking all installations ==="
docker --version
docker-compose --version
git --version
node --version
npm --version
python3 --version
pip3 --version
java -version
mvn --version
echo "=== All checks complete ==="
```

**✅ You're ready for the next phase if:** All commands show version numbers  
**❌ Go back and fix if:** Any command shows "command not found"  

**If everything works, take a 10-minute break! You've done the hard part.**---

#
# 📁 **Phase 2: Get the Code**

### **Step 12: Create a Workspace Folder**

**Why do this?** We need a clean, organized place to put our code. Think of it like creating a folder for a school project.

**What to do:**
```bash
mkdir -p ~/workspace
cd ~/workspace
pwd
```

**What these commands mean:**
- `mkdir -p ~/workspace` = "Create a folder called 'workspace' in my home directory"
- `cd ~/workspace` = "Go into that folder"
- `pwd` = "Show me where I am now"

**What you should see:**
```
/home/your-username/workspace
```

**✅ Good if you see:** A path ending with "/workspace"  
**❌ Problem if you see:** "Permission denied" or different path  

**If you have problems:**
- **"Permission denied"**: You don't have permission to create folders in your home directory (very unusual)
- **Different path**: That's okay as long as it ends with "workspace"

### **Step 13: Download the Code from GitHub**

**Why do this?** All our code is stored on GitHub (like Google Drive for programmers). We need to download it to our computer.

**What to do:**
```bash
git clone https://github.com/manju-rog/unified_chat.git
```

**What this command means:**
- `git clone` = "Download a complete copy of a project"
- `https://github.com/manju-rog/unified_chat.git` = "The location of our project"

**What you should see:**
```
Cloning into 'unified_chat'...
remote: Enumerating objects: 1234, done.
remote: Counting objects: 100% (1234/1234), done.
remote: Compressing objects: 100% (567/567), done.
remote: Total 1234 (delta 890), reused 1123 (delta 789), pack-reused 0
Receiving objects: 100% (1234/1234), 2.34 MiB | 1.23 MiB/s, done.
Resolving deltas: 100% (890/890), done.
```

**This downloads about 50-100 MB of code. It might take 1-5 minutes depending on your internet.**

**✅ Good if you see:** "Cloning into 'unified_chat'..." and progress messages  
**❌ Problem if you see:** "fatal: repository not found" or "Permission denied"  

**If you have problems:**
- **"repository not found"**: Check your internet connection and try again
- **"Permission denied"**: The repository might be private (ask Venkat)
- **Very slow**: Your internet is slow, but it will work

**Go into the downloaded folder:**
```bash
cd unified_chat
pwd
```

**What you should see:**
```
/home/your-username/workspace/unified_chat
```

**Look at what we downloaded:**
```bash
ls -la
```

**What you should see:**
```
total 123
drwxrwxr-x  8 user user  4096 Nov 15 10:30 .
drwxrwxr-x  3 user user  4096 Nov 15 10:29 ..
drwxrwxr-x  8 user user  4096 Nov 15 10:30 .git
-rw-rw-r--  1 user user  1234 Nov 15 10:30 README.md
drwxrwxr-x  3 user user  4096 Nov 15 10:30 ai_absence-ai_absence_mi
drwxrwxr-x  4 user user  4096 Nov 15 10:30 docker
drwxrwxr-x  3 user user  4096 Nov 15 10:30 k8s
drwxrwxr-x  2 user user  4096 Nov 15 10:30 scripts
drwxrwxr-x  3 user user  4096 Nov 15 10:30 unified_ai_chat
...
```

**✅ Good if you see:** Folders like "unified_ai_chat", "docker", "ai_absence-ai_absence_mi"  
**❌ Problem if you see:** "No such file or directory" or empty folder  

### **Step 14: Switch to the Right Version**

**Why do this?** Our code has different versions (like different drafts of a document). We need the "production-deployment" version which has all the latest features.

**What to do:**
```bash
git checkout production-deployment
```

**What you should see:**
```
Branch 'production-deployment' set up to track remote branch 'production-deployment' from 'origin'.
Switched to a new local branch 'production-deployment'
```

**✅ Good if you see:** "Switched to" message  
**❌ Problem if you see:** "error: pathspec 'production-deployment' did not match"  

**If you have problems:**
- **Branch not found**: Try `git branch -a` to see all available branches
- **Still problems**: Use the main branch: `git checkout main`

**Verify you're on the right branch:**
```bash
git branch
```

**What you should see:**
```
* production-deployment
```

**The * shows which branch you're currently on.**---


## 🔑 **Phase 3: Set Up Configuration**

### **Step 15: Get Your Google Gemini API Key**

**Why do we need this?** Our AI brain uses Google's Gemini AI to understand and respond to users. We need a key to access it (like a password).

**How to get the API key:**

1. **Open your web browser** and go to: https://makersuite.google.com/app/apikey

2. **Sign in with your Google account** (use your personal Gmail or company Google account)

3. **Click "Create API Key"**

4. **Copy the key** - it looks like: `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**⚠️ IMPORTANT:** 
- **Keep this key secret!** Don't share it with anyone
- **Don't put it in public places** like chat messages or emails
- **Write it down somewhere safe** - you'll need it multiple times

**If you can't get an API key:**
- Ask Venkat for help
- You might need to use a company Google account
- There might be billing setup required (usually free for testing)

### **Step 16: Create Configuration File**

**Why do this?** Our system needs to know how to connect to the database, where to find the AI, and other settings. We put all these settings in one file.

**What to do:**
```bash
cd ~/workspace/unified_chat
ls -la sow_gen_ai/
```

**Look for a file called `.env` or `.env.example`:**

**If you see `.env.example`:**
```bash
cp sow_gen_ai/.env.example sow_gen_ai/.env
```

**If you don't see either file, create one:**
```bash
touch sow_gen_ai/.env
```

**Now edit the configuration file:**
```bash
nano sow_gen_ai/.env
```

**What nano is:** A simple text editor that works in the terminal (like Notepad but in the command line)

**In the nano editor, type exactly this:**
```bash
# Google Gemini API Key (replace with your actual key)
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Database Configuration (we'll use PostgreSQL in Docker)
DATABASE_URL=postgresql://ai_absence:ai_absence_password@localhost:5432/ai_absence_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_absence_db
DB_USERNAME=ai_absence
DB_PASSWORD=ai_absence_password

# API URLs (for local development)
REACT_APP_API_URL=http://localhost:5002
REACT_APP_ABSENCE_API_URL=http://localhost:8080

# Application Settings
APP_ENV=development
LOG_LEVEL=DEBUG
```

**⚠️ CRITICAL:** Replace `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` with your actual API key!

**How to use nano:**
- **Type normally** to add text
- **Use arrow keys** to move around
- **Ctrl+X** to exit
- **Y** to save changes
- **Enter** to confirm the filename

**After saving, verify the file:**
```bash
cat sow_gen_ai/.env
```

**What you should see:**
```
GEMINI_API_KEY=AIzaSyB... (your actual key)
DATABASE_URL=postgresql://ai_absence:ai_absence_password@localhost:5432/ai_absence_db
...
```

**✅ Good if you see:** Your actual API key and all the settings  
**❌ Problem if you see:** "No such file" or empty file  

**If you have problems:**
- **File not created**: Try the `touch` and `nano` commands again
- **Can't use nano**: Try `gedit sow_gen_ai/.env` (opens a graphical editor)
- **Lost your API key**: Go back to the Google website and create a new one---


## 🗄️ **Phase 4: Set Up the Database**

**Why do we need a database?** Think of a database like a filing cabinet that stores all information about employees, their vacation requests, and work documents. Our system needs somewhere to remember things.

### **Step 17: Create Docker Compose File for Database**

**Why use Docker for database?** Instead of installing PostgreSQL directly on your computer (which can be complicated), we'll run it in a Docker container. It's like having a separate computer just for the database.

**What to do:**
```bash
cd ~/workspace/unified_chat
nano docker-compose-database.yml
```

**In nano, type exactly this:**
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:13
    container_name: ai-absence-postgres
    environment:
      POSTGRES_DB: ai_absence_db
      POSTGRES_USER: ai_absence
      POSTGRES_PASSWORD: ai_absence_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database-init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_absence -d ai_absence_db"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
    driver: local
```

**What this file means:**
- `postgres:13` = Use PostgreSQL version 13
- `ports: "5432:5432"` = Make database accessible on port 5432
- `volumes` = Store database data permanently (won't lose data when container stops)
- `healthcheck` = Automatically check if database is working

**Save the file** (Ctrl+X, Y, Enter)

### **Step 18: Create Database Initialization Script**

**Why do this?** When the database starts for the first time, it's empty. We need to create tables to store employee data, vacation requests, etc.

**What to do:**
```bash
nano database-init.sql
```

**In nano, type exactly this:**
```sql
-- AI Absence & SOW System Database Schema

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    department VARCHAR(100),
    position VARCHAR(100),
    hire_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create absence_requests table
CREATE TABLE IF NOT EXISTS absence_requests (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    absence_type VARCHAR(50) NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by INTEGER REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sow_requests table
CREATE TABLE IF NOT EXISTS sow_requests (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    employee_id INTEGER REFERENCES employees(id),
    session_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample employees
INSERT INTO employees (name, email, department, position, hire_date) VALUES
('John Doe', 'john.doe@company.com', 'Engineering', 'Senior Developer', '2022-01-15'),
('Jane Smith', 'jane.smith@company.com', 'Engineering', 'Product Manager', '2021-06-01'),
('Mike Johnson', 'mike.johnson@company.com', 'HR', 'HR Manager', '2020-03-10'),
('Sarah Wilson', 'sarah.wilson@company.com', 'Engineering', 'DevOps Engineer', '2022-08-20'),
('David Brown', 'david.brown@company.com', 'Finance', 'Financial Analyst', '2021-11-05')
ON CONFLICT (email) DO NOTHING;

-- Insert sample absence requests
INSERT INTO absence_requests (employee_id, start_date, end_date, absence_type, reason, status) VALUES
(1, '2024-02-15', '2024-02-16', 'vacation', 'Family vacation', 'approved'),
(2, '2024-02-20', '2024-02-20', 'sick', 'Medical appointment', 'pending'),
(3, '2024-03-01', '2024-03-05', 'vacation', 'Spring break', 'approved')
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_absence_requests_employee_id ON absence_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_absence_requests_dates ON absence_requests(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_sow_requests_employee_id ON sow_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
```

**What this script does:**
- Creates tables for employees, vacation requests, work documents, and chat sessions
- Adds some sample data so you can test the system
- Creates indexes to make database queries faster

**Save the file** (Ctrl+X, Y, Enter)

### **Step 19: Start the Database**

**What to do:**
```bash
docker-compose -f docker-compose-database.yml up -d
```

**What this command means:**
- `docker-compose` = Run multiple Docker containers together
- `-f docker-compose-database.yml` = Use this specific configuration file
- `up` = Start the containers
- `-d` = Run in background (detached mode)

**What you should see:**
```
Creating network "unified_chat_default" with the default driver
Creating volume "unified_chat_postgres_data" with local driver
Pulling postgres (postgres:13)...
13: Pulling from library/postgres
...
Creating ai-absence-postgres ... done
```

**This downloads PostgreSQL (about 100MB) and starts it. First time takes 2-5 minutes.**

**Check if database is running:**
```bash
docker ps
```

**What you should see:**
```
CONTAINER ID   IMAGE         COMMAND                  CREATED         STATUS                   PORTS                    NAMES
abc123def456   postgres:13   "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:5432->5432/tcp   ai-absence-postgres
```

**✅ Good if you see:** Container with "postgres:13" and status "Up" and "(healthy)"  
**❌ Problem if you see:** No containers, or status "Exited" or "Restarting"  

**If you have problems:**
- **No containers**: The docker-compose command failed. Check for typos in the YAML file
- **Container exited**: Check logs: `docker-compose -f docker-compose-database.yml logs`
- **Port already in use**: Something else is using port 5432. Try `sudo netstat -tulpn | grep 5432`

**Test database connection:**
```bash
docker exec -it ai-absence-postgres psql -U ai_absence -d ai_absence_db -c "SELECT COUNT(*) FROM employees;"
```

**What you should see:**
```
 count 
-------
     5
(1 row)
```

**✅ Good if you see:** "count" with number 5 (the sample employees we added)  
**❌ Problem if you see:** "psql: error" or "connection refused"  

**If database connection fails:**
- Wait 2-3 minutes for database to fully start
- Check container logs: `docker logs ai-absence-postgres`
- Make sure container is healthy: `docker ps` should show "(healthy)"-
--

## 🎉 **Checkpoint 2: Database is Ready!**

**Let's verify the database is working properly:**

```bash
echo "=== Database Status Check ==="
docker ps --filter "name=ai-absence-postgres"
echo ""
echo "=== Testing Database Connection ==="
docker exec -it ai-absence-postgres psql -U ai_absence -d ai_absence_db -c "\dt"
echo ""
echo "=== Sample Data Check ==="
docker exec -it ai-absence-postgres psql -U ai_absence -d ai_absence_db -c "SELECT name, email FROM employees LIMIT 3;"
echo "=== Database checks complete ==="
```

**✅ You're ready for the next phase if:** 
- Container shows "Up" and "(healthy)"
- You see table names like "employees", "absence_requests"
- You see sample employee data

**❌ Go back and fix if:** 
- No container running
- Connection errors
- No tables or data

**If everything works, take another break! The hardest parts are done.**

---

## 🏗️ **Phase 5: Build and Run the Applications**

**Now we'll build and start all parts of our system. Think of this like assembling a car - we have all the parts, now we put them together.**

### **Step 20: Build the Backend (Python AI Brain)**

**Why build the backend first?** The backend is the brain of our system. It talks to the AI and manages everything. We need it working before the website can function.

**What to do:**
```bash
cd ~/workspace/unified_chat/unified_ai_chat/backend
pwd
```

**Make sure you're in the right place:**
```
/home/your-username/workspace/unified_chat/unified_ai_chat/backend
```

**Look at what's in this folder:**
```bash
ls -la
```

**You should see:**
```
app/                 (the Python code)
requirements.txt     (list of needed Python packages)
Dockerfile          (instructions to build Docker container)
```

**Create a Python virtual environment:**
```bash
python3 -m venv venv
```

**What this does:** Creates an isolated Python environment so our project doesn't interfere with other Python programs on your computer.

**Activate the virtual environment:**
```bash
source venv/bin/activate
```

**What you should see:** Your command prompt changes to show `(venv)` at the beginning:
```
(venv) user@computer:~/workspace/unified_chat/unified_ai_chat/backend$
```

**✅ Good if you see:** `(venv)` at the start of your prompt  
**❌ Problem if you see:** No change in prompt  

**If activation didn't work:**
- Make sure you're in the backend directory
- Try: `ls venv/bin/activate` to see if the file exists
- If file doesn't exist, the `python3 -m venv venv` command failed

**Install Python packages:**
```bash
pip install -r requirements.txt
```

**What this does:** Downloads and installs all the Python libraries our backend needs (like FastAPI, database connectors, AI libraries).

**This will download 50-100 packages and take 2-5 minutes. You'll see lots of text like:**
```
Collecting fastapi==0.111.0
  Downloading fastapi-0.111.0-py3-none-any.whl (91 kB)
Collecting uvicorn[standard]==0.30.0
  Downloading uvicorn-0.30.0-py3-none-any.whl (62 kB)
...
Successfully installed fastapi-0.111.0 uvicorn-0.30.0 ...
```

**✅ Good if you see:** "Successfully installed" at the end with many package names  
**❌ Problem if you see:** "ERROR" messages or "Failed building wheel"  

**If installation fails:**
- **Permission errors**: Make sure virtual environment is activated (you should see `(venv)`)
- **Network errors**: Check internet connection
- **Build errors**: Try: `sudo apt install python3-dev build-essential`

**Test the backend installation:**
```bash
python -c "import fastapi; print('FastAPI installed successfully')"
```

**What you should see:**
```
FastAPI installed successfully
```

**Start the backend server:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
```

**What this command means:**
- `python -m uvicorn` = Run the Uvicorn web server
- `app.main:app` = Load our application from app/main.py
- `--host 0.0.0.0` = Accept connections from anywhere
- `--port 5002` = Use port 5002
- `--reload` = Automatically restart if code changes

**What you should see:**
```
INFO:     Will watch for changes in these directories: ['/home/user/workspace/unified_chat/unified_ai_chat/backend']
INFO:     Uvicorn running on http://0.0.0.0:5002 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Good if you see:** "Application startup complete" and no error messages  
**❌ Problem if you see:** "ERROR" messages or server crashes  

**Common problems and solutions:**
- **"Port 5002 already in use"**: Something else is using that port. Try `sudo netstat -tulpn | grep 5002` to see what
- **"Database connection failed"**: Make sure the PostgreSQL container is running: `docker ps`
- **"GEMINI_API_KEY not found"**: Check your .env file has the correct API key

**Test the backend is working:**
Open a new terminal (keep the backend running in the first one) and run:
```bash
curl http://localhost:5002/api/health
```

**What you should see:**
```json
{"status":"healthy","timestamp":"2024-01-15T10:30:00Z","version":"1.0.0"}
```

**✅ Good if you see:** JSON response with "status":"healthy"  
**❌ Problem if you see:** "Connection refused" or error messages  

**Also test in your web browser:** Go to http://localhost:5002/docs

**You should see:** A web page with "FastAPI" and API documentation

**✅ Good if you see:** API documentation page loads  
**❌ Problem if you see:** "This site can't be reached" or error page### 
**Step 21: Build the Absence Service (Java Database Manager)**

**Why do we need this?** This service manages all employee data and vacation requests. It's written in Java and connects to our PostgreSQL database.

**Open a new terminal** (keep the backend running in the previous terminal)

**What to do:**
```bash
cd ~/workspace/unified_chat/ai_absence-ai_absence_mi/backend/absence-management
pwd
```

**Make sure you're in the right place:**
```
/home/your-username/workspace/unified_chat/ai_absence-ai_absence_mi/backend/absence-management
```

**Look at what's in this folder:**
```bash
ls -la
```

**You should see:**
```
src/                 (the Java source code)
pom.xml             (Maven configuration file)
mvnw                (Maven wrapper script)
.mvn/               (Maven wrapper files)
```

**Build the Java application:**
```bash
./mvnw clean package -DskipTests
```

**What this command means:**
- `./mvnw` = Use the Maven wrapper (builds Java projects)
- `clean` = Remove any old build files
- `package` = Compile the code and create a JAR file
- `-DskipTests` = Don't run tests (saves time for now)

**This will take 3-10 minutes the first time as it downloads Java libraries. You'll see lots of text like:**
```
[INFO] Scanning for projects...
[INFO] 
[INFO] ----------------< com.example:absence-management >-----------------
[INFO] Building absence-management 1.0.0
[INFO] --------------------------------[ jar ]---------------------------------
Downloading from central: https://repo1.maven.org/maven2/...
...
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  02:34 min
[INFO] Finished at: 2024-01-15T10:45:00Z
[INFO] ------------------------------------------------------------------------
```

**✅ Good if you see:** "BUILD SUCCESS" at the end  
**❌ Problem if you see:** "BUILD FAILURE" or "ERROR" messages  

**If build fails:**
- **Java not found**: Make sure Java is installed: `java -version`
- **Network errors**: Check internet connection (Maven downloads lots of files)
- **Permission errors**: Make sure `mvnw` is executable: `chmod +x mvnw`

**Check that the JAR file was created:**
```bash
ls -la target/
```

**You should see:**
```
absence-management-1.0.0.jar    (or similar name)
```

**Start the absence service:**
```bash
java -jar target/absence-management-*.jar
```

**What you should see:**
```
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /
 =========|_|==============|___/=/_/_/_/
 :: Spring Boot ::                (v3.1.5)

2024-01-15T10:50:00.123Z  INFO 12345 --- [           main] c.e.AbsenceManagementApplication         : Starting AbsenceManagementApplication...
...
2024-01-15T10:50:05.456Z  INFO 12345 --- [           main] o.s.b.w.embedded.tomcat.TomcatWebServer  : Tomcat started on port(s): 8080 (http)
2024-01-15T10:50:05.789Z  INFO 12345 --- [           main] c.e.AbsenceManagementApplication         : Started AbsenceManagementApplication in 5.234 seconds
```

**✅ Good if you see:** "Started AbsenceManagementApplication" and "Tomcat started on port(s): 8080"  
**❌ Problem if you see:** "ERROR" messages or application crashes  

**Common problems and solutions:**
- **"Port 8080 already in use"**: Something else is using that port. Try `sudo netstat -tulpn | grep 8080`
- **"Database connection failed"**: Make sure PostgreSQL container is running: `docker ps`
- **"Java heap space"**: Your computer might be low on memory. Try closing other programs

**Test the absence service is working:**
Open another new terminal and run:
```bash
curl http://localhost:8080/actuator/health
```

**What you should see:**
```json
{"status":"UP","components":{"db":{"status":"UP","details":{"database":"PostgreSQL","validationQuery":"isValid()"}},"diskSpace":{"status":"UP"}}}
```

**✅ Good if you see:** JSON response with "status":"UP"  
**❌ Problem if you see:** "Connection refused" or "status":"DOWN"  

**Test the API endpoints:**
```bash
curl http://localhost:8080/api/employees
```

**What you should see:**
```json
[{"id":1,"name":"John Doe","email":"john.doe@company.com","department":"Engineering","position":"Senior Developer"},...]
```

**✅ Good if you see:** JSON array with employee data  
**❌ Problem if you see:** Empty array `[]` or error messages  

### **Step 22: Build the Frontend (React Website)**

**Why do we need this?** This is the website that users see and interact with. It's built with React (JavaScript) and shows the chat interface, forms, and data.

**Open another new terminal** (keep backend and absence service running)

**What to do:**
```bash
cd ~/workspace/unified_chat/unified_ai_chat/frontend
pwd
```

**Make sure you're in the right place:**
```
/home/your-username/workspace/unified_chat/unified_ai_chat/frontend
```

**Look at what's in this folder:**
```bash
ls -la
```

**You should see:**
```
src/                 (the React source code)
public/             (static files like images)
package.json        (Node.js configuration)
package-lock.json   (exact versions of packages)
```

**Install Node.js packages:**
```bash
npm install
```

**This downloads all the JavaScript libraries our frontend needs. It takes 2-5 minutes and downloads 500+ packages:**
```
npm WARN deprecated some-package@1.0.0: This package is deprecated
...
added 1324 packages from 567 contributors and audited 1325 packages in 45.678s

9 vulnerabilities (3 moderate, 6 high)
  run `npm audit fix` to fix them, or `npm audit` for details
```

**✅ Good if you see:** "added XXXX packages" and no "ERROR" messages  
**❌ Problem if you see:** "npm ERR!" messages or "EACCES permission denied"  

**If installation fails:**
- **Permission errors**: Try `sudo chown -R $(whoami) ~/.npm`
- **Network errors**: Check internet connection
- **Disk space**: Make sure you have at least 5GB free space

**The vulnerability warnings are normal and not critical for development.**

**Start the frontend development server:**
```bash
npm start
```

**What this does:** Starts a development web server that serves our React application and automatically reloads when code changes.

**You'll see:**
```
Compiled successfully!

You can now view unified-ai-chat in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.100:3000

Note that the development build is not optimized.
To create a production build, use npm run build.

webpack compiled with 0 warnings
```

**✅ Good if you see:** "Compiled successfully!" and URLs shown  
**❌ Problem if you see:** "Failed to compile" or error messages  

**If compilation fails:**
- **Syntax errors**: There might be errors in the React code. Check the error messages
- **Port 3000 in use**: Try `npm start -- --port 3001` to use a different port
- **Memory errors**: Close other programs to free up RAM

**The frontend should automatically open in your web browser. If not, manually go to:** http://localhost:3000

**What you should see:** A web page with the AI Absence & SOW System interface

**✅ Good if you see:** The website loads with chat interface, buttons, and forms  
**❌ Problem if you see:** "This site can't be reached" or blank page  

**If the website doesn't work:**
- **Blank page**: Check browser console (F12) for JavaScript errors
- **API errors**: Make sure backend (port 5002) and absence service (port 8080) are running
- **Network errors**: Check that all three services can communicate-
--

## 🎉 **Checkpoint 3: All Applications Running!**

**You should now have 4 terminals open:**
1. **Database**: Docker container running PostgreSQL
2. **Backend**: Python FastAPI server on port 5002
3. **Absence Service**: Java Spring Boot on port 8080
4. **Frontend**: React development server on port 3000

**Let's verify everything is working:**

```bash
echo "=== System Status Check ==="
echo "Database:"
docker ps --filter "name=ai-absence-postgres" --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "Backend API:"
curl -s http://localhost:5002/api/health | head -c 50
echo ""
echo "Absence Service:"
curl -s http://localhost:8080/actuator/health | head -c 50
echo ""
echo "Frontend:"
curl -s http://localhost:3000 | grep -o "<title>.*</title>"
echo ""
echo "=== All checks complete ==="
```

**✅ You're ready for testing if:** 
- Database shows "Up" status
- Backend returns health JSON
- Absence service returns health JSON
- Frontend returns HTML with title

**❌ Go back and fix if:** 
- Any service shows errors
- Connection refused messages
- Services not responding

---

## 🧪 **Phase 6: Test the Complete System**

**Now let's test that all parts work together like they should in production.**

### **Step 23: Test the Web Interface**

**Open your web browser and go to:** http://localhost:3000

**What you should see:**
- **Header**: "AI Absence & SOW System"
- **Chat interface**: Text input box and send button
- **Navigation**: Buttons or tabs for different features
- **Clean, modern design**: Professional-looking interface

**✅ Good if you see:** Complete web interface loads without errors  
**❌ Problem if you see:** Blank page, error messages, or missing elements  

**If the interface has problems:**
- **Check browser console**: Press F12, look for red error messages
- **Check network tab**: See if API calls are failing
- **Verify all services**: Make sure backend and absence service are running

### **Step 24: Test the Chat Feature**

**In the web interface:**

1. **Click in the chat input box**
2. **Type:** "Hello, I need help with vacation request"
3. **Click Send or press Enter**

**What should happen:**
- Your message appears in the chat
- After 2-5 seconds, you get an AI response
- The AI should understand you want help with vacation

**✅ Good if you see:** AI responds with helpful message about vacation requests  
**❌ Problem if you see:** Error messages, no response, or generic responses  

**If chat doesn't work:**
- **Check your API key**: Make sure GEMINI_API_KEY in .env file is correct
- **Check backend logs**: Look at the terminal running the Python backend
- **Check internet**: AI needs internet to work
- **Try simple message**: Just type "Hello" to test basic functionality

### **Step 25: Test Employee Management**

**In the web interface, look for an "Employees" section or button.**

**What you should see:**
- List of sample employees (John Doe, Jane Smith, etc.)
- Employee details like name, email, department
- Ability to view employee information

**If you can't find employee section:**
- Try different tabs or menu items
- Check if there's a navigation menu
- The feature might be in the chat - try asking "Show me all employees"

**Test adding a new employee:**
1. **Look for "Add Employee" button or form**
2. **Fill in details:**
   - Name: "Test User"
   - Email: "test@company.com"
   - Department: "Testing"
   - Position: "Tester"
3. **Submit the form**

**✅ Good if you see:** New employee appears in the list  
**❌ Problem if you see:** Error messages or employee not saved  

### **Step 26: Test Absence Request Feature**

**Try creating a vacation request:**

1. **In the chat, type:** "I want to request vacation for next Monday and Tuesday"
2. **Follow the AI's prompts** to provide details
3. **Complete the request process**

**What should happen:**
- AI asks for specific dates
- AI asks for reason (optional)
- AI confirms the request
- Request gets saved to database

**✅ Good if you see:** Complete vacation request process works  
**❌ Problem if you see:** AI doesn't understand, errors saving request  

**Alternative test method:**
- Look for "Absence Requests" section in the web interface
- Try creating a request through forms instead of chat

### **Step 27: Test SOW (Statement of Work) Feature**

**Try generating a work document:**

1. **In the chat, type:** "I need to create a Statement of Work for a new project"
2. **Provide project details** when AI asks:
   - Project name: "Website Redesign"
   - Description: "Redesign company website with modern look"
   - Budget: "$10,000"
   - Timeline: "3 months"

**What should happen:**
- AI asks for project details
- AI generates a professional SOW document
- You can download or view the document

**✅ Good if you see:** AI generates a proper SOW document  
**❌ Problem if you see:** AI doesn't understand, no document generated  

### **Step 28: Test Database Persistence**

**Let's make sure data is actually saved:**

**In a terminal, check the database:**
```bash
docker exec -it ai-absence-postgres psql -U ai_absence -d ai_absence_db -c "SELECT COUNT(*) FROM employees;"
```

**You should see more than 5 employees if you added the test user.**

**Check absence requests:**
```bash
docker exec -it ai-absence-postgres psql -U ai_absence -d ai_absence_db -c "SELECT * FROM absence_requests ORDER BY created_at DESC LIMIT 3;"
```

**You should see any vacation requests you created.**

**✅ Good if you see:** Your test data appears in database  
**❌ Problem if you see:** No new data or database errors  

---

## 🎉 **Checkpoint 4: System Fully Working!**

**If all tests pass, congratulations! You have successfully deployed the complete AI Absence & SOW System.**

**What you've accomplished:**
- ✅ Installed all required software
- ✅ Downloaded and configured the code
- ✅ Set up a PostgreSQL database with sample data
- ✅ Built and started the Python AI backend
- ✅ Built and started the Java absence service
- ✅ Built and started the React frontend
- ✅ Tested all major features
- ✅ Verified data persistence

**Your system is now ready for:**
- Development and testing
- Demonstrations to stakeholders
- Further feature development
- Production deployment preparation---


## 🔧 **Phase 7: Daily Operations**

**Now that everything works, here's how to manage the system day-to-day.**

### **Step 29: How to Stop Everything**

**When you're done working, you need to stop all services properly:**

**Stop the frontend** (in the terminal running `npm start`):
- Press `Ctrl+C`
- Wait for it to say "webpack: Disconnected from server"

**Stop the absence service** (in the terminal running the Java application):
- Press `Ctrl+C`
- Wait for it to say "Shutdown completed"

**Stop the backend** (in the terminal running `uvicorn`):
- Press `Ctrl+C`
- Wait for it to say "Shutting down"

**Stop the database:**
```bash
docker-compose -f docker-compose-database.yml down
```

**What you should see:**
```
Stopping ai-absence-postgres ... done
Removing ai-absence-postgres ... done
Removing network unified_chat_default
```

**✅ Good if you see:** All services stop cleanly  
**❌ Problem if you see:** "Error" messages or services hanging  

**If services won't stop:**
- **Force stop**: Press `Ctrl+C` multiple times
- **Kill processes**: Find process IDs with `ps aux | grep java` or `ps aux | grep python` and use `kill -9 <process_id>`
- **Force stop Docker**: `docker kill ai-absence-postgres`

### **Step 30: How to Start Everything (Daily Startup)**

**When you want to work on the system again:**

**1. Start the database:**
```bash
cd ~/workspace/unified_chat
docker-compose -f docker-compose-database.yml up -d
```

**Wait 30 seconds for database to be ready, then check:**
```bash
docker ps --filter "name=ai-absence-postgres"
```

**2. Start the backend (in terminal 1):**
```bash
cd ~/workspace/unified_chat/unified_ai_chat/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
```

**3. Start the absence service (in terminal 2):**
```bash
cd ~/workspace/unified_chat/ai_absence-ai_absence_mi/backend/absence-management
java -jar target/absence-management-*.jar
```

**4. Start the frontend (in terminal 3):**
```bash
cd ~/workspace/unified_chat/unified_ai_chat/frontend
npm start
```

**Total startup time: 2-3 minutes**

### **Step 31: Quick Health Check Script**

**Create a script to quickly check if everything is working:**

```bash
cd ~/workspace/unified_chat
nano quick-check.sh
```

**In nano, type:**
```bash
#!/bin/bash
echo "=== AI Absence & SOW System Health Check ==="
echo ""

echo "1. Database:"
if docker ps --filter "name=ai-absence-postgres" --format "{{.Status}}" | grep -q "Up"; then
    echo "   ✅ PostgreSQL is running"
else
    echo "   ❌ PostgreSQL is not running"
fi

echo ""
echo "2. Backend API:"
if curl -s http://localhost:5002/api/health > /dev/null 2>&1; then
    echo "   ✅ Backend is responding"
else
    echo "   ❌ Backend is not responding"
fi

echo ""
echo "3. Absence Service:"
if curl -s http://localhost:8080/actuator/health > /dev/null 2>&1; then
    echo "   ✅ Absence service is responding"
else
    echo "   ❌ Absence service is not responding"
fi

echo ""
echo "4. Frontend:"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend is responding"
else
    echo "   ❌ Frontend is not responding"
fi

echo ""
echo "=== Health check complete ==="
echo "If all services show ✅, your system is ready!"
echo "If any show ❌, start those services first."
```

**Save and make executable:**
```bash
chmod +x quick-check.sh
```

**Use it anytime:**
```bash
./quick-check.sh
```

### **Step 32: Common Daily Problems and Solutions**

**Problem: "Port already in use"**
```bash
# Find what's using the port
sudo netstat -tulpn | grep 5002  # or 8080, or 3000

# Kill the process
sudo kill -9 <process_id>
```

**Problem: "Database connection failed"**
```bash
# Check if database container is running
docker ps --filter "name=ai-absence-postgres"

# If not running, start it
docker-compose -f docker-compose-database.yml up -d

# Wait 30 seconds, then test
docker exec -it ai-absence-postgres psql -U ai_absence -d ai_absence_db -c "SELECT 1;"
```

**Problem: "Virtual environment not found"**
```bash
# Recreate the virtual environment
cd ~/workspace/unified_chat/unified_ai_chat/backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Problem: "npm packages missing"**
```bash
# Reinstall Node.js packages
cd ~/workspace/unified_chat/unified_ai_chat/frontend
rm -rf node_modules package-lock.json
npm install
```

**Problem: "Java application won't start"**
```bash
# Rebuild the Java application
cd ~/workspace/unified_chat/ai_absence-ai_absence_mi/backend/absence-management
./mvnw clean package -DskipTests
```

---

## 📚 **Phase 8: Understanding What You Built**

**Now that everything works, let's understand what each part does:**

### **The Database (PostgreSQL)**
- **What it does**: Stores all data (employees, vacation requests, work documents)
- **Where it runs**: Docker container on port 5432
- **How to access**: `docker exec -it ai-absence-postgres psql -U ai_absence -d ai_absence_db`
- **Data location**: Stored in Docker volume (persists when container restarts)

### **The Backend (Python FastAPI)**
- **What it does**: Main API server, talks to AI, coordinates everything
- **Where it runs**: Python process on port 5002
- **Key files**: `app/main.py` (main application), `app/gemini_client.py` (AI integration)
- **API docs**: http://localhost:5002/docs

### **The Absence Service (Java Spring Boot)**
- **What it does**: Manages employee data and absence requests
- **Where it runs**: Java process on port 8080
- **Key files**: `src/main/java/` (Java source code), `target/*.jar` (compiled application)
- **Health check**: http://localhost:8080/actuator/health

### **The Frontend (React)**
- **What it does**: User interface, what people see and click
- **Where it runs**: Node.js development server on port 3000
- **Key files**: `src/` (React components), `public/` (static files)
- **Access**: http://localhost:3000

### **How They Work Together**
1. **User** opens website (Frontend)
2. **Frontend** sends requests to Backend API
3. **Backend** processes requests, talks to AI if needed
4. **Backend** calls Absence Service for employee data
5. **Absence Service** reads/writes to Database
6. **Results** flow back to user through the chain

---

## 🎯 **Phase 9: Next Steps and Production**

### **For Development Work**
- **Make code changes**: Edit files in `src/` folders
- **Test changes**: Services auto-reload when you save files
- **Add features**: Follow the existing code patterns
- **Debug issues**: Check terminal logs for error messages

### **For Production Deployment**
- **Use the Docker approach**: Build containers for each service
- **Use Kubernetes**: Deploy to a cluster for scalability
- **Use proper database**: Set up managed PostgreSQL or Oracle
- **Add monitoring**: Set up logging and health monitoring
- **Add security**: Implement authentication and authorization

### **Files You Can Modify**
- **Frontend**: `unified_ai_chat/frontend/src/` - React components
- **Backend**: `unified_ai_chat/backend/app/` - Python API code
- **Absence Service**: `ai_absence-ai_absence_mi/backend/absence-management/src/` - Java code
- **Database**: `database-init.sql` - Database schema and sample data
- **Configuration**: `sow_gen_ai/.env` - Environment variables

### **Files You Shouldn't Touch**
- **Docker files**: Unless you know what you're doing
- **Package files**: `package.json`, `requirements.txt`, `pom.xml` (unless adding dependencies)
- **Build outputs**: `target/`, `node_modules/`, `venv/`

---

**You have successfully:**
- ✅ Set up a complete development environment
- ✅ Deployed a multi-service application
- ✅ Connected AI, web, and database components
- ✅ Tested all major functionality
- ✅ Learned how to manage the system daily

**Your AI Absence & SOW System is now:**
- 🚀 **Running locally** and ready for development
- 🔧 **Fully functional** with all features working
- 📊 **Storing data** persistently in PostgreSQL
- 🤖 **AI-powered** with Google Gemini integration
- 🌐 **Web-accessible** through a modern React interface

**You're now ready to:**
- Demonstrate the system to stakeholders
- Develop new features and improvements
- Deploy to production environments
- Train other team members
---

## 🚀 **Phase 10: Set Up CI/CD Pipeline (Automated Deployment)**

**What is CI/CD?** Think of CI/CD like having a robot assistant that automatically:
- **Tests your code** every time you make changes
- **Builds new versions** of your application
- **Deploys to production** without manual work
- **Rolls back** if something goes wrong

**Why do we need this?** Instead of manually building and deploying every time (which takes hours and is error-prone), the pipeline does it automatically in minutes.

### **Step 33: Understanding Our Pipeline**

**We already have a complete CI/CD pipeline! Let's look at it:**

```bash
cd ~/workspace/unified_chat
ls -la .github/workflows/
```

**You should see:**
```
deploy.yml    (Our complete CI/CD pipeline)
```

**Look at the pipeline:**
```bash
cat .github/workflows/deploy.yml
```

**This file contains our entire automated deployment process. Here's what it does:**

1. **Triggers**: Runs automatically when you push code to GitHub
2. **Tests**: Runs all tests to make sure code works
3. **Builds**: Creates Docker containers for all services
4. **Security**: Scans for vulnerabilities
5. **Deploys**: Pushes to staging, then production
6. **Validates**: Checks that deployment worked
7. **Notifies**: Tells team if deployment succeeded or failed

### **Step 34: Set Up GitHub Repository**

**Why do this?** The pipeline runs on GitHub. We need to connect your local code to GitHub so the automation can work.

**If you don't have a GitHub account:**
1. Go to https://github.com
2. Click "Sign up"
3. Create account with your email
4. Verify your email

**Create a new repository:**
1. **Go to GitHub** and sign in
2. **Click the "+" icon** in top-right corner
3. **Click "New repository"**
4. **Fill in details:**
   - Repository name: `ai-absence-sow-system`
   - Description: `AI-powered absence and SOW management system`
   - Make it **Private** (for now)
   - Don't initialize with README (we already have code)
5. **Click "Create repository"**

**Connect your local code to GitHub:**
```bash
cd ~/workspace/unified_chat

# Add GitHub as remote origin
git remote add origin https://github.com/YOUR_USERNAME/ai-absence-sow-system.git

# Replace YOUR_USERNAME with your actual GitHub username
```

**Push your code to GitHub:**
```bash
# Make sure you're on the right branch
git branch

# Add all files
git add .

# Commit changes
git commit -m "Initial deployment setup with complete CI/CD pipeline"

# Push to GitHub
git push -u origin production-deployment
```

**What you should see:**
```
Enumerating objects: 1234, done.
Counting objects: 100% (1234/1234), done.
...
To https://github.com/YOUR_USERNAME/ai-absence-sow-system.git
 * [new branch]      production-deployment -> production-deployment
Branch 'production-deployment' set up to track remote branch 'production-deployment' from 'origin'.
```

**✅ Good if you see:** Code pushed successfully to GitHub  
**❌ Problem if you see:** "Permission denied" or "Authentication failed"  

**If push fails:**
- **Authentication error**: You might need to set up a Personal Access Token
- **Permission denied**: Check your GitHub username in the URL
- **Repository not found**: Make sure you created the repository on GitHub

### **Step 35: Configure GitHub Secrets**

**Why do this?** Our pipeline needs secret information (like API keys and passwords) to deploy. We store these securely in GitHub.

**Go to your GitHub repository:**
1. **Click "Settings"** tab
2. **Click "Secrets and variables"** in left sidebar
3. **Click "Actions"**
4. **Click "New repository secret"**

**Add these secrets one by one:**

**Secret 1: GEMINI_API_KEY**
- Name: `GEMINI_API_KEY`
- Value: Your actual Gemini API key (from Step 15)
- Click "Add secret"

**Secret 2: DOCKER_USERNAME**
- Name: `DOCKER_USERNAME`
- Value: Your Docker Hub username (create account at hub.docker.com if needed)
- Click "Add secret"

**Secret 3: DOCKER_PASSWORD**
- Name: `DOCKER_PASSWORD`
- Value: Your Docker Hub password or access token
- Click "Add secret"

**Secret 4: DB_PASSWORD**
- Name: `DB_PASSWORD`
- Value: `ai_absence_password` (or your chosen database password)
- Click "Add secret"

**After adding all secrets, you should see:**
```
GEMINI_API_KEY
DOCKER_USERNAME
DOCKER_PASSWORD
DB_PASSWORD
```

**✅ Good if you see:** All 4 secrets listed  
**❌ Problem if you see:** Can't find Settings tab or Secrets section  

### **Step 36: Test the CI/CD Pipeline**

**Now let's trigger the pipeline and see it work:**

**Make a small change to test:**
```bash
cd ~/workspace/unified_chat
echo "# Pipeline Test" >> README.md
```

**Commit and push the change:**
```bash
git add README.md
git commit -m "Test CI/CD pipeline trigger"
git push origin production-deployment
```

**Watch the pipeline run:**
1. **Go to your GitHub repository**
2. **Click "Actions" tab**
3. **You should see a workflow running** called "Deploy to Oracle Cloud"
4. **Click on it** to see details

**What you should see:**
```
Deploy to Oracle Cloud
✓ Build and Test (2m 34s)
✓ Security Scan (1m 12s)
⏳ Build Images (running...)
⏳ Deploy to Staging (queued)
⏳ Deploy to Production (queued)
```

**The pipeline has 5 main jobs:**
1. **Build and Test** - Compiles code and runs tests
2. **Security Scan** - Checks for vulnerabilities
3. **Build Images** - Creates Docker containers
4. **Deploy to Staging** - Deploys to test environment
5. **Deploy to Production** - Deploys to live environment

**✅ Good if you see:** Pipeline starts and shows green checkmarks  
**❌ Problem if you see:** Red X marks or "Failed" status  

**If pipeline fails:**
- **Click on the failed job** to see error details
- **Common issues**: Missing secrets, Docker login failed, code syntax errors
- **Check logs**: Each job shows detailed logs of what went wrong

### **Step 37: Understanding Pipeline Stages**

**Let's understand what each stage does:**

**Stage 1: Build and Test**
```bash
# This is what the pipeline does automatically:
# 1. Checks out your code
# 2. Sets up Node.js, Python, Java
# 3. Installs dependencies
# 4. Runs tests
# 5. Builds applications
```

**You can run these same tests locally:**
```bash
cd ~/workspace/unified_chat

# Test frontend build
cd unified_ai_chat/frontend
npm run build

# Test backend
cd ../backend
source venv/bin/activate
python -c "import app.main; print('Backend imports successfully')"

# Test absence service build
cd ../../ai_absence-ai_absence_mi/backend/absence-management
./mvnw clean package -DskipTests
```

**Stage 2: Security Scan**
```bash
# The pipeline automatically scans for:
# - Vulnerable dependencies
# - Security issues in code
# - Container vulnerabilities
# - Exposed secrets
```

**Stage 3: Build Images**
```bash
# The pipeline automatically:
# 1. Builds Docker images for all services
# 2. Tags them with version numbers
# 3. Pushes to Docker registry
# 4. Scans images for vulnerabilities
```

**Stage 4: Deploy to Staging**
```bash
# The pipeline automatically:
# 1. Deploys to staging environment
# 2. Runs health checks
# 3. Tests all APIs
# 4. Validates data flow
```

**Stage 5: Deploy to Production**
```bash
# The pipeline automatically:
# 1. Deploys to production environment
# 2. Runs comprehensive health checks
# 3. Monitors for errors
# 4. Sends notifications
```

### **Step 38: Monitor Pipeline Results**

**Check pipeline status:**
1. **Go to GitHub Actions tab**
2. **Click on your workflow run**
3. **Check each job status**

**If all jobs pass:**
```
✓ Build and Test (3m 45s)
✓ Security Scan (1m 23s)
✓ Build Images (4m 12s)
✓ Deploy to Staging (2m 56s)
✓ Deploy to Production (3m 18s)
```

**✅ Success! Your code is now automatically deployed!**

**If any job fails:**
1. **Click on the failed job**
2. **Read the error logs**
3. **Fix the issue in your code**
4. **Push the fix** - pipeline will run again automatically

**Common failure reasons:**
- **Test failures**: Code has bugs
- **Build failures**: Syntax errors or missing dependencies
- **Security issues**: Vulnerable packages detected
- **Deployment failures**: Infrastructure problems

### **Step 39: Set Up Notifications**

**Get notified when deployments succeed or fail:**

**Option 1: Email Notifications**
1. **Go to GitHub repository**
2. **Click "Watch" button**
3. **Select "All Activity"**
4. **You'll get emails** for all pipeline runs

**Option 2: Slack Notifications (if your team uses Slack)**
The pipeline already includes Slack integration. To enable:
1. **Create Slack webhook** in your workspace
2. **Add SLACK_WEBHOOK secret** in GitHub
3. **Pipeline will send notifications** to your channel

**Option 3: Mobile Notifications**
1. **Install GitHub mobile app**
2. **Sign in with your account**
3. **Enable push notifications**
4. **Get instant alerts** on your phone

### **Step 40: Daily Development Workflow with CI/CD**

**Now that CI/CD is set up, here's your new daily workflow:**

**Old way (manual):**
1. Write code
2. Test locally
3. Build manually
4. Deploy manually
5. Hope nothing breaks

**New way (automated):**
1. **Write code** locally
2. **Test locally** (optional but recommended)
3. **Commit and push** to GitHub
4. **Pipeline automatically** tests, builds, and deploys
5. **Get notification** when deployment completes
6. **Check production** to verify everything works

**Example daily workflow:**
```bash
# 1. Start your day
cd ~/workspace/unified_chat
git pull origin production-deployment  # Get latest changes

# 2. Make changes
# Edit files, add features, fix bugs

# 3. Test locally (optional)
./quick-check.sh

# 4. Commit and push
git add .
git commit -m "Add new feature: employee search"
git push origin production-deployment

# 5. Watch pipeline (optional)
# Go to GitHub Actions to see progress

# 6. Get notification when done
# Email/Slack/mobile notification

# 7. Verify in production
# Check that your changes are live
```

**Benefits of this workflow:**
- **Faster deployments**: Minutes instead of hours
- **Fewer errors**: Automated testing catches bugs
- **Consistent process**: Same steps every time
- **Easy rollbacks**: Can undo bad deployments quickly
- **Team collaboration**: Everyone sees what's deployed when#
## **Step 41: Understanding Different Environments**

**Our pipeline deploys to multiple environments. Here's what each one is for:**

**Local Environment (Your Laptop):**
- **Purpose**: Development and testing
- **What runs here**: All services on your computer
- **When to use**: Writing code, debugging, testing new features
- **Access**: http://localhost:3000

**Staging Environment (Test Server):**
- **Purpose**: Testing before production
- **What runs here**: Exact copy of production
- **When to use**: Final testing, demos, user acceptance testing
- **Access**: https://staging.your-domain.com (configured by DevOps)

**Production Environment (Live Server):**
- **Purpose**: Real users access this
- **What runs here**: Live application
- **When to use**: After all testing is complete
- **Access**: https://your-domain.com (configured by DevOps)

**Pipeline Flow:**
```
Your Laptop → GitHub → Pipeline → Staging → Production
     ↓            ↓         ↓         ↓         ↓
   Develop    Store Code  Test &   Test with  Live for
   & Test               Build    Real Data    Users
```

### **Step 42: Troubleshooting Pipeline Issues**

**Common pipeline problems and how to fix them:**

**Problem: "Build failed - Tests not passing"**
```bash
# Fix locally first:
cd ~/workspace/unified_chat
./scripts/test-deployment.sh

# If tests fail locally, fix the code
# Then push again
git add .
git commit -m "Fix failing tests"
git push origin production-deployment
```

**Problem: "Docker build failed"**
```bash
# Test Docker build locally:
docker build -f docker/frontend/Dockerfile -t test-frontend .
docker build -f docker/backend/Dockerfile -t test-backend .
docker build -f docker/absence-service/Dockerfile -t test-absence .

# If any fail, check the Dockerfile and fix issues
```

**Problem: "Deployment failed - Health checks failing"**
```bash
# The pipeline runs health checks after deployment
# If they fail, it means services aren't starting properly
# Check the pipeline logs for specific error messages
# Common causes:
# - Database connection issues
# - Missing environment variables
# - Port conflicts
# - Resource limitations
```

**Problem: "Security scan failed"**
```bash
# Update vulnerable packages:

# For Node.js:
cd unified_ai_chat/frontend
npm audit fix

# For Python:
cd ../backend
pip install --upgrade package-name

# For Java:
cd ../../ai_absence-ai_absence_mi/backend/absence-management
./mvnw versions:use-latest-versions
```

**Problem: "Pipeline not triggering"**
```bash
# Check these things:
# 1. Are you pushing to the right branch?
git branch  # Should show * production-deployment

# 2. Is the workflow file in the right place?
ls -la .github/workflows/deploy.yml

# 3. Are there syntax errors in the workflow?
# Check GitHub Actions tab for error messages
```

### **Step 43: Advanced Pipeline Features**

**Our pipeline includes advanced features you should know about:**

**Feature 1: Automatic Rollback**
- **What it does**: If deployment fails, automatically goes back to previous version
- **How it works**: Pipeline keeps track of last working version
- **Manual rollback**: You can also rollback manually from GitHub Actions

**Feature 2: Blue-Green Deployment**
- **What it does**: Deploys new version alongside old version, then switches traffic
- **Benefit**: Zero downtime deployments
- **How it works**: Users never see a broken site during updates

**Feature 3: Canary Deployment**
- **What it does**: Gradually rolls out changes to small percentage of users first
- **Benefit**: Catches problems before they affect everyone
- **How it works**: 5% of users see new version, then 25%, then 100%

**Feature 4: Automated Testing**
- **Unit tests**: Test individual functions
- **Integration tests**: Test services working together
- **End-to-end tests**: Test complete user workflows
- **Performance tests**: Check system can handle load

**Feature 5: Security Scanning**
- **Dependency scanning**: Checks for vulnerable packages
- **Code scanning**: Looks for security issues in code
- **Container scanning**: Scans Docker images for vulnerabilities
- **Secret scanning**: Makes sure no passwords are in code

### **Step 44: Team Collaboration with CI/CD**

**How multiple developers work together:**

**Branch Strategy:**
```bash
# Main branches:
main                    # Stable, production-ready code
production-deployment   # Code ready for deployment
feature/new-feature    # Individual feature development
hotfix/urgent-fix      # Emergency fixes
```

**Typical team workflow:**
1. **Developer creates feature branch**:
   ```bash
   git checkout -b feature/employee-search
   ```

2. **Developer works on feature locally**
3. **Developer pushes feature branch**:
   ```bash
   git push origin feature/employee-search
   ```

4. **Developer creates Pull Request** on GitHub
5. **Team reviews code** and suggests changes
6. **Pipeline runs tests** on the Pull Request
7. **After approval, merge to production-deployment**
8. **Pipeline automatically deploys** to staging, then production

**Code Review Process:**
- **All changes reviewed** by at least one other developer
- **Automated tests must pass** before merge
- **Security scans must pass** before merge
- **Documentation updated** if needed

**Conflict Resolution:**
```bash
# If multiple developers change same files:
git pull origin production-deployment  # Get latest changes
# Fix conflicts in files
git add .
git commit -m "Resolve merge conflicts"
git push origin production-deployment
```

### **Step 45: Monitoring and Alerts**

**The pipeline sets up monitoring so you know if something breaks:**

**Health Monitoring:**
- **Automatic health checks** every 5 minutes
- **API endpoint monitoring** to ensure services respond
- **Database connection monitoring** to catch DB issues
- **Performance monitoring** to detect slowdowns

**Alert Types:**
- **Deployment success/failure** notifications
- **Service down** alerts
- **High error rate** warnings
- **Performance degradation** alerts
- **Security vulnerability** notifications

**Where alerts go:**
- **Email** to development team
- **Slack** channel notifications
- **Mobile** push notifications
- **Dashboard** showing system status

**Responding to alerts:**
1. **Check the alert details** - what exactly is wrong?
2. **Look at pipeline logs** - recent deployments that might have caused it
3. **Check service health** - which specific service is having issues
4. **Fix the problem** - either rollback or push a fix
5. **Verify fix worked** - confirm alerts stop and system is healthy

---

## 🎉 **Checkpoint 5: Complete CI/CD Pipeline Working!**

**You now have a complete, professional CI/CD pipeline that:**

✅ **Automatically tests** your code on every change  
✅ **Builds Docker containers** for all services  
✅ **Scans for security** vulnerabilities  
✅ **Deploys to staging** for testing  
✅ **Deploys to production** after validation  
✅ **Monitors system health** continuously  
✅ **Sends notifications** on success/failure  
✅ **Supports team collaboration** with code reviews  
✅ **Enables easy rollbacks** if problems occur  

**Your development workflow is now:**
1. **Write code** locally
2. **Push to GitHub** 
3. **Pipeline handles everything else** automatically
4. **Get notified** when deployment completes
5. **Users see your changes** in production

