"""
🚀 ULTIMATE RAG SYSTEM v2.1 - Streamlit Frontend
================================================
Beautiful UI for testing the most advanced free-tier RAG system!
"""

import streamlit as st
import requests
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Backend API URL
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Ultimate RAG System v2.1",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .source-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: #f0f2f6;
        margin-bottom: 0.5rem;
    }
    .stats-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🚀 Ultimate RAG System v2.1</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">The Most Advanced Free-Tier RAG System Ever Built!</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ System Control")

    # Health check
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ System Online")
            health_data = response.json()
        else:
            st.error("❌ System Error")
            health_data = None
    except:
        st.error("❌ Cannot connect to backend")
        st.info("Start backend with: `python -m app.main`")
        health_data = None

    st.divider()

    # Get statistics
    if health_data:
        try:
            stats_response = requests.get(f"{API_URL}/statistics")
            if stats_response.status_code == 200:
                stats = stats_response.json()

                st.subheader("📊 System Statistics")
                st.metric("Documents Indexed", stats['documents']['count'])
                st.metric("Total Chunks", stats['vector_store']['main_collection_count'])
                st.metric("Active Sessions", stats['conversations']['active_sessions'])
                st.metric("Features Enabled", stats['settings']['features_enabled'])

                st.divider()

                # Configuration
                config_response = requests.get(f"{API_URL}/config")
                if config_response.status_code == 200:
                    config = config_response.json()

                    with st.expander("🔧 Configuration"):
                        st.write(f"**Model:** {config['model']}")
                        st.write(f"**Retrieval:** {config['retrieval']['final_k']} chunks")
                        st.write(f"**Reranking:** {'✓' if config['features']['reranking'] else '✗'}")
                        st.write(f"**Conversation Memory:** {'✓' if config['features']['conversation_memory'] else '✗'}")
        except:
            pass

    st.divider()

    # Actions
    st.subheader("🔄 Actions")

    if st.button("🗑️ Clear Conversations", use_container_width=True):
        try:
            requests.delete(f"{API_URL}/conversation")
            st.success("Cleared all conversations!")
            st.rerun()
        except:
            st.error("Failed to clear conversations")

    if st.button("⚠️ Clear Vector Store", use_container_width=True, type="secondary"):
        if st.session_state.get('confirm_clear', False):
            try:
                requests.delete(f"{API_URL}/vector-store")
                st.success("Cleared vector store!")
                st.session_state['confirm_clear'] = False
                st.rerun()
            except:
                st.error("Failed to clear vector store")
        else:
            st.session_state['confirm_clear'] = True
            st.warning("Click again to confirm")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📤 Upload Documents", "📚 View Documents", "📊 Analytics"])

# Tab 1: Chat Interface
with tab1:
    st.header("💬 Chat with Your Documents")

    # Session management
    col1, col2 = st.columns([3, 1])
    with col1:
        session_id = st.text_input("Session ID", value="default", help="Unique session for conversation memory")
    with col2:
        include_history = st.checkbox("Memory", value=True, help="Include conversation history")

    # Advanced filters
    with st.expander("🔍 Advanced Filters (Optional)"):
        col1, col2 = st.columns(2)

        with col1:
            # File filters
            try:
                docs_response = requests.get(f"{API_URL}/documents")
                if docs_response.status_code == 200:
                    docs = docs_response.json()
                    file_names = [doc['document_name'] for doc in docs]

                    if file_names:
                        file_filters = st.multiselect(
                            "Filter by Files",
                            options=file_names,
                            help="Only search in selected files"
                        )
                    else:
                        file_filters = []
                        st.info("No documents indexed yet")
                else:
                    file_filters = []
            except:
                file_filters = []

        with col2:
            # Date filters (placeholder for now)
            st.info("Date filtering coming soon!")
            date_filter = None

    # Chat interface
    st.divider()

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Show sources for assistant messages
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📁 Sources"):
                    for source in message["sources"]:
                        st.markdown(f"""
                        <div class="source-box">
                        <strong>{source['file_name']}</strong><br>
                        Type: {source['file_type']}<br>
                        Modified: {source['modified_date']}<br>
                        Chunks used: {source['chunk_count']}
                        </div>
                        """, unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Query the RAG system
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching documents and generating answer..."):
                try:
                    query_data = {
                        "question": prompt,
                        "session_id": session_id,
                        "include_history": include_history
                    }

                    if file_filters:
                        query_data["file_filters"] = file_filters

                    response = requests.post(f"{API_URL}/query", json=query_data)

                    if response.status_code == 200:
                        result = response.json()

                        # Display answer
                        st.markdown(result['answer'])

                        # Show metadata
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Confidence", f"{result['confidence']:.0%}")
                        with col2:
                            st.metric("Chunks Used", result['num_chunks_used'])
                        with col3:
                            st.metric("Files", len(result['files_used']))
                        with col4:
                            if result.get('tokens_used'):
                                st.metric("Tokens", f"{result['tokens_used']['total']:,}")

                        # Show sources
                        if result['sources']:
                            with st.expander("📁 Sources"):
                                for source in result['sources']:
                                    st.markdown(f"""
                                    <div class="source-box">
                                    <strong>{source['file_name']}</strong><br>
                                    Type: {source['file_type']}<br>
                                    Modified: {source['modified_date']}<br>
                                    Chunks used: {source['chunk_count']}
                                    </div>
                                    """, unsafe_allow_html=True)

                        # Add to chat history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result['answer'],
                            "sources": result['sources']
                        })

                    else:
                        st.error(f"Error: {response.status_code}")
                        st.json(response.json())

                except Exception as e:
                    st.error(f"Error querying system: {e}")

# Tab 2: Upload Documents
with tab2:
    st.header("📤 Upload & Process Documents")

    st.info("💡 Supports 30+ file formats: PDF, DOCX, PPTX, CSV, JSON, code files, and more!")

    upload_method = st.radio("Upload Method", ["📁 Upload Files", "📂 Process Folder"], horizontal=True)

    if upload_method == "📁 Upload Files":
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            help="Upload PDF, DOCX, PPTX, TXT, CSV, JSON, and more"
        )

        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} file(s)")

            # Show file details
            files_data = []
            for file in uploaded_files:
                files_data.append({
                    "Name": file.name,
                    "Type": file.type,
                    "Size": f"{file.size / 1024:.1f} KB"
                })

            st.dataframe(files_data, use_container_width=True)

            if st.button("🚀 Process Files", type="primary", use_container_width=True):
                with st.spinner("Processing documents..."):
                    try:
                        # Upload files
                        files = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]

                        response = requests.post(f"{API_URL}/upload/files", files=files)

                        if response.status_code == 200:
                            result = response.json()

                            st.success("✅ Documents processed successfully!")

                            # Show results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Documents", result['documents_processed'])
                            with col2:
                                st.metric("Chunks Created", result['chunks_created'])
                            with col3:
                                st.metric("Chunks Added", result['chunks_added'])

                            # Chunk types
                            if result.get('chunk_types'):
                                st.write("**Chunk Types:**")
                                st.json(result['chunk_types'])

                        else:
                            st.error(f"Error: {response.status_code}")
                            st.json(response.json())

                    except Exception as e:
                        st.error(f"Error processing files: {e}")

    else:  # Process Folder
        folder_path = st.text_input(
            "Folder Path",
            placeholder="/path/to/your/documents",
            help="Absolute path to folder containing documents"
        )

        if folder_path:
            folder = Path(folder_path)

            if folder.exists():
                # Count supported files
                supported_extensions = ['.pdf', '.docx', '.pptx', '.txt', '.csv', '.json', '.md']
                files = [f for f in folder.rglob("*") if f.suffix.lower() in supported_extensions]

                st.info(f"Found {len(files)} supported file(s) in folder")

                if files and st.button("🚀 Process Folder", type="primary", use_container_width=True):
                    with st.spinner(f"Processing {len(files)} documents..."):
                        try:
                            response = requests.post(
                                f"{API_URL}/upload/folder",
                                json={"folder_path": str(folder_path)}
                            )

                            if response.status_code == 200:
                                result = response.json()

                                st.success("✅ Folder processed successfully!")

                                # Show results
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Documents", result['documents_processed'])
                                with col2:
                                    st.metric("Chunks Created", result['chunks_created'])
                                with col3:
                                    st.metric("Chunks Added", result['chunks_added'])

                                # Chunk types
                                if result.get('chunk_types'):
                                    st.write("**Chunk Types:**")
                                    st.json(result['chunk_types'])

                            else:
                                st.error(f"Error: {response.status_code}")
                                st.json(response.json())

                        except Exception as e:
                            st.error(f"Error processing folder: {e}")
            else:
                st.warning("Folder does not exist")

# Tab 3: View Documents
with tab3:
    st.header("📚 Indexed Documents")

    try:
        response = requests.get(f"{API_URL}/documents")

        if response.status_code == 200:
            docs = response.json()

            if docs:
                st.write(f"Total documents: **{len(docs)}**")

                # Convert to dataframe
                df = pd.DataFrame(docs)

                # Format columns
                df['file_size_mb'] = (df['file_size'] / (1024 * 1024)).round(2)
                df['modified_date'] = pd.to_datetime(df['modified_date']).dt.strftime('%Y-%m-%d %H:%M')

                # Display
                st.dataframe(
                    df[['document_name', 'file_type', 'file_size_mb', 'modified_date', 'chunk_count']],
                    use_container_width=True,
                    column_config={
                        "document_name": "File Name",
                        "file_type": "Type",
                        "file_size_mb": "Size (MB)",
                        "modified_date": "Modified",
                        "chunk_count": "Chunks"
                    }
                )

                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download as CSV",
                    csv,
                    "documents.csv",
                    "text/csv"
                )
            else:
                st.info("No documents indexed yet. Upload some documents in the 'Upload Documents' tab!")

        else:
            st.error("Failed to fetch documents")

    except Exception as e:
        st.error(f"Error: {e}")

# Tab 4: Analytics
with tab4:
    st.header("📊 System Analytics")

    try:
        stats_response = requests.get(f"{API_URL}/statistics")

        if stats_response.status_code == 200:
            stats = stats_response.json()

            # Overview
            st.subheader("System Overview")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Documents", stats['documents']['count'])
            with col2:
                st.metric("Total Chunks", stats['vector_store']['main_collection_count'])
            with col3:
                st.metric("Parent Chunks", stats['vector_store']['parent_collection_count'])
            with col4:
                st.metric("Total Conversations", stats['conversations']['total_exchanges'])

            st.divider()

            # Configuration
            st.subheader("⚙️ System Configuration")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Model Configuration:**")
                st.code(f"""
Model: {stats['settings']['model']}
Max Context: {stats['settings']['max_context_tokens']:,} tokens
Retrieval K: {stats['settings']['retrieval_k']} chunks
                """)

            with col2:
                st.write("**Features Enabled:**")
                st.code(f"""
Total Features: {stats['settings']['features_enabled']}
Collections: {stats['vector_store']['total_collections']}
Cache Size: {stats['vector_store']['cache_size']}
                """)

            st.divider()

            # Documents breakdown
            if stats['documents']['count'] > 0:
                st.subheader("📁 Documents Breakdown")

                docs_df = pd.DataFrame(stats['documents']['list'])

                # File type distribution
                file_types = docs_df['file_type'].value_counts()
                st.bar_chart(file_types)

        else:
            st.error("Failed to fetch statistics")

    except Exception as e:
        st.error(f"Error: {e}")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p><strong>🚀 Ultimate RAG System v2.1</strong></p>
    <p>The Most Advanced Free-Tier RAG System Ever Built!</p>
    <p>Features: Multi-stage retrieval • Parent-child chunking • Semantic caching • 30+ file formats</p>
</div>
""", unsafe_allow_html=True)
