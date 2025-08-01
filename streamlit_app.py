import streamlit as st
import requests
import tempfile
import os
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Interview Screening System",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 1rem;
    }
    .status-box {
        background-color: #e8f5e8;
        border: 1px solid #4CAF50;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #4CAF50;
        border-radius: 50%;
        margin-right: 8px;
    }
    .chat-box {
        background-color: #f0f8ff;
        border: 1px solid #0066cc;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        background-color: #f9f9f9;
        margin: 15px 0;
    }
    .recording-section {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'recording_results' not in st.session_state:
    st.session_state.recording_results = None

# Backend URL
BACKEND_BASE_URL = "http://127.0.0.1:8000"
BACKEND_URL = f"{BACKEND_BASE_URL}/upload-audio-json/"

def check_backend_status():
    """Check if backend is online"""
    try:
        response = requests.get(f"{BACKEND_BASE_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def login_system(password):
    """Simple authentication system"""
    # In production, use proper authentication
    return password == "admin123"

# Main application
def main():
    # Header
    st.markdown('<h1 class="main-header">Interview Screening System</h1>', unsafe_allow_html=True)
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # System Status Section
        st.markdown('<h3 class="sub-header">System Status</h3>', unsafe_allow_html=True)
        
        backend_status = check_backend_status()
        if backend_status:
            st.markdown("""
            <div class="status-box">
                <span class="status-indicator"></span>
                <strong>Backend Online</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-box" style="background-color: #ffe8e8; border-color: #f44336;">
                <span class="status-indicator" style="background-color: #f44336;"></span>
                <strong>Backend Offline</strong>
            </div>
            """, unsafe_allow_html=True)
            st.error("⚠️ Backend is not running. Start with: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
    
    with col2:
        # Authentication Section
        if not st.session_state.authenticated:
            st.markdown('<h3 class="sub-header">Authentication Required</h3>', unsafe_allow_html=True)
            
            password = st.text_input("Enter Password", type="password")
            if st.button("🔐 Login", type="primary"):
                if login_system(password):
                    st.session_state.authenticated = True
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
            return
        
        # Main content after authentication
        st.markdown('<h3 class="sub-header">Interview Analysis Chat</h3>', unsafe_allow_html=True)
        
        # Session ID Input
        session_id = st.text_input(
            "Enter Candidate Session ID to Evaluate:",
            placeholder="Enter session ID of the candidate you want to evaluate",
            value=st.session_state.current_session_id or ""
        )
        
        if session_id:
            st.session_state.current_session_id = session_id
            st.success(f"✅ Session ID set: {session_id}")
        
        # Define recorder_html before audio input method selection
        recorder_html = f"""
        <div class="recording-section">
            <div style="text-align: center; padding: 20px;">
                <button id="recordButton" style="background-color: #ff4444; color: white; border: none; padding: 15px 30px; border-radius: 25px; font-size: 16px; cursor: pointer; margin: 10px;">
                    🎤 Start Recording
                </button>
                <button id="stopButton" style="background-color: #666; color: white; border: none; padding: 15px 30px; border-radius: 25px; font-size: 16px; cursor: pointer; margin: 10px; display: none;">
                    ⏹️ Stop & Process
                </button>
                <div id="status" style="margin: 10px; font-weight: bold; color: #666;">Ready to record</div>
                <div id="processingStatus" style="margin: 10px; font-weight: bold; color: #0066cc; display: none;">
                    Processing audio... Please wait
                </div>
                <audio id="audioPlayback" controls style="margin: 10px; display: none; width: 100%;"></audio>
                <div id="resultsSection" style="margin: 10px; display: none; text-align: left; padding: 15px; background-color: #f0f8ff; border-radius: 10px;">
                    <h4>🎯 Analysis Results:</h4>
                    <div id="transcriptionResult"></div>
                    <div id="candidateNameResult"></div>
                    <div id="faqResult"></div>
                    <div id="confirmationButtons" style="margin-top: 15px; text-align: center;">
                        <button id="confirmButton" style="background-color: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; margin: 5px; cursor: pointer;">
                            ✅ Confirm & Save
                        </button>
                        <button id="rejectButton" style="background-color: #f44336; color: white; border: none; padding: 10px 20px; border-radius: 5px; margin: 5px; cursor: pointer;">
                            ❌ Reject & Record Again
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        let mediaRecorder;
        let audioChunks = [];
        let isProcessing = false;
        let currentAudioBlob = null;
        
        async function sendAudioToBackend(audioBlob) {{
            const formData = new FormData();
            formData.append('file', audioBlob, 'recorded_audio.wav');
            
            try {{
                document.getElementById('processingStatus').style.display = 'block';
                document.getElementById('status').textContent = 'Sending to server...';
                // Add timeout using AbortController (5 minutes)
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 300000);
                const response = await fetch('{BACKEND_URL}', {{
                    method: 'POST',
                    body: formData,
                    mode: 'cors',
                    signal: controller.signal
                }});
                clearTimeout(timeoutId);
                
                if (response.ok) {{
                    const result = await response.json();
                    
                    // Get audio file separately
                    const audioResponse = await fetch('{BACKEND_BASE_URL}' + result.audio_url);
                    const audioData = await audioResponse.arrayBuffer();
                    const responseAudioBlob = new Blob([audioData], {{ type: 'audio/mp3' }});
                    const responseAudioUrl = URL.createObjectURL(responseAudioBlob);
                    
                    // Display results
                    document.getElementById('transcriptionResult').innerHTML = '<strong>Transcription:</strong> ' + (result.transcription || 'N/A');
                    document.getElementById('candidateNameResult').innerHTML = '<strong>Candidate Name:</strong> ' + (result.candidate_name || 'N/A');
                    document.getElementById('faqResult').innerHTML = '<strong>Matched FAQ:</strong> ' + (result.selected_faq || 'N/A');
                    
                    // Show results section
                    document.getElementById('resultsSection').style.display = 'block';
                    document.getElementById('status').textContent = 'Processing completed! Review and confirm below.';
                    document.getElementById('status').style.color = '#4CAF50';
                    
                    // Store results for confirmation
                    window.recordingResults = {{
                        transcription: result.transcription,
                        candidateName: result.candidate_name,
                        selectedFaq: result.selected_faq,
                        audioBlob: currentAudioBlob,
                        entities: result.entities
                    }};
                    
                }} else {{
                    const errorText = await response.text();
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}} - ${{errorText}}`);
                }}
            }} catch (error) {{
                console.error('Error sending audio:', error);
                document.getElementById('status').textContent = 'Error: ' + error.message;
                document.getElementById('status').style.color = '#ff0000';
            }} finally {{
                document.getElementById('processingStatus').style.display = 'none';
                isProcessing = false;
            }}
        }}
        
        document.getElementById('recordButton').addEventListener('click', async () => {{
            if (isProcessing) return;
            
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {{
                    audioChunks.push(event.data);
                }};
                
                mediaRecorder.onstop = async () => {{
                    if (isProcessing) return;
                    isProcessing = true;
                    
                    currentAudioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                    const audioUrl = URL.createObjectURL(currentAudioBlob);
                    document.getElementById('audioPlayback').src = audioUrl;
                    document.getElementById('audioPlayback').style.display = 'block';
                    
                    await sendAudioToBackend(currentAudioBlob);
                    
                    stream.getTracks().forEach(track => track.stop());
                }};
                
                mediaRecorder.start();
                document.getElementById('recordButton').style.display = 'none';
                document.getElementById('stopButton').style.display = 'inline-block';
                document.getElementById('status').textContent = 'Recording... Speak now!';
                document.getElementById('status').style.color = '#ff4444';
                
            }} catch (err) {{
                document.getElementById('status').textContent = 'Error: ' + err.message;
                document.getElementById('status').style.color = '#ff0000';
            }}
        }});
        
        document.getElementById('stopButton').addEventListener('click', () => {{
            if (mediaRecorder && mediaRecorder.state !== 'inactive' && !isProcessing) {{
                mediaRecorder.stop();
                document.getElementById('recordButton').style.display = 'inline-block';
                document.getElementById('stopButton').style.display = 'none';
            }}
        }});
        
        document.getElementById('confirmButton').addEventListener('click', () => {{
            if (window.recordingResults) {{
                document.getElementById('status').textContent = '✅ Confirmed! Results saved to session.';
                document.getElementById('status').style.color = '#4CAF50';
                
                // Send data to Streamlit
                const data = {{
                    action: 'confirm',
                    results: window.recordingResults
                }};
                
                setTimeout(() => {{
                    location.reload();
                }}, 2000);
            }}
        }});
        
        document.getElementById('rejectButton').addEventListener('click', () => {{
            document.getElementById('resultsSection').style.display = 'none';
            document.getElementById('audioPlayback').style.display = 'none';
            document.getElementById('recordButton').style.display = 'inline-block';
            document.getElementById('stopButton').style.display = 'none';
            document.getElementById('status').textContent = 'Ready to record again';
            document.getElementById('status').style.color = '#666';
            window.recordingResults = null;
        }});
        </script>
        """

        # Audio Input Method Selection
        audio_input_method = st.radio(
            "Choose audio input method:",
            ("Record Audio", "Upload File", "Test with Sample Audio"),
            horizontal=True
        )

        if audio_input_method == "Record Audio":
            # Audio recording HTML component (existing code)
            st.components.v1.html(recorder_html, height=400)
        elif audio_input_method == "Test with Sample Audio":
            # Sample Audio Testing Section
            st.markdown('<h4>🎧 Sample Audio Testing</h4>', unsafe_allow_html=True)
            st.info("Test the system with pre-recorded sample interviews to see how it works.")
            
            def reset_sample_processing_state():
                """Callback to reset state when a new sample is selected."""
                st.session_state.sample_processed = False
                st.session_state.processing_result = None
            
            # Fetch available sample files
            try:
                sample_response = requests.get(f"{BACKEND_BASE_URL}/sample-audio-files", timeout=10)
                if sample_response.status_code == 200:
                    sample_files = sample_response.json()["sample_files"]
                    
                    # Create a selection box for sample files
                    sample_options = {f"{k}: {v['description']} ({v['size']})": k for k, v in sample_files.items()}
                    selected_sample = st.selectbox(
                        "Choose a sample audio file to test:",
                        options=list(sample_options.keys()),
                        index=0,
                        on_change=reset_sample_processing_state
                    )
                    
                    if st.button("🚀 Test with Selected Sample", type="primary"):
                        sample_id = sample_options[selected_sample]
                        st.info(f"Testing with sample: {sample_id}")
                        
                        if not st.session_state.get('sample_processed', False):
                            st.success("New sample selected! Processing...")
                            with st.spinner("Processing sample audio... This may take a moment."):
                                try:
                                    # Test the sample audio
                                    test_response = requests.post(
                                        f"{BACKEND_BASE_URL}/test-sample-audio/{sample_id}",
                                        timeout=300
                                    )
                                    
                                    if test_response.status_code == 200:
                                        result = test_response.json()
                                        st.session_state.processing_result = result
                                        st.session_state.sample_processed = True
                                        st.success("✅ Sample audio processed successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error processing sample: {test_response.status_code} - {test_response.text}")
                                        st.session_state.processing_result = None
                                except Exception as e:
                                    st.error(f"An error occurred: {e}")
                                    st.session_state.processing_result = None
                            st.rerun() # Rerun once to display results cleanly
                    
                    # Display sample file details
                    with st.expander("📋 Sample File Details"):
                        for sample_id, details in sample_files.items():
                            st.write(f"**{sample_id}**: {details['description']} ({details['size']})")
                    
                    # Display results if they exist in the session state (for sample audio)
                    if st.session_state.get('processing_result') and st.session_state.processing_result.get('sample_file_used'):
                        result = st.session_state.processing_result
                        st.subheader("Sample Audio Analysis:")
                        st.info(f"Analysis complete for sample: {result.get('sample_file_used')} - {result.get('sample_description', '')}")
                        st.subheader("Analysis Results:")
                        st.metric("Candidate Name", result.get('candidate_name', 'N/A'))
                        st.metric("Years of Experience", result.get('years_experience', 'N/A'))
                        st.metric("Desired Role", result.get('desired_role', 'N/A'))
                        with st.expander("View Full Transcription"):
                            st.write(result.get('transcription', 'N/A'))
                        with st.expander("View Extracted Skills"):
                            st.json(result.get('skills', []))
                            
                else:
                    st.error("Failed to fetch sample audio files from backend")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
                st.info("Make sure the backend is running to access sample files.")
        else:
            def reset_processing_state():
                """Callback to reset state when a new file is uploaded."""
                st.session_state.file_processed = False
                st.session_state.processing_result = None

            # Audio file upload
            uploaded_file = st.file_uploader(
                "Upload your audio file (.wav or .webm)", 
                type=["wav", "webm"],
                on_change=reset_processing_state
            )

            if uploaded_file is not None:
                if not st.session_state.get('file_processed', False):
                    st.success("New audio file detected! Processing...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_file_path = tmp_file.name
                    with st.spinner("Performing one-time analysis... This may take a moment."):
                        try:
                            with open(tmp_file_path, "rb") as f:
                                files = {"file": (uploaded_file.name, f, uploaded_file.type)}
                                json_response = requests.post(BACKEND_URL, files=files, timeout=300)
                                
                                if json_response.status_code == 200:
                                    result = json_response.json()
                                    st.session_state.processing_result = result
                                    st.session_state.file_processed = True # Mark as processed
                                else:
                                    st.error(f"Error processing audio: {json_response.status_code} - {json_response.text}")
                                    st.session_state.processing_result = None
                        except Exception as e:
                            st.error(f"An error occurred: {e}")
                            st.session_state.processing_result = None
                        finally:
                            if os.path.exists(tmp_file_path):
                                os.unlink(tmp_file_path)
                    st.rerun() # Rerun once to display results cleanly

            # Display results if they exist in the session state
            if st.session_state.get('processing_result'):
                result = st.session_state.processing_result
                
                # Determine if this is a sample or uploaded file
                is_sample = result.get('sample_file_used') is not None
                
                if is_sample:
                    st.subheader("Sample Audio Analysis:")
                    st.info(f"Analysis complete for sample: {result.get('sample_file_used')} - {result.get('sample_description', '')}")
                else:
                    st.subheader("Your Recording:")
                    st.info("Analysis is complete for the uploaded audio file.")
                
                st.subheader("Analysis Results:")
                st.metric("Candidate Name", result.get('candidate_name', 'N/A'))
                st.metric("Years of Experience", result.get('years_experience', 'N/A'))
                st.metric("Desired Role", result.get('desired_role', 'N/A'))
                with st.expander("View Full Transcription"):
                    st.write(result.get('transcription', 'N/A'))
                with st.expander("View Extracted Skills"):
                    st.json(result.get('skills', []))

        # FAQ Section - Only show if we have results from either upload or sample
        if 'processing_result' in st.session_state and st.session_state.processing_result:
            st.markdown('<h4>❓ Dynamically Generated FAQ</h4>', unsafe_allow_html=True)
            faq_data = st.session_state.processing_result.get('faq')

            if faq_data:
                st.markdown("<b>Suggested Questions Based on Transcript:</b>", unsafe_allow_html=True)
                
                faq_dict = {item['question']: item['answer'] for item in faq_data}
                
                selected_question = st.radio(
                    "Select a question for on-demand audio:",
                    list(faq_dict.keys()),
                    key="faq_radio"
                )

                if selected_question:
                    st.info(f"**Answer:** {faq_dict[selected_question]}")

                if st.button("🔊 Generate Audio for Selected Answer"):
                    if selected_question:
                        with st.spinner("Generating audio for the answer..."):
                            try:
                                selected_faq_obj = {"question": selected_question, "answer": faq_dict[selected_question]}
                                tts_response = requests.post(
                                    f"{BACKEND_BASE_URL}/tts-for-faq/",
                                    json={"faq": selected_faq_obj},
                                    timeout=60
                                )
                                if tts_response.status_code == 200:
                                    tts_data = tts_response.json()
                                    tts_audio_url = tts_data.get("audio_url")
                                    if tts_audio_url:
                                        audio_response = requests.get(f"{BACKEND_BASE_URL}{tts_audio_url}")
                                        if audio_response.status_code == 200:
                                            st.audio(audio_response.content, format="audio/mp3")
                                        else:
                                            st.error(f"Error fetching TTS audio: {audio_response.status_code}")
                                else:
                                    st.error(f"TTS generation failed: {tts_response.status_code} - {tts_response.text}")
                            except Exception as e:
                                st.error(f"Error during TTS generation: {str(e)}")
            else:
                st.info("No FAQ data available for this transcript.")
        else:
            st.info("Process an audio file or test with a sample to see dynamically generated FAQs and listen to their answers here.")

        # Manual FAQ Section - Only show if we have results from either upload or sample
        if 'processing_result' in st.session_state and st.session_state.processing_result:
            st.markdown('<h4>✍️ Ask a Custom Question</h4>', unsafe_allow_html=True)
            transcription = st.session_state.processing_result.get('transcription')

            # This form structure is now correct and will not lose the input
            with st.form(key="manual_faq_form"):
                st.text_input(
                    "Enter your own question about the transcript:",
                    key="manual_question_input"  # The key that saves the input state
                )
                submit_button = st.form_submit_button("Get Answer for Custom Question")

                if submit_button:
                    # We read the value from session_state, which is preserved
                    manual_question = st.session_state.get("manual_question_input", "").strip()
                    if manual_question and transcription:
                        with st.spinner("Getting answer from AI..."):
                            try:
                                response = requests.post(
                                    f"{BACKEND_BASE_URL}/answer-manual-faq/",
                                    json={"transcription": transcription, "question": manual_question},
                                    timeout=120
                                )
                                if response.status_code == 200:
                                    # We save the result and clear any old audio
                                    st.session_state.manual_faq_result = {
                                        "question": manual_question,
                                        "answer": response.json().get("answer")
                                    }
                                else:
                                    st.error(f"Failed to get answer: {response.text}")
                                    st.session_state.manual_faq_result = None
                            except Exception as e:
                                st.error(f"An error occurred: {e}")
                                st.session_state.manual_faq_result = None
                    else:
                        st.warning("Please enter a question.")
                        st.session_state.manual_faq_result = None
                    
                    # Force a single rerun to update the display -- THIS WAS THE BUG
                    # st.rerun() # REMOVING THIS LINE

            # The display logic is now outside the form and reads from the session state
            if 'manual_faq_result' in st.session_state and st.session_state.manual_faq_result:
                manual_faq = st.session_state.manual_faq_result
                st.markdown(f"**Q: {manual_faq['question']}**")
                st.info(f"**A:** {manual_faq['answer']}")
                
                if st.button("🔊 Generate Audio for Custom Answer", key="tts_for_manual_faq"):
                    with st.spinner("Generating audio..."):
                        try:
                            tts_response = requests.post(
                                f"{BACKEND_BASE_URL}/tts-for-faq/",
                                json={"faq": manual_faq},
                                timeout=60
                            )
                            if tts_response.status_code == 200:
                                tts_data = tts_response.json()
                                tts_audio_url = tts_data.get("audio_url")
                                if tts_audio_url:
                                    audio_response = requests.get(f"{BACKEND_BASE_URL}{tts_audio_url}")
                                    if audio_response.status_code == 200:
                                        # Save audio to state to prevent it from disappearing
                                        st.session_state.manual_faq_audio = audio_response.content
                            else:
                                st.error(f"TTS generation failed: {tts_response.text}")
                        except Exception as e:
                            st.error(f"Error generating TTS: {e}")
                
                # Display the audio if it exists in the state
                if 'manual_faq_audio' in st.session_state and st.session_state.manual_faq_audio:
                    st.audio(st.session_state.manual_faq_audio, format="audio/mp3")

        else:
            st.info("Process an audio file or test with a sample first to ask a custom question.")

    # Logout button at bottom
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.authenticated = False
            st.session_state.current_session_id = None
            st.session_state.chat_history = []
            st.rerun()

if __name__ == "__main__":
    main() 