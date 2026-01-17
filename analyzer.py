import streamlit as st
import sys

# --- 1. CONFIG (WAJIB BARIS PERTAMA) ---
st.set_page_config(page_title="YouTube Command Center V18", page_icon="✅", layout="wide")

# --- DEBUGGER ---
print("--- STARTING V18 ---")

# --- 2. IMPORT LIBRARY ---
try:
    import re
    import random
    import datetime
    import requests
    import statistics
    import pandas as pd
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    print("✓ Library Loaded")
except ImportError as e:
    st.error(f"Library Error: {e}")
    st.stop()

# --- 3. DATABASE CONFIG ---
URL_DATABASE_ONLINE = "https://gist.githubusercontent.com/rhanierex/f2d76f11df8d550376d81b58124d3668/raw/0b58a1eb02a7cffc2261a1c8d353551f3337001c/gistfile1.txt"
FALLBACK_POWER_WORDS = ["secret", "best", "exposed", "tutorial", "guide"]
VIRAL_EMOJIS = ["🔥", "😱", "🔴", "✅", "❌", "🎵", "⚠️", "⚡", "🚀", "💰", "💯", "🤯", "😭", "😡", "😴", "🌙", "✨", "💤", "🌧️", "🎹"]
STOP_WORDS = ["the", "and", "or", "for", "to", "in", "on", "at", "by", "with", "video", "dan", "di", "ke", "dari"]

# --- 4. LOAD DATA ---
@st.cache_data(ttl=600) 
def load_power_words(url):
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list): return data, "🟢 Online"
            except: pass
    except: pass
    return FALLBACK_POWER_WORDS, "🟠 Offline"

POWER_WORDS_DB, db_status = load_power_words(URL_DATABASE_ONLINE)

# --- 5. LOGIC FUNCTIONS ---
def clean_title_text(title, keyword):
    if not keyword: return title[:40]
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    clean = pattern.sub("", title).strip()
    clean = re.sub(r'^[:\-\|]\s*', '', clean)
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = re.sub(r'\(.*?\)', '', clean)
    return clean[:45].rsplit(' ', 1)[0] + "..." if len(clean) > 45 else clean

def generate_tags(title, keyword):
    clean_t = re.sub(r'[^\w\s]', '', title.lower())
    words = clean_t.split()
    tags = [keyword.lower()]
    year = datetime.datetime.now().year
    for w in words:
        if w not in STOP_WORDS and w not in tags and len(w) > 2:
            tags.append(w)
    tags.append(f"{keyword.lower()} {year}")
    return tags[:15]

def generate_description(title, keyword, tags):
    year = datetime.datetime.now().year
    return f"""🔴 **{title}**\n\nIn this video, we explore **{keyword}**. Guide for {year}.\n\n👇 **Timestamps:**\n0:00 Intro\n0:30 {keyword.title()}\n5:00 Conclusion\n\n🔔 **SUBSCRIBE!**\n\n#Hashtags:\n#{keyword.replace(" ", "")} #Video"""

def generate_smart_suggestions(original_title, keyword, api_key=None):
    suggestions = []
    core = clean_title_text(original_title, keyword) or "Video"
    year = datetime.datetime.now().year
    emo = random.choice(VIRAL_EMOJIS)
    pwr = random.choice(POWER_WORDS_DB).upper()
    
    if api_key:
        try:
            yt = build('youtube', 'v3', developerKey=api_key)
            res = yt.search().list(q=keyword, type='video', part='snippet', maxResults=3).execute()
            if 'items' in res and res['items']:
                top_title = res['items'][0]['snippet']['title']
                words = top_title.split()
                for w in words:
                    if w.isupper() and len(w) > 3: 
                        pwr = w; break
        except: pass

    suggestions.append(f"{keyword.title()}: {core} ({pwr} {year}) {emo}")
    suggestions.append(f"{emo} {keyword.title()} {pwr}: {core} [{year}]")
    suggestions.append(f"{core} - {keyword.title()} {emo} ({pwr} {year})")
    return suggestions

def analyze_title(title, keyword=""):
    score = 0
    checks = []
    if 20 <= len(title) <= 85: score += 20; checks.append(("success", f"Length OK ({len(title)})"))
    else: checks.append(("warning", f"Length Issue ({len(title)})"))
    if keyword:
        if keyword.lower() in title.lower():
            score += 15
            clean_start = re.sub(r'^[^a-zA-Z0-9]+', '', title.lower()).strip()
            if clean_start.startswith(keyword.lower()): score += 15; checks.append(("success", "Keyword Front"))
            else: checks.append(("warning", "Keyword Present"))
        else: checks.append(("error", "Keyword Missing"))
    else: score += 30
    if any(pw in title.lower() for pw in POWER_WORDS_DB): score += 20; checks.append(("success", "Power Word Found"))
    else: checks.append(("warning", "No Power Word"))
    if re.search(r'\d+', title): score += 10; checks.append(("success", "Has Number"))
    else: checks.append(("info", "Add Number"))
    if re.search(r'[\[\(\]\)]', title): score += 10; checks.append(("success", "Has Brackets"))
    else: checks.append(("info", "Add Brackets"))
    if any(e in title for e in VIRAL_EMOJIS): score += 10; checks.append(("success", "Has Emoji"))
    else: checks.append(("info", "Add Emoji"))
    return min(score, 100), checks

def get_keyword_metrics(api_key, keyword):
    print(f"-> API Request: {keyword}")
    if not api_key: return None, "API Key Kosong"
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        search_res = youtube.search().list(q=keyword, type='video', part='id,snippet', maxResults=20, order='relevance').execute()
        video_ids = [item['id']['videoId'] for item in search_res['items']]
        if not video_ids: return None, "Tidak ada video."
        
        stats_res = youtube.videos().list(id=','.join(video_ids), part='statistics,snippet').execute()
        metrics = []
        for item in stats_res['items']:
            metrics.append({
                'Title': item['snippet']['title'],
                'Views': int(item['statistics'].get('viewCount', 0)),
                'Channel': item['snippet']['channelTitle'],
                'Date': item['snippet']['publishedAt'][:10]
            })
            
        if not metrics: return None, "Metrics Empty"
        df = pd.DataFrame(metrics)
        median_views = statistics.median([m['Views'] for m in metrics])
        score = min((median_views / 5000) * 10, 100)
        difficulty = "High" if median_views > 500000 else "Medium" if median_views > 50000 else "Low"
        print("✓ API Success")
        return {'median_views': median_views, 'score': int(score), 'difficulty': difficulty, 'top_videos': df}, None
    except Exception as e:
        print(f"x API Error: {e}")
        return None, str(e)

# --- 6. UI UTAMA ---
with st.sidebar:
    st.header("⚙️ Config")
    if "Online" in db_status: st.success(db_status)
    else: st.warning(db_status)
    st.divider()
    api_key = st.text_input("YouTube API Key", type="password")
    if api_key: st.success("🟢 Connected")

st.title("✅ YouTube Command Center V18")

tab1, tab2, tab3 = st.tabs(["🔍 Keyword Inspector", "📝 Video Optimizer", "📺 Channel Audit"])

# TAB 1: KEYWORD
with tab1:
    kw_input = st.text_input("Masukan Topik:", placeholder="Contoh: kucing lucu")
    if st.button("Analisa Market"):
        if not api_key: st.error("Perlu API Key")
        elif not kw_input: st.warning("Isi keyword")
        else:
            with st.spinner("Connecting..."):
                data, err = get_keyword_metrics(api_key, kw_input)
                if err: st.error(err)
                elif data:
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("Potensi", f"{data['score']}/100")
                    with c2: st.metric("Kesulitan", data['difficulty'])
                    with c3: st.metric("Median Views", f"{int(data['median_views']):,}")
                    
                    st.divider()
                    # FIX: Hapus use_container_width -> Pakai width="stretch" (Khusus Streamlit 2026)
                    st.bar_chart(data['top_videos'], x="Title", y="Views") 
                    st.dataframe(data['top_videos'][['Title', 'Channel', 'Views', 'Date']], width=None)

# TAB 2: OPTIMIZER
with tab2:
    c1, c2 = st.columns([1,2])
    with c1: target = st.text_input("Target Keyword", placeholder="Keyword utama...")
    with c2: draft = st.text_input("Draft Judul", placeholder="Judul video...")
    
    if st.button("Analisa Judul"):
        if target and draft:
            score, logs = analyze_title(draft, target)
            st.subheader(f"Score: {score}/100")
            clr = "green" if score>=80 else "orange" if score >= 60 else "red"
            st.markdown(f"<div style='background-color:#eee;height:10px'><div style='width:{score}%;background-color:{clr};height:10px'></div></div>", unsafe_allow_html=True)
            
            with st.expander("Detail", expanded=True):
                for s, m in logs: st.write(f"{'✅' if s=='success' else '⚠️'} {m}")
            
            if score < 100:
                st.info("Rekomendasi:")
                for s in generate_smart_suggestions(draft, target, api_key): st.code(s, language='text')
            
            st.divider()
            c_tag, c_desc = st.columns(2)
            tags = generate_tags(draft, target)
            with c_tag: st.text_area("Tags:", ", ".join(tags))
            with c_desc: st.text_area("Desc:", generate_description(draft, target, tags))

# TAB 3: AUDIT
with tab3:
    cid = st.text_input("Channel ID (UC...)", placeholder="UC_x5XG...")
    if st.button("Audit"):
        if not api_key or not cid.startswith("UC"): st.error("Cek API Key & Channel ID")
        else:
            print(f"-> Audit Channel: {cid}")
            with st.spinner("Audit..."):
                try:
                    yt = build('youtube', 'v3', developerKey=api_key)
                    ch = yt.channels().list(id=cid, part='contentDetails').execute()
                    if not ch['items']: st.error("Channel not found"); st.stop()
                    upid = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                    vids = yt.playlistItems().list(playlistId=upid, part='snippet', maxResults=10).execute()
                    
                    for item in vids['items']:
                        vt = item['snippet']['title']
                        img = item['snippet']['thumbnails']['default']['url']
                        sc, _ = analyze_title(vt, vt.split()[0] if vt else "Video")
                        
                        with st.container():
                            ca, cb, cc = st.columns([1,4,1])
                            # FIX: Ganti use_container_width=True menjadi width=150 (Manual Pixel)
                            # Ini lebih aman dan anti-error di versi masa depan
                            with ca: st.image(img, width=150) 
                            with cb:
                                st.write(f"**{vt}**")
                                if sc < 80:
                                    with st.expander("Saran"):
                                        for s in generate_smart_suggestions(vt, vt.split()[0], api_key): st.code(s, language='text')
                            with cc: st.markdown(f"**{sc}**")
                            st.divider()
                except Exception as e:
                    print(f"x Error Audit: {e}")
                    st.error(str(e))