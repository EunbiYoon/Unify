import os, json, re
import numpy as np
import streamlit as st
import tensorflow as tf
from PIL import Image

try:
    import pandas as pd
except Exception:
    pd = None

# ✅ Auto-refresh for autoplay
from streamlit_autorefresh import st_autorefresh

# -----------------------
# Config
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "sample")          # sample/NG, sample/OK
ART_DIR  = os.path.join(BASE_DIR, "artifacts")
MODEL_PATH   = os.path.join(ART_DIR, "model.keras")
CLASSES_PATH = os.path.join(ART_DIR, "class_names.json")

IMG_SIZE = (200, 200)
THRESHOLD = 0.5

st.set_page_config(page_title="OK/NG Inspector", layout="wide")

# -----------------------
# CSS (styling + alignment)
# -----------------------
st.markdown(
    """
    <style>
      /* ✅ Make sidebar and main start at the same vertical baseline */
      section[data-testid="stSidebar"] .block-container { padding-top: 16px !important; }
      .main .block-container { padding-top: 16px !important; }

      /* ✅ Remove default top margins from headings that can shift alignment */
      section[data-testid="stSidebar"] h1,
      section[data-testid="stSidebar"] h2,
      section[data-testid="stSidebar"] h3,
      .main h1, .main h2, .main h3 {
        margin-top: 0px !important;
      }

      /* Right panel: keep it from exceeding left image area; scroll inside */
      .result-panel {
        max-height: 78vh;
        overflow-y: auto;
        padding-right: 6px;
        padding-top:0px
      }

      /* Header row */
      .header-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0 0 10px 0;
        padding: 0;
      }
      .header-title {
        font-size: 32px;
        font-weight: 850;
        margin: 0;
        line-height: 1.1;
      }

      /* Big label block */
      .big-badge {
        width: 100%;
        border-radius: 18px;
        color: white;
        font-size: 40px;
        font-weight: 900;
        text-align: center;
        padding: 18px 22px;
        margin-top: 0px;
      }

      /* Section titles inside the panel */
      .section-title {
        font-size: 26px;
        font-weight: 850;
        margin: 18px 0 8px 0;
      }

      /* Sidebar hint text */
      .sidebar-hint {
        font-size: 13px;
        opacity: 0.75;
        margin: 6px 0 14px 0;
        line-height: 1.35;
      }

      /* Make Streamlit buttons feel more clickable (hover) */
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        border-radius: 14px !important;
        transition: transform 0.08s ease, background 0.12s ease, border 0.12s ease;
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px);
      }
      .st-emotion-cache-zy6yx3{
        padding-top:20px;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------
# Load model & classes
# -----------------------
@st.cache_resource
def load_artifacts():
    model = tf.keras.models.load_model(MODEL_PATH)
    with open(CLASSES_PATH, "r", encoding="utf-8") as f:
        class_names = json.load(f)  # e.g., ["NG","OK"]
    return model, class_names

def parse_figure_num(filename: str) -> int:
    # ✅ safe: handles Figure_1.png, Figure-1.png, Figure 1.png
    m = re.search(r"figure[_ -]*(\d+)", filename, re.IGNORECASE)
    return int(m.group(1)) if m else -1

def list_dataset_images(root_dir):
    exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    items = []

    for label in os.listdir(root_dir):
        label_dir = os.path.join(root_dir, label)
        if not os.path.isdir(label_dir):
            continue

        for fname in os.listdir(label_dir):
            if fname.lower().endswith(exts):
                items.append({
                    "true_label": label,  # internal only
                    "path": os.path.join(label_dir, fname),
                    "filename": fname,
                    "fig_num": parse_figure_num(fname),
                })

    # Figure number DESC: 8,7,6,...,1
    items.sort(key=lambda x: (x["fig_num"], x["filename"].lower()), reverse=True)

    for i, it in enumerate(items):
        it["id"] = i
        it["ui_name"] = it["filename"]   # UI shows only filename, no OK/NG
    return items

def predict_one(model, pil_img):
    img = pil_img.convert("RGB").resize(IMG_SIZE)
    x = np.array(img, dtype=np.float32) / 255.0
    x = np.expand_dims(x, axis=0)
    prob = float(model.predict(x, verbose=0)[0][0])  # sigmoid
    pred_idx = 1 if prob >= THRESHOLD else 0
    return prob, pred_idx

@st.cache_data(show_spinner=True)
def evaluate_dataset(items, model, class_names):
    y_true = []
    y_pred = []
    for it in items:
        img = Image.open(it["path"]).convert("RGB")
        _, pred_idx = predict_one(model, img)
        pred_label = class_names[pred_idx] if pred_idx < len(class_names) else str(pred_idx)
        y_true.append(it["true_label"])
        y_pred.append(pred_label)
    return y_true, y_pred

def confusion_matrix_binary(y_true, y_pred, labels=("NG", "OK")):
    l0, l1 = labels
    tn = fp = fn = tp = 0
    for t, p in zip(y_true, y_pred):
        if t == l0 and p == l0:
            tn += 1
        elif t == l0 and p == l1:
            fp += 1
        elif t == l1 and p == l0:
            fn += 1
        elif t == l1 and p == l1:
            tp += 1
    return np.array([[tn, fp], [fn, tp]], dtype=int)

def accuracy(y_true, y_pred):
    if not y_true:
        return 0.0
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)

# -----------------------
# Guard
# -----------------------
if not (os.path.exists(MODEL_PATH) and os.path.exists(CLASSES_PATH)):
    st.error("Run train.py first to create artifacts/model.keras and artifacts/class_names.json.")
    st.stop()

model, class_names = load_artifacts()
items = list_dataset_images(DATA_DIR)

if not items:
    st.error("No images found under sample/OK and sample/NG.")
    st.stop()

# -----------------------
# Sidebar: dataset list (filename only, Figure DESC)
# -----------------------
st.sidebar.markdown(
    "<div class='header-row'><p class='header-title'>Dataset Images</p></div>",
    unsafe_allow_html=True
)

st.sidebar.markdown(
    "<div class='sidebar-hint'>Click an image to inspect it. Recent selections are saved in your browsing history.</div>",
    unsafe_allow_html=True
)

# ✅ selection init
if "selected_id" not in st.session_state:
    st.session_state.selected_id = items[0]["id"]

# ✅ autoplay (3초마다 자동 변경)
autoplay = st.sidebar.toggle("Auto-play", value=True)
if autoplay:
    tick = st_autorefresh(interval=2000, key="autoplay_tick")  # 3초마다 rerun
    if "last_tick" not in st.session_state:
        st.session_state.last_tick = tick
    if tick != st.session_state.last_tick:
        st.session_state.last_tick = tick
        st.session_state.selected_id = (st.session_state.selected_id + 1) % len(items)
else:
    # autoplay 껐을 때 tick 상태 초기화(다시 켰을 때 1칸 점프 방지)
    if "last_tick" in st.session_state:
        del st.session_state["last_tick"]

# ✅ sidebar list
for it in items:
    colA, colB = st.sidebar.columns([1, 3], vertical_alignment="center")

    with colA:
        try:
            thumb = Image.open(it["path"]).convert("RGB")
            colA.image(thumb, use_container_width=True)
        except Exception:
            pass

    with colB:
        if st.button(it["ui_name"], key=f"img_{it['id']}", help="Click to view this image."):
            st.session_state.selected_id = it["id"]

# -----------------------
# Main layout
# -----------------------
selected_item = items[st.session_state.selected_id]
selected_path = selected_item["path"]
true_label = selected_item["true_label"]  # internal only

left, right = st.columns([2, 1], vertical_alignment="top")

with left:
    st.markdown(
        "<div class='header-row'><p class='header-title' style='font-size:28px'>Processed Image</p></div>",
        unsafe_allow_html=True
    )
    img = Image.open(selected_path).convert("RGB")
    st.image(img, use_container_width=True)

with right:
    prob, pred_idx = predict_one(model, img)
    pred_label = class_names[pred_idx] if pred_idx < len(class_names) else str(pred_idx)
    pred_upper = str(pred_label).upper()

    badge_color = "#16a34a" if pred_upper == "OK" else "#dc2626"

    st.markdown(
        "<div class='header-row'><p class='header-title' style='font-size:28px'>Result</p></div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='result-panel'>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='big-badge' style='background:{badge_color};; margin-top:-1rem'>{pred_upper}</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='section-title'>Details</div>", unsafe_allow_html=True)
    st.write(f"**Sigmoid probability:** {prob:.4f}")
    st.write(f"**Threshold:** {THRESHOLD}")

    correct = (true_label == pred_label)
    st.write("**Match:**", "✅ Correct" if correct else "❌ Wrong")

    st.markdown("<div class='section-title'>Confusion Matrix</div>", unsafe_allow_html=True)

    y_true, y_pred = evaluate_dataset(items, model, class_names)
    labels = ("NG", "OK")
    cm = confusion_matrix_binary(y_true, y_pred, labels=labels)
    acc = accuracy(y_true, y_pred)

    tn, fp = cm[0, 0], cm[0, 1]
    fn, tp = cm[1, 0], cm[1, 1]

    if pd is not None:
        cm_df = pd.DataFrame(
            cm,
            index=[f"True {labels[0]}", f"True {labels[1]}"],
            columns=[f"Pred {labels[0]}", f"Pred {labels[1]}"],
        )
        st.dataframe(cm_df, use_container_width=True)
    else:
        st.table({
            f"Pred {labels[0]}": [int(tn), int(fn)],
            f"Pred {labels[1]}": [int(fp), int(tp)],
        })

    st.write(f"**Accuracy:** {acc*100:.2f}% ({int(acc*len(y_true))}/{len(y_true)})")
    st.warning(f"**NG → OK (False Positive): {fp}** (Defect predicted as OK)")

    st.markdown("</div>", unsafe_allow_html=True)
