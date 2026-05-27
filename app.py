app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MediMeeting</title>
</head>
<body style="font-family: Arial; background: linear-gradient(135deg,#667eea,#764ba2); min-height:100vh; display:flex; align-items:center; justify-content:center;">
<div style="background:white; padding:40px; border-radius:20px; max-width:500px; width:90%; text-align:center;">
<h1>🤝 MediMeeting</h1>
<p>Record and summarize meetings</p>

<input id="meeting_title" placeholder="Meeting title..." style="width:100%; padding:12px; margin:15px 0;">

<button id="recordBtn" onclick="toggleRecord()" style="font-size:40px; border-radius:50%; width:100px; height:100px;">🎙️</button>
<p id="status">Click to record</p>

<button id="submitBtn" onclick="processAudio()" disabled style="width:100%; padding:12px;">✨ Create Summary</button>

<h3>Transcript</h3>
<pre id="transcript" style="white-space:pre-wrap; text-align:left;"></pre>

<h3>Summary</h3>
<pre id="summary" style="white-space:pre-wrap; text-align:left;"></pre>
</div>

<script>
let mediaRecorder;
let audioChunks = [];
let recordedAudio = null;
let recording = false;

async function toggleRecord() {
if (!recording) {
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

let options = {};
if (MediaRecorder.isTypeSupported('audio/mp4')) {
options = { mimeType: 'audio/mp4' };
} else if (MediaRecorder.isTypeSupported('audio/webm')) {
options = { mimeType: 'audio/webm' };
}

mediaRecorder = new MediaRecorder(stream, options);
audioChunks = [];

mediaRecorder.ondataavailable = e => {
if (e.data.size > 0) audioChunks.push(e.data);
};

mediaRecorder.onstop = () => {
recordedAudio = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/mp4' });
document.getElementById('submitBtn').disabled = false;
};

mediaRecorder.start();
recording = true;
document.getElementById('recordBtn').textContent = '⏹️';
document.getElementById('status').textContent = 'Recording...';
} else {
mediaRecorder.stop();
mediaRecorder.stream.getTracks().forEach(t => t.stop());
recording = false;
document.getElementById('recordBtn').textContent = '🎙️';
document.getElementById('status').textContent = 'Done';
}
}

async function processAudio() {
const btn = document.getElementById('submitBtn');
btn.disabled = true;
btn.textContent = '⏳ Processing...';

try {
const formData = new FormData();
formData.append('audio', recordedAudio, 'audio.m4a');

const transcribeRes = await fetch('/transcribe', {
method: 'POST',
body: formData
});

const transcribeData = await transcribeRes.json();
if (!transcribeRes.ok) throw new Error(transcribeData.error);

document.getElementById('transcript').textContent = transcribeData.text;

const summarizeRes = await fetch('/summarize', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ text: transcribeData.text })
});

const summarizeData = await summarizeRes.json();
if (!summarizeRes.ok) throw new Error(summarizeData.error);

document.getElementById('summary').textContent = summarizeData.summary;

} catch (e) {
alert('Error: ' + e.message);
} finally {
btn.disabled = false;
btn.textContent = '✨ Create Summary';
}
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
audio_file = request.files["audio"]

r = requests.post(
"https://api.openai.com/v1/audio/transcriptions",
headers={
"Authorization": f"Bearer {OPENAI_API_KEY}"
},
files={
"file": (
audio_file.filename or "audio.m4a",
audio_file.read(),
audio_file.mimetype or "audio/mp4"
)
},
data={
"model": "whisper-1"
},
timeout=60
)

print("OPENAI TRANSCRIBE RESPONSE:", r.status_code, r.text)

if r.status_code != 200:
return jsonify({"error": r.text}), 500

return jsonify({"text": r.json().get("text", "")})

except Exception as e:
print("TRANSCRIBE ERROR:", str(e))
return jsonify({"error": str(e)}), 500

@app.route("/summarize", methods=["POST"])
def summarize():
try:
data = request.json
text = data.get("text", "")

prompt = f"Summarize this meeting in 2-3 clear sentences:\\n\\n{text}"

r = requests.post(
"https://api.openai.com/v1/chat/completions",
headers={
"Authorization": f"Bearer {OPENAI_API_KEY}",
"Content-Type": "application/json"
},
json={
"model": "gpt-4o-mini",
"messages": [
{"role": "user", "content": prompt}
]
},
timeout=60
)

print("OPENAI SUMMARY RESPONSE:", r.status_code, r.text)

if r.status_code != 200:
return jsonify({"error": r.text}), 500

summary = r.json()["choices"][0]["message"]["content"]
return jsonify({"summary": summary})

except Exception as e:
print("SUMMARY ERROR:", str(e))
return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
port = int(os.environ.get("PORT", 8080))
app.run(host="0.0.0.0", port=port)
                     
