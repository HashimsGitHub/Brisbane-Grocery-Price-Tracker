import streamlit as st

st.set_page_config(
    page_title="Aussie Price Tracker",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global theme injection ────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Imports ── */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');

/* ── Root variables ── */
:root {
    --neon-blue:   #00EEFF;
    --neon-blue-dim: #00AACC;
    --woolworths:  #00C853;   /* Woolworths green */
    --coles:       #FF1744;   /* Coles red */
    --bg:          #000000;
    --bg2:         #0a0a0a;
    --bg3:         #0f1117;
    --border:      #1a2a2a;
}

/* ── Full black background everywhere ── */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stBottom"],
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
.main .block-container {
    background-color: var(--bg) !important;
    color: var(--neon-blue) !important;
}

/* ── Default text: neon blue ── */
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
    color: var(--neon-blue) !important;
}

/* ── Headings: neon blue, slightly brighter ── */
h1, h2, h3, h4, h5, h6,
[data-testid="stHeadingWithActionElements"] * {
    color: var(--neon-blue) !important;
    text-shadow: 0 0 8px rgba(0,238,255,0.4);
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] * {
    color: var(--neon-blue) !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: var(--neon-blue) !important;
}
section[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
}

/* ── Woolworths / Coles inline markdown styling helpers ── */
.woolworths { color: var(--woolworths) !important; font-weight: 600; }
.coles      { color: var(--coles)      !important; font-weight: 600; }

/* ── Buttons ── */
.stButton > button,
.stFormSubmitButton > button {
    background-color: transparent !important;
    color: var(--neon-blue) !important;
    border: 1px solid var(--neon-blue) !important;
    box-shadow: 0 0 8px rgba(0,238,255,0.3) !important;
    transition: all 0.2s;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background-color: rgba(0,238,255,0.1) !important;
    box-shadow: 0 0 16px rgba(0,238,255,0.6) !important;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    border-color: var(--neon-blue) !important;
    box-shadow: 0 0 12px rgba(0,238,255,0.5) !important;
}

/* ── Inputs, selects, textareas ── */
input, textarea, select,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] div {
    background-color: var(--bg2) !important;
    color: var(--neon-blue) !important;
    border-color: var(--border) !important;
    caret-color: var(--neon-blue) !important;
}
[data-baseweb="select"] [data-testid="stSelectboxContainer"] {
    background-color: var(--bg2) !important;
}

/* ── Dropdown menus ── */
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"],
[data-baseweb="select"] ul {
    background-color: var(--bg2) !important;
    border: 1px solid var(--border) !important;
}
[role="option"], [data-baseweb="menu"] li {
    color: var(--neon-blue) !important;
    background-color: var(--bg2) !important;
}
[role="option"]:hover, [data-baseweb="menu"] li:hover {
    background-color: rgba(0,238,255,0.1) !important;
}

/* ── Multiselect tags ── */
[data-baseweb="tag"] {
    background-color: rgba(0,238,255,0.15) !important;
    border: 1px solid var(--neon-blue-dim) !important;
}
[data-baseweb="tag"] span { color: var(--neon-blue) !important; }

/* ── Dataframe outer shell (iframe border/bg) ── */
[data-testid="stDataFrame"] {
    background-color: var(--bg2) !important;
}
/* Note: cell text inside the iframe is styled via JS injection below */

/* ── Metrics ── */
[data-testid="stMetric"] {
    background-color: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px;
    padding: 12px !important;
}
[data-testid="stMetricValue"] {
    color: var(--neon-blue) !important;
    text-shadow: 0 0 10px rgba(0,238,255,0.5);
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
    background-color: var(--neon-blue) !important;
    box-shadow: 0 0 8px rgba(0,238,255,0.6);
}
[data-testid="stProgressBar"] > div {
    background-color: var(--bg2) !important;
}

/* ── Alerts / info / warning / success / error ── */
[data-testid="stAlert"] {
    background-color: var(--bg2) !important;
    border-radius: 6px;
}
[data-testid="stAlert"][kind="info"]    { border-left: 3px solid var(--neon-blue) !important; }
[data-testid="stAlert"][kind="success"] { border-left: 3px solid var(--woolworths) !important; }
[data-testid="stAlert"][kind="warning"] { border-left: 3px solid #FFD700 !important; }
[data-testid="stAlert"][kind="error"]   { border-left: 3px solid var(--coles) !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}
[data-testid="stExpander"] summary:hover {
    background-color: rgba(0,238,255,0.05) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    color: var(--neon-blue-dim) !important;
    border-bottom: 2px solid transparent;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--neon-blue) !important;
    border-bottom: 2px solid var(--neon-blue) !important;
}

/* ── Dividers / hr ── */
hr { border-color: var(--border) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--neon-blue-dim); border-radius: 3px; }

/* ── Plotly chart backgrounds ── */
.js-plotly-plot .plotly .bg { fill: transparent !important; }

/* ── Radio buttons ── */
[data-testid="stRadio"] label { color: var(--neon-blue) !important; }
[data-testid="stRadio"] [role="radio"] span { border-color: var(--neon-blue) !important; }

/* ── Checkboxes ── */
[data-testid="stCheckbox"] label { color: var(--neon-blue) !important; }

/* ── Number input ── */
[data-testid="stNumberInput"] input { color: var(--neon-blue) !important; }
[data-testid="stNumberInput"] button { color: var(--neon-blue) !important; border-color: var(--border) !important; }

/* ── Code blocks ── */
code, pre {
    background-color: var(--bg2) !important;
    color: var(--neon-blue) !important;
    border: 1px solid var(--border) !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] * { color: var(--neon-blue) !important; }

/* ── Top navigation / toolbar ── */
[data-testid="stToolbar"] { background-color: var(--bg) !important; }

/* ── Form border ── */
[data-testid="stForm"] {
    border: 1px solid var(--border) !important;
    background-color: var(--bg2) !important;
    border-radius: 8px;
    padding: 16px;
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
from pages_app import dashboard, submit_price, price_history, suburb_compare, price_alerts, store_rankings, auto_scrape

# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.title("🛒 Aussie Price Tracker")
st.sidebar.caption("Crowdsourced grocery & fuel prices")

pages = {
    "🏠 Dashboard":        dashboard.show,
    "📝 Submit a Price":   submit_price.show,
    "🤖 Auto-Scrape":      auto_scrape.show,
    "📈 Price History":    price_history.show,
    "🗺️ Suburb Compare":  suburb_compare.show,
    "🚨 Price Alerts":     price_alerts.show,
    "📊 Store Rankings":   store_rankings.show,
}

selection = st.sidebar.radio("Navigate", list(pages.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Data contributed by the community.<br>"
    "Prices are retained for 5 years.<br><br>"
    f'<span style="color:#00C853;font-weight:600">■ Woolworths</span> &nbsp; '
    f'<span style="color:#FF1744;font-weight:600">■ Coles</span> &nbsp; '
    f'<span style="color:#00EEFF">■ Other</span>',
    unsafe_allow_html=True,
)

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
            'body, .dvn-scroller { background:#0a0a0a !important; }',
            '.cell-wrap-text, .ag-cell, .ag-header-cell-text,',
            '.ag-row, .ag-cell-value, span, div { color:#00EEFF !important; }',
            '.ag-header { background:#061010 !important; }',
            '.ag-row-odd { background:#0d0d0d !important; }',
            '.ag-row-even { background:#0a0a0a !important; }',
            '.ag-row:hover { background:rgba(0,238,255,0.06) !important; }',
            '.ag-header-cell { border-bottom:1px solid #1a2a2a !important; }',
            '::-webkit-scrollbar { width:5px; height:5px; }',
            '::-webkit-scrollbar-track { background:#000; }',
            '::-webkit-scrollbar-thumb { background:#00AACC; border-radius:3px; }',
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
