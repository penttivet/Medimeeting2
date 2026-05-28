from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MediMeeting</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
.container { background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 500px; width: 100%; padding: 40px; }
h1 { text-align: center; color: #333; margin-bottom: 10px; font-size: 32px; }
.subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }
.tabs { display: flex; gap: 10px; margin-bottom: 30px; }
.tab-btn { flex: 1; padding: 12px; border: 2px solid #ddd; background: white; border-radius: 10px; cursor: pointer; font-weight: 600; transition: all 0.3s; }
.tab-btn.active { background: #667eea; color: white; border-color: #667eea; }
.tab { display: none; }
.tab.active { display: block; }
input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
.record-section { text-align: center; margin: 30px 0; }
.record-btn { width: 100px; height: 100px; border-radius: 50%; border: none; background: #667eea; color: white; font-size: 40px; cursor: pointer; margin: 0 auto; transition: all 0.3s; }
.record-btn:hover { background: #764ba2; }
.record-btn.recording { background: #ff4757; animation: pulse 1s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
.status { text-align: center; color: #666; font-size: 13px; margin-top: 10px; }
button { width: 100%; padding: 12px; border: none; border-radius: 8px; background: #667eea; color: white; cursor: pointer; font-weight: 600; margin-bottom: 10px; transition: all 0.3s; }
button:hover { background: #764ba2; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.result { background: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 20px; display: none; }
.result.show { display: block; }
.result-title { font-weight: 600; margin-bottom: 10px; color: #333; }
.result-text { font-size: 14px; line-height: 1.6; color: #666; white-space: pre-wrap; }
</style>
</head>
<body>
<div class="container">
<h1>🤝 MediMeeting</h1>
<p class="subtitle">Record and summarize meetings</p>
<div class="tabs">
<button class="tab-btn active" onclick="switchTab('meeting')">🤝 Meeting</button>
<button class="tab-btn" onclick="switchTab('call')">☎️ Call</button>
</div>
<div id="meeting" class="tab active">
<input type="text" id="meeting_title" placeholder="Meeting title...">
<div class="record-section">
<button class="record-btn" id="meeting_btn" onclick="toggleRecord('meeting')">🎙️</button>
<div class="status" id="meeting_status">Click to record</div>
</div>
<button id="meeting_submit" onclick="process('meeting')" disabled>✨ Create Summary</button>
<div id="meeting_result" class="result">
<div class="result-title">Transcript</div>
<div class="result-text" id="meeting_transcript"></div>
<div class="result-title" style="margin-top: 15px;">Summary</div>
<div class="result-text" id="meeting_summary"></div>
</div>
</div>
<div id="call" class="tab">
<input type="text" id="call_with" placeholder="Call with...">
<input type="text" id="call_topic" placeholder="Call topic...">
<div class="record-section">
<button class="record-btn" id="call_btn" onclick="toggleRecord('call')">🎙️</button>
<div class="status" id="call_status">Click to record</div>
</div>
<button id="call_submit" onclick="process('call')" disabled>✨ Create Summary</button>
<div id="call_result" class="result">
<div class="result-title">Transcript</div>
<div class="result-text" id="call_transcript"></div>
<div class="result-title" style="margin-top: 15px;">Summary</div>
<div class="result-text" id="call_summary"></div>
</div>
</div>
</div>
<script>
let mediaRecorder;
let audioChunks = [];
let recording = { meeting: false, call: false };
let recordedAudio = { meeting: null, call: null };
function switchTab(tab) {
document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
document.getElementById(tab).classList.add('active');
event.target.classList.add('active');
}
async function toggleRecord(tab) {
if (!recording[tab]) {
try {
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
mediaRecorder = new MediaRecorder(stream);
       
       
audioChunks = [];
mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
mediaRecorder.onstop = () => {
recordedAudio[tab] = new Blob(audioChunks, { type: 'audio/mp4' 
});
document.getElementById(tab + '_submit').disabled = false;
};
mediaRecorder.start();
recording[tab] = true;
document.getElementById(tab + '_btn').textContent = '⏹️';
document.getElementById(tab + '_btn').classList.add('recording');
document.getElementById(tab + '_status').textContent = 'Recording...';
} catch (e) {
alert('Microphone error: ' + e.message);
}
} else {
mediaRecorder.stop();
mediaRecorder.stream.getTracks().forEach(t => t.stop());
recording[tab] = false;
document.getElementById(tab + '_btn').textContent = '🎙️';
document.getElementById(tab + '_btn').classList.remove('recording');
document.getElementById(tab + '_status').textContent = 'Done';
}
}
async function process(tab) {
if (!recordedAudio[tab]) return;
const btn = document.getElementById(tab + '_submit');
btn.disabled = true;
btn.textContent = '⏳ Processing...';
try {
const formData = new FormData();
formData.append('audio', recordedAudio[tab], 'audio.webm');
const transcribeRes = await fetch('/transcribe', {
method: 'POST',
body: formData
});
const transcribeData = await transcribeRes.json();
if (!transcribeRes.ok) throw new Error(transcribeData.error);
const summarizeRes = await fetch('/summarize', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
text: transcribeData.text,
tab: tab,
title: document.getElementById(tab + '_title')?.value || '',
with: document.getElementById(tab + '_with')?.value || '',
topic: document.getElementById(tab + '_topic')?.value || ''
})
});
const summarizeData = await summarizeRes.json();
if (!summarizeRes.ok) throw new Error(summarizeData.error);
document.getElementById(tab + '_transcript').textContent = transcribeData.text;
document.getElementById(tab + '_summary').textContent = summarizeData.summary;
document.getElementById(tab + '_result').classList.add('show');
} catch (e) {
alert('Error: ' + e.message);
} finally {
btn.disabled = false;
btn.textContent = '✨ Create Summary';
}
}
</script>
</body>
</html>"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        audio_file = request.files['audio']
        r = requests.post(
            'https://api.openai.com/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
            files={'file': ('audio.webm', audio_file.read(), 'audio/webm')},
            data={'model': 'whisper-1'},
            timeout=60
        )
        if r.status_code != 200:
               print("OPENAI TRANSCRIBE RESPONSE:", r.status_code,r.text)
            return jsonify({'error': r.text}), 500
        return jsonify({'text': r.json()['text']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.json
        text = data['text']
        r = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 300,
                'messages': [{'role': 'user', 'content': f'Summarize in 2-3 sentences: {text}'}]
            },
            timeout=30
        )
        if r.status_code != 200:
            return jsonify({'error': 'Summary failed'}), 500
        summary = r.json()['content'][0]['text']
        return jsonify({'summary': summary})
    except Exception as e:
        print("TRANSCRIBE ERROR:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



