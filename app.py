import streamlit as st

st.set_page_config(
    page_title="Brisbane Grocery Price Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global theme injection — Neon Cyberpunk Edition ───────────────────────────
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;600;700;800&family=Space+Mono:wght@400;700&display=swap');

/* ── Root variables ── */
:root {
    --neon:        #00EEFF;
    --neon-dim:    #00AACC;
    --neon-faint:  rgba(0,238,255,0.07);
    --woolworths:  #00C853;
    --coles:       #FF1744;
    --amber:       #FFD700;
    --bg:          #000000;
    --bg2:         #080c12;
    --bg3:         #050a0f;
    --card-border: rgba(0,238,255,0.28);
    --border:      #1a2a2a;
    --font-body:   'Exo 2', 'Segoe UI', sans-serif;
    --font-mono:   'Space Mono', monospace;
}

/* ── Full black background + animated grid ── */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stBottom"],
.main .block-container {
    background-color: var(--bg) !important;
    color: var(--neon) !important;
    font-family: var(--font-body) !important;
}

/* Cyberpunk grid overlay */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,238,255,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,238,255,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

/* Scanline effect */
[data-testid="stAppViewContainer"]::after {
    content: "";
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        rgba(0,255,255,0.015) 0px,
        rgba(0,255,255,0.015) 2px,
        transparent 2px,
        transparent 8px
    );
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar — dark glass panel ── */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: rgba(4, 8, 14, 0.95) !important;
    border-right: 1px solid var(--card-border) !important;
}
section[data-testid="stSidebar"] * {
    color: var(--neon) !important;
    font-family: var(--font-body) !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: var(--neon) !important;
    font-weight: 600;
    letter-spacing: 0.5px;
}
section[data-testid="stSidebar"] hr {
    border-color: var(--card-border) !important;
}

/* Sidebar title */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: var(--font-mono) !important;
    letter-spacing: 2px;
    text-shadow: 0 0 8px rgba(0,238,255,0.5);
}

/* Sidebar radio active item highlight */
section[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + div {
    color: #fff !important;
    text-shadow: 0 0 6px var(--neon);
}

/* ── Default text ── */
body, p, span, label, div, li, td, th,
.stMarkdown, .stMarkdown p,
.stText, [data-testid="stText"],
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"],
[data-testid="stCaptionContainer"],
[data-testid="stExpander"] summary,
[data-testid="stExpander"] p,
.stAlert p {
    color: var(--neon) !important;
    font-family: var(--font-body) !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6,
[data-testid="stHeadingWithActionElements"] * {
    color: var(--neon) !important;
    font-family: var(--font-body) !important;
    font-weight: 700;
    letter-spacing: 1px;
    text-shadow: 0 0 10px rgba(0,238,255,0.35);
}
h1 { font-size: 1.9rem !important; letter-spacing: 2px; }

/* ── Woolworths / Coles colour helpers ── */
.woolworths { color: var(--woolworths) !important; font-weight: 700; }
.coles      { color: var(--coles)      !important; font-weight: 700; }

/* ── Buttons — neon pill ── */
.stButton > button,
.stFormSubmitButton > button {
    background-color: transparent !important;
    color: var(--neon) !important;
    border: 1px solid var(--neon) !important;
    border-radius: 40px !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    box-shadow: 0 0 10px rgba(0,238,255,0.25) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background-color: rgba(0,238,255,0.12) !important;
    box-shadow: 0 0 20px rgba(0,238,255,0.55) !important;
    color: #fff !important;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: rgba(0,238,255,0.1) !important;
    border-color: var(--neon) !important;
    box-shadow: 0 0 16px rgba(0,238,255,0.4) !important;
}

/* ── Inputs ── */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] div {
    background-color: var(--bg2) !important;
    color: var(--neon) !important;
    border-color: var(--card-border) !important;
    border-radius: 12px !important;
    caret-color: var(--neon) !important;
    font-family: var(--font-body) !important;
}
[data-baseweb="select"] [data-testid="stSelectboxContainer"] {
    background-color: var(--bg2) !important;
    border-radius: 12px !important;
}
[data-baseweb="input"] {
    border-radius: 12px !important;
    border-color: var(--card-border) !important;
}

/* ── Dropdowns ── */
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"],
[data-baseweb="select"] ul {
    background-color: var(--bg2) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
}
[role="option"], [data-baseweb="menu"] li {
    color: var(--neon) !important;
    background-color: var(--bg2) !important;
}
[role="option"]:hover, [data-baseweb="menu"] li:hover {
    background-color: rgba(0,238,255,0.1) !important;
}

/* ── Multiselect tags ── */
[data-baseweb="tag"] {
    background-color: rgba(0,238,255,0.12) !important;
    border: 1px solid var(--neon-dim) !important;
    border-radius: 20px !important;
}
[data-baseweb="tag"] span { color: var(--neon) !important; }

/* ── Metrics — card style ── */
[data-testid="stMetric"] {
    background: rgba(8,12,18,0.75) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 20px !important;
    padding: 18px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 12px rgba(0,238,255,0.1) !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    backdrop-filter: blur(10px);
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 40px rgba(0,238,255,0.15) !important;
    border-color: var(--neon) !important;
}
[data-testid="stMetricValue"] {
    color: var(--neon) !important;
    font-family: var(--font-mono) !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    text-shadow: 0 0 8px rgba(0,238,255,0.6) !important;
}
[data-testid="stMetricLabel"] {
    color: #9cf !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
    font-weight: 600 !important;
}
[data-testid="stMetricDelta"] {
    font-family: var(--font-mono) !important;
}

/* ── Dataframe wrapper ── */
[data-testid="stDataFrame"] {
    background-color: var(--bg2) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--neon-dim), var(--neon)) !important;
    box-shadow: 0 0 10px rgba(0,238,255,0.7) !important;
    border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div {
    background-color: var(--bg3) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 4px !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    background: rgba(8,12,18,0.8) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(6px);
}
[data-testid="stAlert"][kind="info"]    { border-left: 3px solid var(--neon) !important; }
[data-testid="stAlert"][kind="success"] { border-left: 3px solid var(--woolworths) !important; }
[data-testid="stAlert"][kind="warning"] { border-left: 3px solid var(--amber) !important; }
[data-testid="stAlert"][kind="error"]   { border-left: 3px solid var(--coles) !important; }

/* ── Expander — glass card ── */
[data-testid="stExpander"] {
    background: rgba(8,12,18,0.75) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(8px) !important;
}
[data-testid="stExpander"] summary {
    border-radius: 16px !important;
}
[data-testid="stExpander"] summary:hover {
    background-color: rgba(0,238,255,0.05) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    color: var(--neon-dim) !important;
    border-bottom: 2px solid transparent !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--neon) !important;
    border-bottom: 2px solid var(--neon) !important;
    text-shadow: 0 0 6px rgba(0,238,255,0.5);
}

/* ── Select slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: var(--neon) !important;
    box-shadow: 0 0 8px var(--neon) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid] {
    background: var(--neon) !important;
}

/* ── Checkboxes ── */
[data-testid="stCheckbox"] label { color: var(--neon) !important; }

/* ── Number input ── */
[data-testid="stNumberInput"] input { color: var(--neon) !important; }
[data-testid="stNumberInput"] button {
    color: var(--neon) !important;
    border-color: var(--card-border) !important;
    border-radius: 8px !important;
}

/* ── Code blocks ── */
code, pre {
    background-color: var(--bg3) !important;
    color: var(--neon) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] * { color: var(--neon) !important; }

/* ── Toolbar ── */
[data-testid="stToolbar"] { background-color: var(--bg) !important; }

/* ── Form ── */
[data-testid="stForm"] {
    background: rgba(8,12,18,0.75) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 20px !important;
    padding: 20px !important;
    backdrop-filter: blur(10px);
}

/* ── Dividers ── */
hr { border-color: var(--card-border) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb {
    background: var(--neon-dim);
    border-radius: 3px;
}

/* ── Plotly chart backgrounds ── */
.js-plotly-plot .plotly .bg { fill: transparent !important; }

/* ── Radio ── */
[data-testid="stRadio"] label { color: var(--neon) !important; }
[data-testid="stRadio"] [role="radio"] span { border-color: var(--neon) !important; }

/* ── Stale captions dimmer ── */
[data-testid="stCaptionContainer"] {
    color: #9cf !important;
    font-size: 0.82rem !important;
}

/* ── Column containers — subtle glass cards ── */
[data-testid="stHorizontalBlock"] > div {
    background: rgba(8,12,18,0.5);
    border-radius: 16px;
    border: 1px solid rgba(0,238,255,0.08);
    padding: 2px;
}

/* ── Woolies/Coles badge helpers ── */
.woolies-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 40px;
    font-weight: 700;
    font-size: 0.78rem;
    background: rgba(0,200,83,0.15);
    color: #00E676 !important;
    border: 1px solid var(--woolworths);
    letter-spacing: 0.5px;
}
.coles-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 40px;
    font-weight: 700;
    font-size: 0.78rem;
    background: rgba(255,23,68,0.15);
    color: #FF5252 !important;
    border: 1px solid var(--coles);
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)


# ── Woolworths / Coles helper for markdown ───────────────────────────────────
def ww(text: str) -> str:
    """Wrap text in Woolworths green span."""
    return f'<span style="color:#00C853;font-weight:600">{text}</span>'

def coles(text: str) -> str:
    """Wrap text in Coles red span."""
    return f'<span style="color:#FF1744;font-weight:600">{text}</span>'


from db import get_db
from pages_app import dashboard, price_history, suburb_compare, store_rankings, auto_scrape

# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.markdown(
    '<div style="font-family:\'Space Mono\',monospace;font-size:1.05rem;font-weight:700;'
    'letter-spacing:2px;color:#00EEFF;text-shadow:0 0 8px rgba(0,238,255,0.5);">'
    '◢ BRISBANE PRICE TRACKER ◣</div>',
    unsafe_allow_html=True,
)
st.sidebar.caption("🟢 Woolworths · 🔴 Coles · Live scraped prices")

pages = {
    "🏠 Dashboard":        dashboard.show,
    "🤖 Auto-Scrape":      auto_scrape.show,
    "📈 Price History":    price_history.show,
    "🗺️ Suburb Compare":  suburb_compare.show,
    "📊 Store Rankings":   store_rankings.show,
}

selection = st.sidebar.radio("Navigate", list(pages.keys()), label_visibility="collapsed")



# ── Render selected page ──────────────────────────────────────────────────────
db = get_db()
pages[selection](db)

# ── Brand-colour + dataframe theme injector ──────────────────────────────────
# st.iframe() runs JS inside an iframe — window.parent.document
# IS accessible on Streamlit Cloud (same origin), so this works correctly.
st.iframe("""
<script>
(function () {
  const WW    = '#00C853';
  const COLES = '#FF1744';
  const RE    = /(Woolworths|Coles)/g;

  function colorize(node) {
    if (!node) return;
    if (node.nodeType === 3) {
      var txt = node.nodeValue;
      if (!txt) return;
      RE.lastIndex = 0;
      if (!RE.test(txt)) { RE.lastIndex = 0; return; }
      RE.lastIndex = 0;
      var frag = document.createDocumentFragment();
      var last = 0, m;
      while ((m = RE.exec(txt)) !== null) {
        if (m.index > last)
          frag.appendChild(document.createTextNode(txt.slice(last, m.index)));
        var s = document.createElement('span');
        s.textContent = m[1];
        s.setAttribute('style', 'color:' + (m[1]==='Woolworths' ? WW : COLES) + ' !important;font-weight:700;');
        s.setAttribute('data-branded', '1');
        frag.appendChild(s);
        last = RE.lastIndex;
      }
      RE.lastIndex = 0;
      if (last < txt.length)
        frag.appendChild(document.createTextNode(txt.slice(last)));
      if (node.parentNode) node.parentNode.replaceChild(frag, node);

    } else if (node.nodeType === 1) {
      var tag = node.tagName;
      if (tag==='SCRIPT'||tag==='STYLE'||tag==='TEXTAREA'||tag==='INPUT') return;
      if (node.getAttribute('data-branded')) return;
      // Must copy to array — childNodes is live and mutates during iteration
      var children = Array.prototype.slice.call(node.childNodes);
      children.forEach(colorize);
    }
  }

  // Inject CSS into every st.dataframe iframe so text is visible on black bg
  function styleDataframes() {
    try {
      var frames = window.parent.document.querySelectorAll(
        '[data-testid="stDataFrame"] iframe, [data-testid="stDataFrameResizable"] iframe'
      );
      frames.forEach(function(iframe) {
        try {
          var idoc = iframe.contentDocument || iframe.contentWindow.document;
          if (!idoc || idoc.getElementById('_df_theme')) return;
          var style = idoc.createElement('style');
          style.id = '_df_theme';
          style.textContent = [
            'body, .dvn-scroller { background:#080c12 !important; }',
            '.cell-wrap-text, .ag-cell, .ag-header-cell-text,',
            '.ag-row, .ag-cell-value, span, div { color:#00EEFF !important; }',
            '.ag-header { background:#030810 !important; border-bottom:1px solid rgba(0,238,255,0.3) !important; }',
            '.ag-header-cell-text { font-weight:700 !important; letter-spacing:1px !important; }',
            '.ag-row-odd  { background:#080c12 !important; }',
            '.ag-row-even { background:#060a10 !important; }',
            '.ag-row:hover { background:rgba(0,238,255,0.07) !important; }',
            '.ag-cell { border-color:rgba(0,238,255,0.05) !important; }',
            '::-webkit-scrollbar { width:4px; height:4px; }',
            '::-webkit-scrollbar-track { background:#000; }',
            '::-webkit-scrollbar-thumb { background:#00AACC; border-radius:3px; box-shadow:0 0 4px #00AACC; }',
          ].join('\n');
          idoc.head.appendChild(style);
        } catch(e2) {}
      });
    } catch(e) {}
  }

  function run() {
    try {
      var doc = window.parent.document;
      colorize(doc.body);
      styleDataframes();
    } catch(e) {
      // Same-origin access failed — no-op
    }
  }

  // Multiple passes: Streamlit renders asynchronously
  setTimeout(run, 500);
  setTimeout(run, 1200);
  setTimeout(run, 2500);

  // MutationObserver on parent DOM for re-renders / page navigation
  try {
    var parentDoc = window.parent.document;
    var target = parentDoc.body;
    new MutationObserver(function(muts) {
      muts.forEach(function(m) {
        m.addedNodes.forEach(colorize);
      });
      styleDataframes();
    }).observe(target, { childList: true, subtree: true });
  } catch(e) {}
})();
</script>
""", height=1)
