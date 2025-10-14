import streamlit as st
import requests
import websocket
import json
import threading
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api"
WS_BASE_URL = "ws://localhost:8000/api/ws"

# Page config
st.set_page_config(
    page_title="SOW Generator Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for chat interface
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        color: #000; /* Set text color to black for all chat messages */
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
        border-left: 4px solid #2196f3;
        /* color: #000;  Not needed, inherited from .chat-message */
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 20%;
        border-left: 4px solid #4caf50;
        /* color: #000;  Not needed, inherited from .chat-message */
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #000; /* Make header text black */
    }
    .progress-indicator {
        background-color: #e0e0e0;
        height: 8px;
        border-radius: 4px;
        margin: 1rem 0;
        overflow: hidden;
    }
    .progress-bar {
        background: linear-gradient(90deg, #4caf50, #2196f3);
        height: 100%;
        transition: width 0.3s ease;
    }
    .stage-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        background-color: #2196f3;
        color: white;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'template_id' not in st.session_state:
    st.session_state.template_id = None
if 'ws_connected' not in st.session_state:
    st.session_state.ws_connected = False
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = "initial"
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'is_complete' not in st.session_state:
    st.session_state.is_complete = False
if 'awaiting_response' not in st.session_state:
    st.session_state.awaiting_response = False

# Function to connect and get initial greeting
def connect_and_get_greeting(session_id):
    """Connect to WebSocket and get initial greeting"""
    try:
        ws_url = f"{WS_BASE_URL}/{session_id}"
        ws = websocket.create_connection(ws_url, timeout=30)
        
        # Receive initial greeting
        initial = ws.recv()
        initial_data = json.loads(initial)
        
        ws.close()
        
        return initial_data['message']
        
    except Exception as e:
        return f"Error connecting: {str(e)}"

# Function to send message via WebSocket
def send_message_ws(session_id, message):
    """Send message and get response via WebSocket"""
    try:
        ws_url = f"{WS_BASE_URL}/{session_id}"
        ws = websocket.create_connection(ws_url, timeout=90)
        
        # Receive and discard initial greeting (we already showed it)
        ws.recv()
        
        # Send user message
        ws.send(json.dumps({"message": message}))
        
        # Receive response
        response = ws.recv()
        response_data = json.loads(response)
        
        # Update session state
        st.session_state.current_stage = response_data.get('stage', 'initial')
        st.session_state.progress = response_data.get('progress', 0)
        st.session_state.is_complete = response_data.get('is_complete', False)
        
        ws.close()
        
        return response_data['message']
        
    except Exception as e:
        return f"Error: {str(e)}"

# Header
st.markdown('<div class="main-header">🤖 SOW Generator Chatbot</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("💬 Chat Session")
    
    # API Status
    try:
        health = requests.get("http://localhost:8000/health", timeout=2)
        if health.status_code == 200:
            st.success("✅ API: Online")
        else:
            st.error("⚠️ API: Issues")
    except:
        st.error("❌ API: Offline")
        st.stop()
    
    st.markdown("---")
    
    # Template Upload
    st.subheader("📤 1. Upload Template")
    uploaded_file = st.file_uploader("Choose DOCX template", type=['docx'])
    
    if uploaded_file and not st.session_state.template_id:
        with st.spinner("Uploading..."):
            files = {'file': (uploaded_file.name, uploaded_file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = requests.post(f"{API_BASE_URL}/upload-template", files=files)
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.template_id = data['template_id']
                st.success("✅ Template uploaded!")
                
                # Create session
                session_response = requests.post(f"{API_BASE_URL}/create-session?template_id={st.session_state.template_id}")
                if session_response.status_code == 200:
                    st.session_state.session_id = session_response.json()['session_id']
                    st.success(f"✅ Session created!")
                    
                    # ✅ Automatically connect and get greeting
                    with st.spinner("Connecting to chatbot..."):
                        greeting = connect_and_get_greeting(st.session_state.session_id)
                        
                        # Add greeting to messages
                        st.session_state.messages.append({
                            'role': 'assistant',
                            'content': greeting
                        })
                        
                        st.success("✅ Chatbot ready!")
                    
                    time.sleep(1)  # Brief pause so user sees success messages
                    st.rerun()
    
    if st.session_state.template_id:
        st.info(f"📋 Template: {st.session_state.template_id[:20]}...")
    
    st.markdown("---")
    
    # Progress Indicator
    st.subheader("📊 Progress")
    
    progress_value = st.session_state.progress
    st.markdown(f"""
        <div class="progress-indicator">
            <div class="progress-bar" style="width: {progress_value}%"></div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**{progress_value}%** Complete")
    
    # Stage indicator
    stage_names = {
        "initial": "🎯 Getting Started",
        "project_info": "📋 Project Info",
        "services": "🔧 Services",
        "deliverables": "📦 Deliverables",
        "timeline": "📅 Timeline",
        "resources": "👥 Resources",
        "contacts": "📞 Contacts",
        "budget": "💰 Budget",
        "completed": "✅ Complete"
    }
    
    current_stage_name = stage_names.get(st.session_state.current_stage, "Unknown")
    st.markdown(f"**Stage:** {current_stage_name}")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    if st.session_state.is_complete:
        if st.button("📥 Download SOW", use_container_width=True):
            try:
                download_response = requests.get(f"{API_BASE_URL}/download/{st.session_state.session_id}")
                if download_response.status_code == 200:
                    st.download_button(
                        label="💾 Save Document",
                        data=download_response.content,
                        file_name=f"SOW_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Error: {e}")
    
    if st.button("🔄 Start New Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Tips
    with st.expander("💡 Tips"):
        st.markdown("""
        **How to use:**
        1. Upload your template
        2. Answer the bot's questions
        3. Be specific and complete
        4. Review each response
        
        **Example responses:**
        - Project: "SOW-2025-001, Cloud Migration, reduce costs"
        - Services: "Planning for 2 weeks, Migration for 4 weeks"
        - Budget: "Planning $15000, Migration $40000"
        """)

# Main chat area
st.subheader("💬 Conversation")

# Display chat messages
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        role = message['role']
        content = message['content']
        
        if role == "assistant":
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <div class="message-header">
                    🤖 Assistant
                </div>
                <div>{content}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-header">
                    👤 You
                </div>
                <div>{content}</div>
            </div>
            """, unsafe_allow_html=True)

# Chat input (only show if session exists and not complete)
if st.session_state.session_id:
    if not st.session_state.is_complete:
        # User input
        user_input = st.chat_input("Type your response here...", key="chat_input")
        
        if user_input and not st.session_state.awaiting_response:
            # Add user message
            st.session_state.messages.append({
                'role': 'user',
                'content': user_input
            })
            
            # Set awaiting flag
            st.session_state.awaiting_response = True
            
            # Show loading
            with st.spinner("🤖 Thinking..."):
                # Send to WebSocket and get response
                bot_response = send_message_ws(st.session_state.session_id, user_input)
                
                # Add bot response
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': bot_response
                })
            
            # Reset awaiting flag
            st.session_state.awaiting_response = False
            
            # Rerun to update UI
            st.rerun()
        
        # Show stage-specific help
        if st.session_state.current_stage == "project_info":
            st.info("💡 Provide: Document number, project name, and objectives")
        elif st.session_state.current_stage == "services":
            st.info("💡 Describe each service with name, description, and duration")
        elif st.session_state.current_stage == "deliverables":
            st.info("💡 List deliverable names and their descriptions")
        elif st.session_state.current_stage == "timeline":
            st.info("💡 Provide start date, end date, number of sprints")
        elif st.session_state.current_stage == "resources":
            st.info("💡 List role, team, count, and allocation for each resource")
        elif st.session_state.current_stage == "contacts":
            st.info("💡 Provide complete contact details for both contractor and client")
        elif st.session_state.current_stage == "budget":
            st.info("💡 List each milestone with its fee amount and estimated expenses")
    
    else:
        # Completion screen
        st.success("🎉 **Conversation Complete!**")
        st.balloons()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Generate & Download Document", use_container_width=True):
                with st.spinner("Generating document..."):
                    try:
                        gen_response = requests.post(f"{API_BASE_URL}/generate-document/{st.session_state.session_id}")
                        
                        if gen_response.status_code == 200:
                            st.success("✅ Document generated!")
                            
                            # Download
                            download_response = requests.get(f"{API_BASE_URL}/download/{st.session_state.session_id}")
                            
                            if download_response.status_code == 200:
                                st.download_button(
                                    label="💾 Download SOW Document",
                                    data=download_response.content,
                                    file_name=f"SOW_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    use_container_width=True
                                )
                        else:
                            st.error(f"Generation failed: {gen_response.json().get('detail')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("🔄 Start New SOW", use_container_width=True):
                st.session_state.clear()
                st.rerun()

else:
    # Show welcome message
    st.info("👈 Please upload a template in the sidebar to begin")
    
    st.markdown("""
    ### Welcome to SOW Generator! 🚀
    
    This chatbot will guide you through creating a professional Statement of Work document.
    
    **How it works:**
    1. Upload your SOW template (.docx)
    2. Answer questions about your project
    3. Review and download your completed SOW
    
    **What you'll need:**
    - Project details (name, dates, objectives)
    - Services to be provided
    - Deliverables and milestones
    - Resource requirements
    - Contact information
    - Budget details
    
    Ready? Upload your template to get started! 👆
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>SOW Generator Chatbot • Powered by FastAPI & WebSocket</p>
</div>
""", unsafe_allow_html=True)
