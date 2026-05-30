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
.subtitle { text-align: center; color: #666; margin-bottom: 20px; font-size: 14px; }
.lang-label { text-align: center; font-size: 12px; color: #999; margin-bottom: 8px; }
.lang-section { display: flex; gap: 10px; margin-bottom: 20px; }
.lang-btn { flex: 1; padding: 10px; border: 2px solid #ddd; background: white; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 15px; transition: all 0.3s; }
.lang-btn.active { background: #667eea; color: white; border-color: #667eea; }
.tabs { display: flex; gap: 10px; margin-bottom: 30px; }
.tab-btn { flex: 1; padding: 12px; border: 2px solid #ddd; background: white; border-radius: 10px; cursor: pointer; font-weight: 600; transition: all 0.3s; }
.tab-btn.active { background: #667eea; color: white; border-color: #667eea; }
.tab { display: none; }
.tab.active { display: block; }
input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
.record-section { text-align: center; margin: 20px 0; }
.record-btn { width: 100px; height: 100px; border-radius: 50%; border: none; background: #667eea; color: white; font-size: 40px; cursor: pointer; margin: 0 auto; transition: all 0.3s; display: flex; align-items: center; justify-content: center; }
.record-btn:hover { background: #764ba2; }
.record-btn.recording { background: #ff4757; animation: pulse 1s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
.status { text-align: center; color: #666; font-size: 13px; margin-top: 10px; }
.main-btn { width: 100%; padding: 12px; border: none; border-radius: 8px; background: #667eea; color: white; cursor: pointer; font-weight: 600; margin-bottom: 10px; transition: all 0.3s; font-size: 15px; }
.main-btn:hover { background: #764ba2; }
.main-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.download-btn { width: 100%; padding: 10px; border: 2px solid #2ed573; border-radius: 8px; background: white; color: #2ed573; cursor: pointer; font-weight: 600; margin-bottom: 10px; transition: all 0.3s; font-size: 14px; }
.download-btn:hover { background: #2ed573; color: white; }
.clear-btn { width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 8px; background: white; color: #999; cursor: pointer; font-weight: 600; margin-bottom: 10px; transition: all 0.3s; font-size: 14px; }
.clear-btn:hover { border-color: #ff4757; color: #ff4757; }
.result { background: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 10px; display: none; }
.result.show { display: block; }
.result-title { font-weight: 600; margin-bottom: 8px; color: #333; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
.result-text { font-size: 14px; line-height: 1.6; color: #555; white-space: pre-wrap; }
.divider { border: none; border-top: 1px solid #ddd; margin: 12px 0; }
</style>
</head>
<body>
<div class="container">
<h1>🤝 MediMeeting</h1>
<p class="subtitle">Record and summarize meetings</p>

<div class="lang-label">Valitse kieli / Choose language:</div>
<div class="lang-section">
<button class="lang-btn active" id="lang_fi" onclick="setLang('fi')">🇫🇮 Suomi</button>
<button class="lang-btn" id="lang_en" onclick="setLang('en')">🇬🇧 English</button>
</div>

<div class="tabs">
<button class="tab-btn active" id="tab_meeting" onclick="switchTab('meeting')">🤝 Meeting</button>
<button class="tab-btn" id="tab_call" onclick="switchTab('call')">☎️ Call</button>
</div>

<div id="meeting" class="tab active">
<input type="text" id="meeting_title" placeholder="Meeting title...">
<div class="record-section">
<button class="record-btn" id="meeting_btn" onclick="toggleRecord('meeting')">🎙️</button>
<div class="status" id="meeting_status">Click to record</div>
</div>
<button class="main-btn" id="meeting_submit" onclick="process('meeting')" disabled>✨ Create Summary</button>
<button class="download-btn" id="meeting_download" onclick="downloadAndClear('meeting')" style="display:none">💾 Download & Save / Tallenna</button>
<button class="clear-btn" onclick="clearResult('meeting')">🗑️ Clear / Tyhjennä</button>
<div id="meeting_result" class="result">
<div class="result-title">🎙️ Transkripti / Transcript</div>
<div class="result-text" id="meeting_transcript"></div>
<hr class="divider">
<div class="result-title" id="meeting_summary_fi_label" style="display:none">🇫🇮 Yhteenveto (Suomi)</div>
<div class="result-text" id="meeting_summary_fi" style="display:none"></div>
<hr class="divider" id="meeting_divider2" style="display:none">
<div class="result-title">🇬🇧 Summary (English)</div>
<div class="result-text" id="meeting_summary_en"></div>
</div>
</div>

<div id="call" class="tab">
<input type="text" id="call_with" placeholder="Call with...">
<input type="text" id="call_topic" placeholder="Call topic...">
<div class="record-section">
<button class="record-btn" id="call_btn" onclick="toggleRecord('call')">🎙️</button>
<div class="status" id="call_status">Click to record</div>
</div>
<button class="main-btn" id="call_submit" onclick="process('call')" disabled>✨ Create Summary</button>
<button class="download-btn" id="call_download" onclick="downloadAndClear('call')" style="display:none">💾 Download & Save / Tallenna</button>
<button class="clear-btn" onclick="clearResult('call')">🗑️ Clear / Tyhjennä</button>
<div id="call_result" class="result">
<div class="result-title">🎙️ Transkripti / Transcript</div>
<div class="result-text" id="call_transcript"></div>
<hr class="divider">
<div class="result-title" id="call_summary_fi_label" style="display:none">🇫🇮 Yhteenveto (Suomi)</div>
<div class="result-text" id="call_summary_fi" style="display:none"></div>
<hr class="divider" id="call_divider2" style="display:none">
<div class="result-title">🇬🇧 Summary (English)</div>
<div class="result-text" id="call_summary_en"></div>
</div>
</div>
</div>

<script>
let mediaRecorder;
let audioChunks = [];
let recording = { meeting: false, call: false };
let recordedAudio = { meeting: null, call: null };
let selectedLang = 'fi';

function setLang(lang) {
selectedLang = lang;
document.querySelectorAll('.lang-btn').forEach(el => el.classList.remove('active'));
document.getElementById('lang_' + lang).classList.add('active');
}

function switchTab(tab) {
document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
document.getElementById(tab).classList.add('active');
document.getElementById('tab_' + tab).classList.add('active');
}

function downloadAndClear(tab) {
const title = document.getElementById(tab === 'meeting' ? 'meeting_title' : 'call_with').value || tab;
const transcript = document.getElementById(tab + '_transcript').textContent;
const summaryFi = document.getElementById(tab + '_summary_fi').textContent;
const summaryEn = document.getElementById(tab + '_summary_en').textContent;

let content = `MEDIMEETING - ${title}\n`;
content += `Date: ${new Date().toLocaleString('fi-FI')}\n`;
content += `${'='.repeat(50)}\n\n`;
content += `TRANSKRIPTI / TRANSCRIPT:\n${transcript}\n\n`;
if (summaryFi) {
content += `YHTEENVETO (SUOMI):\n${summaryFi}\n\n`;
}
content += `SUMMARY (ENGLISH):\n${summaryEn}\n`;

const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = `medimeeting_${title.replace(/\s+/g,'_')}_${new Date().toISOString().slice(0,10)}.txt`;
a.click();
URL.revokeObjectURL(url);

setTimeout(() => clearResult(tab), 500);
}

function clearResult(tab) {
document.getElementById(tab + '_transcript').textContent = '';
document.getElementById(tab + '_summary_en').textContent = '';
document.getElementById(tab + '_summary_fi').textContent = '';
document.getElementById(tab + '_summary_fi').style.display = 'none';
document.getElementById(tab + '_summary_fi_label').style.display = 'none';
document.getElementById(tab + '_divider2').style.display = 'none';
document.getElementById(tab + '_result').classList.remove('show');
document.getElementById(tab + '_submit').disabled = true;
document.getElementById(tab + '_download').style.display = 'none';
recordedAudio[tab] = null;
document.getElementById(tab + '_status').textContent = 'Click to record';
document.getElementById(tab + '_btn').textContent = '🎙️';
}

async function toggleRecord(tab) {
if (!recording[tab]) {
try {
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
mediaRecorder = new MediaRecorder(stream);
audioChunks = [];
mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
mediaRecorder.onstop = () => {
recordedAudio[tab] = new Blob(audioChunks, { type: 'audio/webm' });
document.getElementById(tab + '_submit').disabled = false;
};
mediaRecorder.start();
recording[tab] = true;
document.getElementById(tab + '_btn').textContent = '⏹️';
document.getElementById(tab + '_btn').classList.add('recording');
document.getElementById(tab + '_status').textContent = selectedLang === 'fi' ? 'Nauhoitetaan...' : 'Recording...';
} catch (e) {
alert('Microphone error: ' + e.message);
}
} else {
mediaRecorder.stop();
mediaRecorder.stream.getTracks().forEach(t => t.stop());
recording[tab] = false;
document.getElementById(tab + '_btn').textContent = '🎙️';
document.getElementById(tab + '_btn').classList.remove('recording');
document.getElementById(tab + '_status').textContent = selectedLang === 'fi' ? 'Valmis! Paina Create Summary.' : 'Done! Press Create Summary.';
}
}

async function process(tab) {
if (!recordedAudio[tab]) return;
const btn = document.getElementById(tab + '_submit');
btn.disabled = true;
btn.textContent = selectedLang === 'fi' ? '⏳ Käsitellään...' : '⏳ Processing...';
try {
const formData = new FormData();
formData.append('audio', recordedAudio[tab], 'audio.webm');
formData.append('lang', selectedLang);
const transcribeRes = await fetch('/transcribe', { method: 'POST', body: formData });
const transcribeData = await transcribeRes.json();
if (!transcribeRes.ok) throw new Error(transcribeData.error);

const summarizeRes = await fetch('/summarize', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ text: transcribeData.text, lang: selectedLang })
});
const summarizeData = await summarizeRes.json();
if (!summarizeRes.ok) throw new Error(summarizeData.error);

document.getElementById(tab + '_transcript').textContent = transcribeData.text;
document.getElementById(tab + '_summary_en').textContent = summarizeData.summary_en;

if (selectedLang === 'fi' && summarizeData.summary_fi) {
document.getElementById(tab + '_summary_fi').textContent = summarizeData.summary_fi;
document.getElementById(tab + '_summary_fi').style.display = 'block';
document.getElementById(tab + '_summary_fi_label').style.display = 'block';
document.getElementById(tab + '_divider2').style.display = 'block';
} else {
document.getElementById(tab + '_summary_fi').style.display = 'none';
document.getElementById(tab + '_summary_fi_label').style.display = 'none';
document.getElementById(tab + '_divider2').style.display = 'none';
}

document.getElementById(tab + '_result').classList.add('show');
document.getElementById(tab + '_download').style.display = 'block';
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
        lang = request.form.get('lang', 'fi')
        whisper_lang = 'fi' if lang == 'fi' else 'en'
        r = requests.post(
            'https://api.openai.com/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
            files={'file': ('audio.webm', audio_file.read(), 'audio/webm')},
            data={'model': 'whisper-1', 'language': whisper_lang},
            timeout=60
        )
        if r.status_code != 200:
            return jsonify({'error': r.text}), 500
        return jsonify({'text': r.json()['text']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.json
        text = data['text']
        lang = data.get('lang', 'fi')

        if lang == 'fi':
            prompt = f"""Olet lääketieteellinen sihteeri. Sinulle annetaan suomenkielinen kokouksen transkripti.

Tee kaksi yhteenvetoa:
1. SUOMEKSI: Lyhyt yhteenveto 2-3 lauseella suomeksi.
2. ENGLANNIKSI: Short summary in 2-3 sentences in English.

Vastaa TÄSMÄLLEEN tässä muodossa (älä lisää muuta tekstiä):
SUOMI: [suomenkielinen yhteenveto]
ENGLISH: [english summary]

Transkripti: {text}"""
        else:
            prompt = f"Summarize the following meeting transcript in 2-3 sentences in English:\n\n{text}"

        r = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 600,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=30
        )
        if r.status_code != 200:
            return jsonify({'error': 'Summary failed'}), 500

        response_text = r.json()['content'][0]['text']

        if lang == 'fi':
            summary_fi = ''
            summary_en = ''
            for line in response_text.split('\n'):
                line = line.strip()
                if line.startswith('SUOMI:'):
                    summary_fi = line.replace('SUOMI:', '').strip()
                elif line.startswith('ENGLISH:'):
                    summary_en = line.replace('ENGLISH:', '').strip()
            return jsonify({'summary_fi': summary_fi, 'summary_en': summary_en})
        else:
            return jsonify({'summary_fi': '', 'summary_en': response_text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
