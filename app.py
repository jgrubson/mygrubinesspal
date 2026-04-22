from datetime import date, timedelta, datetime, time
from statistics import mean
from zoneinfo import ZoneInfo
import calendar
import json

import pandas as pd
import streamlit as st
from openai import OpenAI
from supabase import create_client

# ==================================================
# CONFIG / CLIENTS
# ==================================================
APP_TZ = ZoneInfo("America/Sao_Paulo")


def local_today() -> date:
    return datetime.now(APP_TZ).date()


@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_resource
def get_openai():
    key = st.secrets.get("OPENAI_API_KEY")
    return OpenAI(api_key=key) if key else None


st.set_page_config(
    page_title="MyGrubinessPal",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {max-width: 760px; padding-top: 0.6rem; padding-bottom: 6rem;}
    :root {
        --bg: #0b1020;
        --panel: #12192b;
        --panel-2: #182238;
        --line: #26314b;
        --muted: #9fb0c9;
        --text: #eef3ff;
        --green: #69d3a6;
        --yellow: #ffd166;
        --red: #ff8a8a;
        --blue: #84b6ff;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(190deg, #09101d 0%, #0d1220 100%);
        color: var(--text);
    }
    .top-date {
        background: rgba(18,25,43,0.92);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 12px 14px;
        margin-bottom: 14px;
        text-align: center;
        box-shadow: 0 10px 28px rgba(0,0,0,0.18);
    }
    .top-date .main {font-size: 17px; font-weight: 800; color: var(--text);}
    .top-date .sub {font-size: 12px; color: var(--muted); margin-top: 4px;}
    .section-title {
        margin: 18px 0 8px;
        color: var(--green);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 800;
    }
    .card {
        background: rgba(18,25,43,0.96);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    }
    .card-tight {padding: 12px 14px;}
    .big {font-size: 31px; line-height: 1; font-weight: 800; color: var(--text);}
    .muted {font-size: 13px; color: var(--muted); margin-top: 6px;}
    .kpi-row {display:grid; grid-template-columns: repeat(4,1fr); gap:8px; margin-top: 10px;}
    .kpi {
        background: rgba(24,34,56,0.96);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 10px 8px;
        text-align: center;
    }
    .kpi .l {font-size: 10px; text-transform: uppercase; letter-spacing: 0.9px; color: var(--muted);}
    .kpi .v {font-size: 20px; font-weight: 800; color: var(--text); margin-top: 2px;}
    .status {
        display:inline-block; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 800; margin-top: 8px;
    }
    .g {background: rgba(66,160,111,0.14); color: var(--green); border:1px solid rgba(105,211,166,0.24)}
    .y {background: rgba(255,209,102,0.14); color: var(--yellow); border:1px solid rgba(255,209,102,0.22)}
    .r {background: rgba(255,138,138,0.14); color: var(--red); border:1px solid rgba(255,138,138,0.22)}
    .b {background: rgba(132,182,255,0.14); color: var(--blue); border:1px solid rgba(132,182,255,0.22)}
    .meal-card {
        background: rgba(24,34,56,0.96);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    .meal-name {font-size: 14px; font-weight: 800; color: var(--text);}
    .meal-detail {font-size: 12px; color: var(--muted); margin-top: 4px;}
    .check-card {
        background: rgba(24,34,56,0.96);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }
    .analysis-box {
        background: linear-gradient(135deg, rgba(17,58,47,0.96), rgba(18,25,43,0.98));
        border: 1px solid #2b5a4e;
        color: #dbf9ea;
        border-radius: 18px;
        padding: 16px 18px;
        margin-top: 8px;
        box-shadow: 0 14px 30px rgba(0,0,0,0.18);
    }
    .analysis-box .t {font-size: 11px; text-transform: uppercase; letter-spacing: 1.1px; color: var(--green); font-weight: 800; margin-bottom: 8px;}
    .analysis-box ul {margin: 0; padding-left: 18px;}
    .analysis-box li {margin-bottom: 6px;}
    .calendar-note {font-size:12px; color:var(--muted); margin-top:10px;}
    .small-label {font-size:12px; color:var(--muted); margin-bottom:6px;}
    .streamlit-expanderHeader {font-size: 15px; font-weight: 700;}
    .stButton > button {min-height: 42px; border-radius: 12px;}
    .stNumberInput input, .stTextInput input {font-size: 16px !important;}

    .hero-grid {display:grid; grid-template-columns: 1.35fr 1fr; gap:12px; margin-bottom: 12px;}
    .hero-card {
        background: linear-gradient(135deg, rgba(20,32,53,0.98), rgba(16,23,38,0.98));
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 16px;
        box-shadow: 0 18px 40px rgba(0,0,0,0.22);
    }
    .hero-kicker {font-size: 11px; text-transform: uppercase; letter-spacing: 1.1px; color: var(--green); font-weight: 800; margin-bottom: 8px;}
    .hero-main {font-size: 34px; line-height: 1; font-weight: 900; color: var(--text);}
    .hero-sub {font-size: 13px; color: var(--muted); margin-top: 8px;}
    .summary-chip-row {display:flex; gap:8px; flex-wrap:wrap; margin-top: 12px;}
    .summary-chip {
        background: rgba(132,182,255,0.10);
        border: 1px solid rgba(132,182,255,0.18);
        border-radius: 999px;
        padding: 7px 10px;
        font-size: 12px;
        color: var(--text);
    }
    .stack-card {
        background: rgba(18,25,43,0.96);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.16);
    }
    .stack-title {font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); font-weight: 800;}
    .stack-value {font-size: 26px; font-weight: 900; color: var(--text); margin-top: 8px;}
    .stack-sub {font-size: 13px; color: var(--muted); margin-top: 6px; line-height: 1.5;}
    .period-grid {display:grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 10px;}
    .period-card {
        background: rgba(18,25,43,0.96);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 14px;
        min-height: 150px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.16);
    }
    .period-card .top {font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--green); font-weight: 800;}
    .period-card .big {font-size: 28px; margin-top: 8px;}
    .period-card .small {font-size: 12px; color: var(--muted); margin-top: 6px; line-height: 1.5;}
    .legend-wrap {display:flex; gap:10px; flex-wrap:wrap; margin: 8px 0 2px;}
    .legend-badge {display:inline-flex; align-items:center; gap:8px; border:1px solid var(--line); background: rgba(24,34,56,0.96); border-radius:999px; padding:7px 10px; font-size:12px; color: var(--text);}
    .nav-caption {font-size:12px; color: var(--muted); margin-top: 4px;}


    .strategy-grid {display:grid; grid-template-columns: 1.15fr 1fr; gap:12px; margin-bottom: 12px;}
    .strategy-card {
        background: linear-gradient(135deg, rgba(16,29,49,0.98), rgba(15,20,32,0.98));
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 16px;
        box-shadow: 0 16px 34px rgba(0,0,0,0.18);
        margin-bottom: 12px;
    }
    .strategy-kicker {font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--yellow); font-weight: 800; margin-bottom: 8px;}
    .strategy-title {font-size: 24px; font-weight: 900; line-height: 1.1; color: var(--text);}
    .strategy-copy {font-size: 13px; color: var(--muted); line-height: 1.6; margin-top: 10px;}
    .target-grid {display:grid; grid-template-columns: repeat(2,1fr); gap: 10px; margin-top: 12px;}
    .target-card {background: rgba(24,34,56,0.96); border: 1px solid var(--line); border-radius: 16px; padding: 12px;}
    .target-label {font-size: 11px; text-transform: uppercase; letter-spacing: 0.9px; color: var(--muted);}
    .target-value {font-size: 22px; font-weight: 900; margin-top: 4px; color: var(--text);}
    .target-sub {font-size: 12px; color: var(--muted); margin-top: 4px; line-height: 1.5;}
    .hydration-wrap {display:grid; grid-template-columns: 1.1fr 1fr; gap:12px; margin-bottom: 12px;}
    .progress-bar {width:100%; height: 12px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow:hidden; margin-top: 10px;}
    .progress-fill {height: 100%; background: linear-gradient(90deg, #5ac8fa, #69d3a6); border-radius: 999px;}
    .tag-row {display:flex; gap:8px; flex-wrap:wrap; margin-top: 12px;}
    .tag {display:inline-flex; align-items:center; border-radius:999px; border:1px solid var(--line); background: rgba(255,255,255,0.04); padding: 7px 10px; font-size:12px; color: var(--text);}
    .food-search-box {background: rgba(24,34,56,0.65); border: 1px dashed var(--line); border-radius: 14px; padding: 12px; margin-top: 10px;}
    .soft-note {font-size: 12px; color: var(--muted); line-height: 1.55;}
    .custom-estimate {background: rgba(13,42,38,0.85); border:1px solid #2f6f5d; border-radius: 14px; padding: 12px; margin-top: 10px;}

</style>
""",
    unsafe_allow_html=True,
)

db = get_supabase()
ai = get_openai()
MODEL = st.secrets.get("OPENAI_MODEL", "gpt-5.4")

# ==================================================
# STATE
# ==================================================
if "page" not in st.session_state:
    st.session_state.page = "hoje"
if "sel_date" not in st.session_state:
    st.session_state.sel_date = local_today()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ==================================================
# DATA HELPERS
# ==================================================
def q(table, select="*", **filters):
    try:
        query = db.table(table).select(select)
        for k, v in filters.items():
            query = query.eq(k, v)
        res = query.execute()
        return res.data or []
    except Exception:
        return []


def safe_execute(fn):
    try:
        res = fn()
        return True, getattr(res, "data", None)
    except Exception as e:
        return False, str(e)


DEFAULT_GOALS = {
    "weight": {"metric": "weight", "target_value": 99.9, "label": "meta intermediária"},
    "weight_long_term": {"metric": "weight_long_term", "target_value": 90.0, "label": "meta longa"},
    "kcal_daily": {"metric": "kcal_daily", "target_value": 2400, "label": "calorias"},
    "protein_daily": {"metric": "protein_daily", "target_value": 190, "label": "proteína"},
    "carb_daily": {"metric": "carb_daily", "target_value": 190, "label": "carboidratos"},
    "fat_daily": {"metric": "fat_daily", "target_value": 70, "label": "gorduras"},
    "water_daily_ml": {"metric": "water_daily_ml", "target_value": 4000, "label": "água"},
}

STRATEGY_TEXT = {
    "title": "Perder gordura sem desmontar sua estrutura.",
    "copy": "O foco do app agora é déficit controlado, proteína alta, treino de força, hidratação e sono. O objetivo não é só descer peso; é reduzir gordura preservando massa magra e diminuindo o risco de flacidez por perda mal conduzida.",
    "focus": "Sair dos 3 dígitos com consistência, sem transformar o processo em restrição caótica.",
}
PROJECT_PROFILE = {
    "start_date": date(2026, 3, 25),
    "start_weight": 143.7,
    "goal_weight_intermediate": 99.9,
    "goal_weight_final": 90.0,
    "expected_loss_per_week_min": 0.4,
    "expected_loss_per_week_ideal": 0.8,
    "expected_loss_per_week_max_safe": 1.2,
}
def clamp_weight_to_goal(weight_value: float) -> float:
    return max(PROJECT_PROFILE["goal_weight_final"], round(weight_value, 1))


def get_projected_weight(date_value, weekly_loss):
    start_date = PROJECT_PROFILE["start_date"]
    start_weight = PROJECT_PROFILE["start_weight"]

    if date_value <= start_date:
        return start_weight

    days_elapsed = (date_value - start_date).days
    weeks_elapsed = days_elapsed / 7
    projected = start_weight - (weeks_elapsed * weekly_loss)
    return clamp_weight_to_goal(projected)


def get_weight_curve_status(actual_weight, date_value):
    if actual_weight is None:
        return {
            "status": "sem_peso",
            "label": "sem peso registrado",
            "projected_min": get_projected_weight(date_value, PROJECT_PROFILE["expected_loss_per_week_min"]),
            "projected_ideal": get_projected_weight(date_value, PROJECT_PROFILE["expected_loss_per_week_ideal"]),
            "projected_max_safe": get_projected_weight(date_value, PROJECT_PROFILE["expected_loss_per_week_max_safe"]),
        }

    projected_min = get_projected_weight(date_value, PROJECT_PROFILE["expected_loss_per_week_min"])
    projected_ideal = get_projected_weight(date_value, PROJECT_PROFILE["expected_loss_per_week_ideal"])
    projected_max_safe = get_projected_weight(date_value, PROJECT_PROFILE["expected_loss_per_week_max_safe"])

    tolerance = 0.5

    if actual_weight > projected_min + tolerance:
        status = "claramente_atrasado"
        label = "acima da faixa projetada"
    elif actual_weight < projected_max_safe - tolerance:
        status = "queda_rapida_demais"
        label = "queda rápida demais"
    elif abs(actual_weight - projected_ideal) <= tolerance:
        status = "na_curva_ideal"
        label = "na curva ideal"
    else:
        status = "dentro_da_faixa"
        label = "dentro da faixa"

    return {
        "status": status,
        "label": label,
        "projected_min": projected_min,
        "projected_ideal": projected_ideal,
        "projected_max_safe": projected_max_safe,
    }


def get_monthly_target_rows(end_date):
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)

    start_date = PROJECT_PROFILE["start_date"]
    rows = []

    cursor = date(start_date.year, start_date.month, 1)

    while cursor <= end_date:
        if cursor.month == 12:
            month_end = date(cursor.year, 12, 31)
        else:
            month_end = date(cursor.year, cursor.month + 1, 1) - timedelta(days=1)

        if month_end < start_date:
            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, 1)
            else:
                cursor = date(cursor.year, cursor.month + 1, 1)
            continue

        ref_date = min(month_end, end_date)
        ideal_weight = get_projected_weight(ref_date, PROJECT_PROFILE["expected_loss_per_week_ideal"])

        rows.append(
            {
                "month_label": ref_date.strftime("%m/%Y"),
                "date": ref_date,
                "target_weight": round(ideal_weight, 1),
            }
        )

        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    return rows
    

DEFAULT_CHECKLIST_ITEMS = [
    {"item_key": "euthyrox", "name": "Euthyrox", "time_slot": "jejum", "dosage": "25 mcg", "instruction": "Tomar sozinho, com água, em jejum.", "sort_order": 1, "active": True},
    {"item_key": "sertralina", "name": "Sertralina", "time_slot": "manha", "dosage": "200 mg", "instruction": "Pela manhã.", "sort_order": 2, "active": True},
    {"item_key": "b12", "name": "B12", "time_slot": "manha", "dosage": "1000 mcg", "instruction": "No café da manhã.", "sort_order": 3, "active": True},
    {"item_key": "creatina", "name": "Creatina", "time_slot": "variavel", "dosage": "3–5 g", "instruction": "Uso diário.", "sort_order": 4, "active": True},
    {"item_key": "pantoprazol", "name": "Pantoprazol", "time_slot": "almoco", "dosage": "40 mg", "instruction": "No meio do dia.", "sort_order": 5, "active": True},
    {"item_key": "omega3_almoco", "name": "Ômega 3", "time_slot": "almoco", "dosage": "1 cápsula", "instruction": "Parte da dose do dia.", "sort_order": 6, "active": True},
    {"item_key": "omega3_jantar", "name": "Ômega 3", "time_slot": "jantar", "dosage": "2 cápsulas", "instruction": "Completar dose do dia.", "sort_order": 7, "active": True},
    {"item_key": "dprev", "name": "Vitamina D (DPrev)", "time_slot": "jantar", "dosage": "5000 UI", "instruction": "No jantar.", "sort_order": 8, "active": True},
    {"item_key": "estat_eze", "name": "Rosucor/Plenance EZE", "time_slot": "jantar", "dosage": "5/10 mg", "instruction": "No jantar.", "sort_order": 9, "active": True},
    {"item_key": "lipidil", "name": "Lipidil", "time_slot": "jantar", "dosage": "160 mg", "instruction": "No jantar.", "sort_order": 10, "active": True},
    {"item_key": "magnesio", "name": "Magnésio", "time_slot": "noite", "dosage": "2 cápsulas", "instruction": "À noite, longe do Euthyrox.", "sort_order": 11, "active": True},
    {"item_key": "trazodona", "name": "Trazodona", "time_slot": "noite", "dosage": "50 mg", "instruction": "Após lanche leve.", "sort_order": 12, "active": True},
    {"item_key": "cpap", "name": "CPAP", "time_slot": "noite", "dosage": "usar", "instruction": "Marcar se usou na noite.", "sort_order": 13, "active": True},
    {"item_key": "treino", "name": "Treino", "time_slot": "variavel", "dosage": "feito", "instruction": "Marcar quando o treino realmente aconteceu.", "sort_order": 14, "active": True},
]

ALCOHOL_KEYS = {
    "cerveja_garrafa", "caipirinha", "gin_tonica", "whisky_dose", "vodka_mixer_zero",
    "vinho_taca", "destilado_dose", "chopp", "aperol_spritz", "cerveja_lata", "cerveja_long", "cerveja_600"
}

LOCAL_FOOD_LIBRARY = [
    {"food_key": "agua", "name": "Água", "default_portion_g": 300, "kcal_per_100g": 0, "protein_per_100g": 0, "carbs_per_100g": 0, "fat_per_100g": 0, "active": True},
    {"food_key": "cafe_puro", "name": "Café puro", "default_portion_g": 100, "kcal_per_100g": 2, "protein_per_100g": 0.3, "carbs_per_100g": 0, "fat_per_100g": 0, "active": True},
    {"food_key": "coca_zero_lata", "name": "Coca-Cola Zero lata", "default_portion_g": 350, "kcal_per_100g": 0.3, "protein_per_100g": 0, "carbs_per_100g": 0.1, "fat_per_100g": 0, "active": True},
    {"food_key": "refrigerante_normal_lata", "name": "Refrigerante normal lata", "default_portion_g": 350, "kcal_per_100g": 42, "protein_per_100g": 0, "carbs_per_100g": 10.6, "fat_per_100g": 0, "active": True},
    {"food_key": "suco_laranja", "name": "Suco de laranja", "default_portion_g": 300, "kcal_per_100g": 45, "protein_per_100g": 0.7, "carbs_per_100g": 10.4, "fat_per_100g": 0.2, "active": True},
    {"food_key": "ovo_mexido", "name": "Ovo mexido", "default_portion_g": 100, "kcal_per_100g": 148, "protein_per_100g": 10.5, "carbs_per_100g": 1.6, "fat_per_100g": 11.2, "active": True},
    {"food_key": "tapioca", "name": "Tapioca", "default_portion_g": 100, "kcal_per_100g": 160, "protein_per_100g": 0.2, "carbs_per_100g": 39, "fat_per_100g": 0.1, "active": True},
    {"food_key": "granola", "name": "Granola", "default_portion_g": 30, "kcal_per_100g": 430, "protein_per_100g": 10, "carbs_per_100g": 64, "fat_per_100g": 14, "active": True},
    {"food_key": "maca", "name": "Maçã", "default_portion_g": 130, "kcal_per_100g": 52, "protein_per_100g": 0.3, "carbs_per_100g": 14, "fat_per_100g": 0.2, "active": True},
    {"food_key": "pasta_amendoim", "name": "Pasta de amendoim", "default_portion_g": 15, "kcal_per_100g": 588, "protein_per_100g": 25, "carbs_per_100g": 20, "fat_per_100g": 50, "active": True},
    {"food_key": "frango_desfiado", "name": "Frango desfiado", "default_portion_g": 120, "kcal_per_100g": 163, "protein_per_100g": 31, "carbs_per_100g": 0, "fat_per_100g": 3.6, "active": True},
    {"food_key": "tilapia", "name": "Tilápia", "default_portion_g": 120, "kcal_per_100g": 128, "protein_per_100g": 26, "carbs_per_100g": 0, "fat_per_100g": 2.7, "active": True},
    {"food_key": "atum_lata", "name": "Atum em lata", "default_portion_g": 120, "kcal_per_100g": 116, "protein_per_100g": 26, "carbs_per_100g": 0, "fat_per_100g": 1.0, "active": True},
    {"food_key": "batata_doce", "name": "Batata-doce cozida", "default_portion_g": 120, "kcal_per_100g": 86, "protein_per_100g": 1.6, "carbs_per_100g": 20, "fat_per_100g": 0.1, "active": True},
    {"food_key": "farofa", "name": "Farofa", "default_portion_g": 30, "kcal_per_100g": 410, "protein_per_100g": 2.5, "carbs_per_100g": 70, "fat_per_100g": 12, "active": True},
    {"food_key": "pizza_mucarela_fatia", "name": "Pizza de muçarela (fatia)", "default_portion_g": 120, "kcal_per_100g": 285, "protein_per_100g": 12, "carbs_per_100g": 31, "fat_per_100g": 13, "active": True},
    {"food_key": "pizza_calabresa_fatia", "name": "Pizza de calabresa (fatia)", "default_portion_g": 120, "kcal_per_100g": 296, "protein_per_100g": 12, "carbs_per_100g": 28, "fat_per_100g": 15, "active": True},
    {"food_key": "miojo_preparado", "name": "Miojo preparado", "default_portion_g": 160, "kcal_per_100g": 188, "protein_per_100g": 4.2, "carbs_per_100g": 25.5, "fat_per_100g": 8.3, "active": True},
    {"food_key": "hamburguer_artesanal", "name": "Hambúrguer artesanal", "default_portion_g": 220, "kcal_per_100g": 250, "protein_per_100g": 14, "carbs_per_100g": 18, "fat_per_100g": 14, "active": True},
    {"food_key": "batata_frita", "name": "Batata frita", "default_portion_g": 100, "kcal_per_100g": 312, "protein_per_100g": 3.4, "carbs_per_100g": 41, "fat_per_100g": 15, "active": True},
    {"food_key": "big_mac", "name": "Big Mac", "default_portion_g": 215, "kcal_per_100g": 257, "protein_per_100g": 12.8, "carbs_per_100g": 20, "fat_per_100g": 15, "active": True},
    {"food_key": "mc_fritas_media", "name": "McFritas média", "default_portion_g": 110, "kcal_per_100g": 307, "protein_per_100g": 3.5, "carbs_per_100g": 41, "fat_per_100g": 15, "active": True},
    {"food_key": "quarterao", "name": "Quarterão com queijo", "default_portion_g": 200, "kcal_per_100g": 254, "protein_per_100g": 15, "carbs_per_100g": 21, "fat_per_100g": 13, "active": True},
    {"food_key": "mc_nuggets_6", "name": "McNuggets 6 un", "default_portion_g": 100, "kcal_per_100g": 261, "protein_per_100g": 15, "carbs_per_100g": 15, "fat_per_100g": 15, "active": True},
    {"food_key": "sorvete_pote", "name": "Sorvete de pote", "default_portion_g": 100, "kcal_per_100g": 207, "protein_per_100g": 3.5, "carbs_per_100g": 24, "fat_per_100g": 11, "active": True},
    {"food_key": "chocolate_ao_leite", "name": "Chocolate ao leite", "default_portion_g": 25, "kcal_per_100g": 535, "protein_per_100g": 7.2, "carbs_per_100g": 59, "fat_per_100g": 30, "active": True},
    {"food_key": "bolo_chocolate", "name": "Bolo de chocolate", "default_portion_g": 80, "kcal_per_100g": 371, "protein_per_100g": 5.6, "carbs_per_100g": 52, "fat_per_100g": 16, "active": True},
    {"food_key": "salgado_padaria", "name": "Salgado de padaria", "default_portion_g": 120, "kcal_per_100g": 320, "protein_per_100g": 9, "carbs_per_100g": 28, "fat_per_100g": 18, "active": True},
    {"food_key": "pao_de_queijo", "name": "Pão de queijo", "default_portion_g": 50, "kcal_per_100g": 330, "protein_per_100g": 6, "carbs_per_100g": 34, "fat_per_100g": 18, "active": True},
    {"food_key": "feijao_tropeiro", "name": "Feijão tropeiro", "default_portion_g": 120, "kcal_per_100g": 230, "protein_per_100g": 8, "carbs_per_100g": 22, "fat_per_100g": 12, "active": True},
    {"food_key": "churrasco_selfservice", "name": "Churrasco self-service", "default_portion_g": 200, "kcal_per_100g": 250, "protein_per_100g": 20, "carbs_per_100g": 8, "fat_per_100g": 15, "active": True},
    {"food_key": "yakisoba", "name": "Yakisoba", "default_portion_g": 250, "kcal_per_100g": 140, "protein_per_100g": 7, "carbs_per_100g": 18, "fat_per_100g": 4, "active": True},
    {"food_key": "temaki_salmao", "name": "Temaki de salmão", "default_portion_g": 160, "kcal_per_100g": 190, "protein_per_100g": 10, "carbs_per_100g": 21, "fat_per_100g": 6, "active": True},
    {"food_key": "sushi_12", "name": "Combinado sushi 12 peças", "default_portion_g": 240, "kcal_per_100g": 145, "protein_per_100g": 8, "carbs_per_100g": 21, "fat_per_100g": 3, "active": True},
    {"food_key": "cerveja_garrafa", "name": "Cerveja garrafa 600 ml", "default_portion_g": 600, "kcal_per_100g": 43, "protein_per_100g": 0.5, "carbs_per_100g": 3.5, "fat_per_100g": 0, "active": True},
    {"food_key": "caipirinha", "name": "Caipirinha", "default_portion_g": 250, "kcal_per_100g": 90, "protein_per_100g": 0, "carbs_per_100g": 12, "fat_per_100g": 0, "active": True},
    {"food_key": "gin_tonica", "name": "Gin tônica", "default_portion_g": 250, "kcal_per_100g": 65, "protein_per_100g": 0, "carbs_per_100g": 7, "fat_per_100g": 0, "active": True},
    {"food_key": "whisky_dose", "name": "Whisky dose", "default_portion_g": 50, "kcal_per_100g": 220, "protein_per_100g": 0, "carbs_per_100g": 0, "fat_per_100g": 0, "active": True},
    {"food_key": "vodka_mixer_zero", "name": "Vodka + mixer zero", "default_portion_g": 200, "kcal_per_100g": 60, "protein_per_100g": 0, "carbs_per_100g": 0.2, "fat_per_100g": 0, "active": True},
]


def merge_food_libraries(remote_foods, local_foods):
    merged = {f['food_key']: f for f in local_foods}
    for f in remote_foods:
        merged[f['food_key']] = f
    return sorted(merged.values(), key=lambda f: f['name'].lower())


def get_goals():
    rows = q("goals", active=True)
    merged = {k: dict(v) for k, v in DEFAULT_GOALS.items()}
    for r in rows:
        merged[r["metric"]] = r
    return merged


def get_weight_history(days=30, end_date=None):
    end_d = end_date or local_today()
    start = (end_d - timedelta(days=days - 1)).isoformat()
    end_s = end_d.isoformat()
    res = (
        db.table("daily_weight")
        .select("date,weight_kg")
        .gte("date", start)
        .lte("date", end_s)
        .order("date")
        .execute()
    )
    return res.data or []


def get_weight(dt):
    rows = q("daily_weight", date=dt)
    return float(rows[0]["weight_kg"]) if rows else None


def save_weight(dt, kg):
    db.table("daily_weight").upsert({"date": dt, "weight_kg": kg}, on_conflict="date").execute()


def get_checklist_items():
    try:
        res = db.table("checklist_items").select("*").eq("active", True).order("sort_order").execute()
        remote = res.data or []
    except Exception:
        remote = []
    merged = {item["item_key"]: dict(item) for item in DEFAULT_CHECKLIST_ITEMS}
    for item in remote:
        merged[item["item_key"]] = item
    return sorted(merged.values(), key=lambda x: int(x.get("sort_order") or 999))


def get_checklist(dt):
    rows = q("checklist_daily", date=dt)
    return {r["item_key"]: r for r in rows}


def save_check(dt, key, done):
    db.table("checklist_daily").upsert({"date": dt, "item_key": key, "done": done}, on_conflict="date,item_key").execute()


def get_meals(dt):
    return q("meals", date=dt)


def get_foods():
    try:
        res = db.table("food_library").select("*").eq("active", True).order("name").execute()
        remote = res.data or []
    except Exception:
        remote = []
    return merge_food_libraries(remote, LOCAL_FOOD_LIBRARY)


def get_sleep(dt):
    rows = q("sleep_cpap", date=dt)
    return rows[0] if rows else {}


def get_workout(dt):
    rows = q("workout_logs", date=dt)
    return rows[0] if rows else {}


def save_workout(dt, payload):
    data = {"date": dt, **payload}
    return safe_execute(lambda: db.table("workout_logs").upsert(data, on_conflict="date").execute())


def get_hydration(dt):
    rows = q("hydration_daily", date=dt)
    return rows[0] if rows else {}


def save_hydration(dt, water_ml):
    data = {"date": dt, "water_ml": water_ml}
    return safe_execute(lambda: db.table("hydration_daily").upsert(data, on_conflict="date").execute())


def get_last_known_weight(dt_iso):
    try:
        res = (
            db.table("daily_weight")
            .select("date,weight_kg")
            .lte("date", dt_iso)
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return float(rows[0]["weight_kg"]) if rows else None
    except Exception:
        return None


def get_daily_closure(dt_iso):
    rows = q("daily_closure", date=dt_iso)
    return rows[0] if rows else {}


def save_daily_closure(payload):
    return safe_execute(lambda: db.table("daily_closure").upsert(payload, on_conflict="date").execute())


def meal_totals(meals):
    return {
        "kcal": sum(float(m.get("kcal") or 0) for m in meals),
        "prot": sum(float(m.get("protein_g") or 0) for m in meals),
        "carb": sum(float(m.get("carbs_g") or 0) for m in meals),
        "fat": sum(float(m.get("fat_g") or 0) for m in meals),
    }


def day_completeness(dt):
    score = 0
    if get_weight(dt):
        score += 1
    meals = get_meals(dt)
    if len(meals) >= 3:
        score += 2
    elif len(meals) >= 1:
        score += 1
    ck = get_checklist(dt)
    routine_items = [i for i in get_checklist_items() if is_routine_item(i)]
    done_count = sum(1 for i in routine_items if ck.get(i["item_key"], {}).get("done"))
    if done_count >= max(1, int(len(routine_items) * 0.8)):
        score += 2
    elif done_count >= max(1, int(len(routine_items) * 0.4)):
        score += 1
    if get_sleep(dt):
        score += 1
    if score >= 5:
        return "green"
    if score >= 3:
        return "yellow"
    if score >= 1:
        return "red"
    return "gray"


# ==================================================
# DOMAIN RULES
# ==================================================
MEAL_CONFIG = {
    "cafe": {
        "label": "☕ Café da manhã",
        "foods": [
            "ovo_cozido", "ovo_mexido", "whey_dose", "suco_verde", "leite_desnatado", "pao_integral",
            "banana", "maca", "aveia", "iogurte_grego", "cafe_puro", "queijo_branco", "tapioca", "granola", "pao_de_queijo", "suco_laranja", "agua", "coca_zero_lata"
        ],
    },
    "almoco": {
        "label": "🍚 Almoço",
        "foods": [
            "arroz_branco", "feijao_cozido", "arroz_feijao", "frango_grelhado", "frango_desfiado", "patinho_moido",
            "carne_magra", "lombo_suino", "batata_cozida", "batata_doce", "mandioca_cozida", "lentilha",
            "alface", "rucula", "tomate", "cenoura_crua", "beterraba", "chuchu", "vagem",
            "couve_cozida", "azeite", "farofa", "feijao_tropeiro", "churrasco_selfservice", "yakisoba",
            "agua", "refri_zero", "coca_zero_lata", "refrigerante_normal_lata"
        ],
    },
    "lanche": {
        "label": "🥪 Lanche / pré-treino",
        "foods": [
            "pao_integral", "whey_dose", "iogurte_grego", "banana", "maca", "queijo_branco",
            "castanhas", "cafe_puro", "leite_desnatado", "requeijao_light", "aveia", "pao_de_queijo", "salgado_padaria", "pasta_amendoim", "agua", "refri_zero", "coca_zero_lata"
        ],
    },
    "jantar": {
        "label": "🍽️ Jantar",
        "foods": [
            "macarrao_cozido", "miojo_preparado", "arroz_branco", "frango_grelhado", "patinho_moido", "carne_magra",
            "hamburguer_caseiro", "hamburguer_artesanal", "big_mac", "quarterao", "mc_nuggets_6", "mc_fritas_media",
            "mussarela", "pao_integral", "sopa_lentilha", "caldo_abobora", "pizza_mucarela_fatia", "pizza_calabresa_fatia",
            "alface", "rucula", "tomate", "cenoura_crua", "couve_cozida", "agua", "refri_zero", "coca_zero_lata", "refrigerante_normal_lata"
        ],
    },
    "ceia": {
        "label": "🌙 Ceia",
        "foods": [
            "iogurte_grego", "whey_dose", "queijo_branco", "banana", "leite_desnatado", "castanhas", "chocolate_ao_leite", "sorvete_pote", "bolo_chocolate", "agua"
        ],
    },
    "bebida": {
        "label": "🥤 Bebidas fora da refeição",
        "foods": [
            "agua", "cafe_puro", "refri_zero", "coca_zero_lata", "refrigerante_normal_lata", "suco_laranja", "cerveja_lata", "cerveja_long", "cerveja_600", "cerveja_garrafa",
            "vinho_taca", "destilado_dose", "whisky_dose", "caipirinha", "gin_tonica", "vodka_mixer_zero", "chopp", "xeque_mate_lata", "aperol_spritz"
        ],
    },
}

FOOD_ONLY_KEYS = {"suco_verde", "whey", "whey_dose"}
NON_ROUTINE_TERMS = ["suco", "whey", "café da manhã", "almoco", "almoço", "jantar", "ceia", "agua", "água", "bebida"]


def is_routine_item(item):
    name = (item.get("name") or "").lower()
    key = (item.get("item_key") or "").lower()
    instruction = (item.get("instruction") or "").lower()
    text = f"{name} {key} {instruction}"
    if key in FOOD_ONLY_KEYS:
        return False
    return not any(term in text for term in NON_ROUTINE_TERMS)


def meal_context_options(meal_key, foods, show_all=False):
    suggested = set(MEAL_CONFIG[meal_key]["foods"])
    if show_all:
        selected = foods
    else:
        selected = [f for f in foods if f["food_key"] in suggested]
    return sorted(selected, key=lambda f: f["name"].lower())


def format_date_label(d: date) -> str:
    today = local_today()
    dias_pt = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    if d == today:
        return f"Hoje — {d.strftime('%d/%m/%Y')}"
    if d == today - timedelta(days=1):
        return f"Ontem — {d.strftime('%d/%m/%Y')}"
    return f"{dias_pt[d.weekday()].capitalize()} — {d.strftime('%d/%m/%Y')}"


def parse_time_field(value, default: time | None = None):
    if isinstance(value, time):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.strptime(value[:5], "%H:%M").time()
        except Exception:
            pass
    return default


def compute_sleep_hours(bed_t, wake_t):
    if not bed_t or not wake_t:
        return None
    ref_day = local_today()
    bed_dt = datetime.combine(ref_day, bed_t)
    wake_dt = datetime.combine(ref_day, wake_t)
    if wake_dt <= bed_dt:
        wake_dt += timedelta(days=1)
    return round((wake_dt - bed_dt).total_seconds() / 3600, 2)




def slugify_text(text):
    text = (text or "").strip().lower()
    chars = []
    for ch in text:
        if ch.isalnum():
            chars.append(ch)
        elif ch in " -_/|":
            chars.append("_")
    slug = "".join(chars)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")[:40] or "item_customizado"


def estimate_custom_food(description, grams_ml=100):
    if ai is None:
        return {"error": "A chave da OpenAI não está configurada."}
    prompt = f"""Estime macros e calorias de forma plausível para o alimento descrito abaixo, considerando a porção informada. Responda apenas em JSON válido com as chaves: name, kcal, protein_g, carbs_g, fat_g, portion_g, rationale.

Alimento: {description}
Porção: {grams_ml} g ou ml

Use estimativa prática de app nutricional, sem discurso.
"""
    try:
        response = ai.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": "Você estima calorias e macros de alimentos para um diário alimentar. Responda só JSON."},
                {"role": "user", "content": prompt},
            ],
            max_output_tokens=220,
        )
        raw = getattr(response, "output_text", "") or ""
    except Exception:
        try:
            response = ai.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Você estima calorias e macros de alimentos para um diário alimentar. Responda só JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=220,
            )
            raw = response.choices[0].message.content or ""
        except Exception as e:
            return {"error": f"Erro ao estimar item: {e}"}
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        payload = json.loads(raw[start:end])
        return payload
    except Exception:
        return {"error": f"A IA não retornou JSON utilizável. Resposta: {raw[:300]}"}


def target_snapshot(goals):
    return {
        "kcal": float(goals.get("kcal_daily", {}).get("target_value", 2400)),
        "protein": float(goals.get("protein_daily", {}).get("target_value", 190)),
        "carb": float(goals.get("carb_daily", {}).get("target_value", 190)),
        "fat": float(goals.get("fat_daily", {}).get("target_value", 70)),
        "water_ml": float(goals.get("water_daily_ml", {}).get("target_value", 4000)),
        "weight_goal": float(goals.get("weight", {}).get("target_value", 99.9)),
        "weight_long": float(goals.get("weight_long_term", {}).get("target_value", 90)),
    }


def food_status_class(kcal, prot, goals):
    kcal_goal = float(goals.get("kcal_daily", {}).get("target_value", 2400))
    protein_goal = float(goals.get("protein_daily", {}).get("target_value", 190))
    if kcal <= 0:
        return None, None
    if kcal <= kcal_goal * 1.08 and prot >= protein_goal * 0.9:
        return "g", "🟢 Dia coerente com a estratégia"
    if kcal <= kcal_goal * 1.22 or prot >= protein_goal * 0.7:
        return "y", "🟡 Revise calorias ou proteína"
    return "r", "🔴 Dia fora da estratégia"


def overall_status(dt_iso, goals):
    meals = get_meals(dt_iso)
    checklist = get_checklist(dt_iso)
    sleep = get_sleep(dt_iso)
    routine_items = [i for i in get_checklist_items() if is_routine_item(i)]
    routine_total = len(routine_items)
    routine_done = sum(1 for i in routine_items if checklist.get(i["item_key"], {}).get("done"))
    t = meal_totals(meals)
    score = 0
    if t["kcal"] > 0:
        if t["kcal"] <= float(goals.get("kcal_daily", {}).get("target_value", 2400)) * 1.1:
            score += 35
        else:
            score += 18
        if t["prot"] >= float(goals.get("protein_daily", {}).get("target_value", 190)) * 0.85:
            score += 25
        else:
            score += 10
    if routine_total:
        score += int((routine_done / routine_total) * 25)
    if sleep:
        score += 15
    if score >= 80:
        return "g", f"aderente · {score}/100"
    if score >= 55:
        return "y", f"parcial · {score}/100"
    return "r", f"fraco · {score}/100"


def compute_daily_score(goals, meals, checklist, sleep, workout=None, hydration=None):
    workout = workout or {}
    hydration = hydration or {}
    totals = meal_totals(meals)
    kcal_goal = float(goals.get("kcal_daily", {}).get("target_value", 2400))
    protein_goal = float(goals.get("protein_daily", {}).get("target_value", 190))
    water_goal = float(goals.get("water_daily_ml", {}).get("target_value", 4000))

    # Alimentação 30
    if totals["kcal"] <= 0:
        food_points = 0
    else:
        if totals["kcal"] <= kcal_goal * 1.05:
            kcal_points = 15
        elif totals["kcal"] <= kcal_goal * 1.15:
            kcal_points = 12
        elif totals["kcal"] <= kcal_goal * 1.30:
            kcal_points = 8
        elif totals["kcal"] <= kcal_goal * 1.45:
            kcal_points = 4
        else:
            kcal_points = 0

        meal_count = len(meals)
        if meal_count >= 4:
            structure_points = 10
        elif meal_count == 3:
            structure_points = 8
        elif meal_count == 2:
            structure_points = 4
        else:
            structure_points = 2

        alcohol_count = sum(1 for m in meals if (m.get("food_key") or "") in ALCOHOL_KEYS)
        if alcohol_count == 0:
            context_points = 5
        elif alcohol_count == 1 and totals["kcal"] <= kcal_goal * 1.15:
            context_points = 3
        else:
            context_points = 1

        food_points = kcal_points + structure_points + context_points

    # Proteína 20
    prot_ratio = 0 if protein_goal <= 0 else totals["prot"] / protein_goal
    if prot_ratio >= 1.0:
        protein_points = 20
    elif prot_ratio >= 0.9:
        protein_points = 17
    elif prot_ratio >= 0.8:
        protein_points = 13
    elif prot_ratio >= 0.65:
        protein_points = 8
    elif totals["prot"] > 0:
        protein_points = 4
    else:
        protein_points = 0

    # Treino 20
    trained = bool(checklist.get("treino", {}).get("done")) or bool(workout.get("workout_type"))
    if trained and workout.get("duration_min"):
        workout_points = 20
    elif trained:
        workout_points = 16
    else:
        workout_points = 0

    # Sono + CPAP 15
    total_hours = float((sleep or {}).get("total_hours") or 0)
    cpap_hours = float((sleep or {}).get("cpap_hours") or 0)
    used_cpap = bool((sleep or {}).get("used_cpap"))
    if total_hours >= 7:
        sleep_points = 15
    elif total_hours >= 6:
        sleep_points = 11
    elif total_hours > 0:
        sleep_points = 7
    else:
        sleep_points = 0
    if used_cpap and cpap_hours and cpap_hours < 4:
        sleep_points = max(0, sleep_points - 2)

    # Rotina 10
    routine_items = [i for i in get_checklist_items() if is_routine_item(i) and i.get("item_key") not in {"treino", "cpap"}]
    routine_total = len(routine_items)
    if routine_total:
        routine_done = sum(1 for i in routine_items if checklist.get(i["item_key"], {}).get("done"))
        routine_points = round((routine_done / routine_total) * 10)
    else:
        routine_points = 0

    # Água 5
    water_ml = float(hydration.get("water_ml") or 0)
    water_ratio = 0 if water_goal <= 0 else water_ml / water_goal
    if water_ratio >= 1:
        water_points = 5
    elif water_ratio >= 0.8:
        water_points = 4
    elif water_ratio >= 0.6:
        water_points = 3
    elif water_ml > 0:
        water_points = 1
    else:
        water_points = 0

    breakdown = {
        "alimentacao": int(food_points),
        "proteina": int(protein_points),
        "treino": int(workout_points),
        "sono_cpap": int(sleep_points),
        "rotina": int(routine_points),
        "agua": int(water_points),
    }
    total = sum(breakdown.values())

    # travas
    if workout_points == 0 and protein_points <= 8:
        total = min(total, 59)
    if food_points == 0 and sleep_points == 0:
        total = min(total, 39)

    if total >= 85:
        label = "dia forte"
        klass = "g"
    elif total >= 70:
        label = "dia bom"
        klass = "g"
    elif total >= 55:
        label = "dia parcial"
        klass = "y"
    else:
        label = "dia fraco"
        klass = "r"

    return {"total": int(total), "label": label, "class": klass, "breakdown": breakdown}


def render_score_card(score_data):
    breakdown = score_data["breakdown"]
    rows = [
        ("Alimentação", breakdown["alimentacao"], 30),
        ("Proteína", breakdown["proteina"], 20),
        ("Treino", breakdown["treino"], 20),
        ("Sono + CPAP", breakdown["sono_cpap"], 15),
        ("Rotina", breakdown["rotina"], 10),
        ("Água", breakdown["agua"], 5),
    ]
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title" style="margin-top:0">Fechamento do dia</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big">{score_data["total"]}/100</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="status {score_data["class"]}">{score_data["label"]}</span>', unsafe_allow_html=True)
    for label, value, total in rows:
        pct = 0 if total <= 0 else int((value / total) * 100)
        st.markdown(f"**{label}** · {value}/{total}")
        st.progress(pct / 100)
    st.markdown('</div>', unsafe_allow_html=True)


def period_summary(days):
    end_d = st.session_state.sel_date
    start_d = end_d - timedelta(days=days - 1)
    start = start_d.isoformat()
    end_s = end_d.isoformat()

    meals = db.table("meals").select("date,meal_type,kcal,protein_g,carbs_g,fat_g,food_key").gte("date", start).lte("date", end_s).execute().data or []
    sleep_rows = db.table("sleep_cpap").select("date,total_hours,energy_score,ahi").gte("date", start).lte("date", end_s).execute().data or []
    checks = db.table("checklist_daily").select("date,item_key,done").gte("date", start).lte("date", end_s).execute().data or []
    try:
        hydration_rows = db.table("hydration_daily").select("date,water_ml").gte("date", start).lte("date", end_s).execute().data or []
    except Exception:
        hydration_rows = []
    weights = get_weight_history(days, end_date=end_d)

    try:
        workouts = db.table("workout_logs").select("date,workout_type,duration_min,strength_split").gte("date", start).lte("date", end_s).execute().data or []
    except Exception:
        workouts = []

    by_day = {}
    for m in meals:
        d = m["date"]
        by_day.setdefault(d, {"kcal": 0.0, "prot": 0.0, "meals": 0})
        by_day[d]["kcal"] += float(m.get("kcal") or 0)
        by_day[d]["prot"] += float(m.get("protein_g") or 0)
        by_day[d]["meals"] += 1

    sleep_map = {r["date"]: r for r in sleep_rows}
    routine_items = [i for i in get_checklist_items() if is_routine_item(i)]
    routine_keys = {i["item_key"] for i in routine_items}
    routine_total = len(routine_keys)

    routine_counts = {}
    treino_days = set()
    for r in checks:
        d = r["date"]
        if r.get("item_key") == "treino" and r.get("done"):
            treino_days.add(d)
        if r.get("item_key") in routine_keys:
            routine_counts.setdefault(d, {"done": 0})
            if r.get("done"):
                routine_counts[d]["done"] += 1

    workout_days = {r["date"] for r in workouts}
    treino_days = treino_days | workout_days

    active_days = sorted(set(list(by_day.keys()) + list(sleep_map.keys()) + list(routine_counts.keys()) + list(treino_days)))
    meal_days = sum(1 for d in by_day if by_day[d]["meals"] > 0)
    meal_days_3plus = sum(1 for d in by_day if by_day[d]["meals"] >= 3)
    sleep_days = len(sleep_map)
    avg_kcal = mean([by_day[d]["kcal"] for d in by_day]) if by_day else 0
    avg_prot = mean([by_day[d]["prot"] for d in by_day]) if by_day else 0
    avg_sleep = mean([float(r.get("total_hours") or 0) for r in sleep_rows if r.get("total_hours")]) if sleep_rows else 0
    avg_energy = mean([int(r.get("energy_score") or 0) for r in sleep_rows if r.get("energy_score") is not None]) if sleep_rows else 0
    avg_ahi = mean([float(r.get("ahi") or 0) for r in sleep_rows if r.get("ahi") is not None]) if sleep_rows else 0
    avg_water_ml = mean([float(r.get("water_ml") or 0) for r in hydration_rows if r.get("water_ml") is not None]) if hydration_rows else 0
    water_days = len([r for r in hydration_rows if r.get("water_ml")])
    filled_days = sum(1 for d in active_days if (by_day.get(d, {}).get("meals", 0) >= 3 or sleep_map.get(d) or routine_counts.get(d)))

    adherence_values = []
    if routine_total:
        for d in active_days:
            done = routine_counts.get(d, {}).get("done", 0)
            adherence_values.append((done / routine_total) * 100)
    avg_routine_adherence = mean(adherence_values) if adherence_values else 0

    workout_types = [w.get("workout_type") for w in workouts if w.get("workout_type")]
    top_workout_type = None
    if workout_types:
        top_workout_type = max(set(workout_types), key=workout_types.count)

    first_w = float(weights[0]["weight_kg"]) if weights else None
    last_w = float(weights[-1]["weight_kg"]) if weights else None
    treino_ratio = (len(treino_days) / days) * 100 if days else 0

    return {
        "days": days,
        "start": start,
        "end": end_s,
        "avg_kcal": avg_kcal,
        "avg_prot": avg_prot,
        "avg_sleep": avg_sleep,
        "avg_energy": avg_energy,
        "avg_ahi": avg_ahi,
        "avg_water_ml": avg_water_ml,
        "water_days": water_days,
        "treino_days": len(treino_days),
        "treino_ratio": treino_ratio,
        "filled_days": filled_days,
        "active_days": len(active_days),
        "meal_days": meal_days,
        "meal_days_3plus": meal_days_3plus,
        "sleep_days": sleep_days,
        "avg_routine_adherence": avg_routine_adherence,
        "top_workout_type": top_workout_type,
        "first_weight": first_w,
        "last_weight": last_w,
    }


def render_period_summary_card(summary):
    delta = None
    if summary["first_weight"] is not None and summary["last_weight"] is not None:
        delta = summary["last_weight"] - summary["first_weight"]

    consistency_lines = []
    consistency_lines.append(f"Rotina média {summary['avg_routine_adherence']:.0f}%")
    consistency_lines.append(f"Treino em {summary['treino_days']}/{summary['days']} dias")
    consistency_lines.append(f"Sono registrado em {summary['sleep_days']}/{summary['days']} dias")
    consistency_lines.append(f"Alimentação útil em {summary['meal_days_3plus']}/{summary['days']} dias")
    if summary.get("top_workout_type"):
        consistency_lines.append(f"Treino mais frequente: {summary['top_workout_type']}")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"**Resumo dos últimos {summary['days']} dias**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("kcal média", f"{summary['avg_kcal']:.0f}")
    c2.metric("prot média", f"{summary['avg_prot']:.0f}g")
    c3.metric("sono médio", f"{summary['avg_sleep']:.1f}h")
    c4.metric("água média", f"{summary['avg_water_ml']/1000:.1f}L")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("treino", f"{summary['treino_days']} dias")
    c6.metric("rotina", f"{summary['avg_routine_adherence']:.0f}%")
    c7.metric("energia", f"{summary['avg_energy']:.1f}/10")
    c8.metric("água", f"{summary['water_days']}/{summary['days']}")

    if delta is not None:
        st.caption(f"Peso no período: {summary['first_weight']:.1f} → {summary['last_weight']:.1f} kg ({delta:+.1f} kg)")
    st.markdown("**Consistência do período**")
    for line in consistency_lines:
        st.markdown(f"- {line}")
    st.markdown('</div>', unsafe_allow_html=True)


def build_day_review(dt_iso, goals, meals, checklist, sleep, weight, workout=None, hydration=None):
    t = meal_totals(meals)
    kcal_goal = float(goals.get("kcal_daily", {}).get("target_value", 2400))
    protein_goal = float(goals.get("protein_daily", {}).get("target_value", 190))
    routine_items = [i for i in get_checklist_items() if is_routine_item(i)]
    done = sum(1 for i in routine_items if checklist.get(i["item_key"], {}).get("done"))
    total = len(routine_items)
    workout = workout or {}
    hydration = hydration or {}
    water_goal = float(goals.get("water_daily_ml", {}).get("target_value", 4000))
    water_ml = float(hydration.get("water_ml") or 0)
    trained = bool(checklist.get("treino", {}).get("done")) or bool(workout.get("workout_type"))

    positives = []
    attention_items = []
    action_items = []

    def add_attention(text, priority=5):
        attention_items.append((priority, text))

    def add_action(text, priority=5):
        action_items.append((priority, text))

    if t["kcal"] == 0:
        add_attention("Você ainda não registrou alimentação suficiente para ler o dia com segurança.", priority=10)
        add_action("Preencha as refeições antes de confiar na análise.", priority=10)
    else:
        if t["kcal"] <= kcal_goal * 1.08:
            positives.append("As calorias do dia ficaram numa faixa coerente para o objetivo.")
        else:
            add_attention("As calorias passaram do ponto para um dia de corte controlado.", priority=7)
            add_action("Ajuste amanhã a refeição que mais concentrou energia no dia.", priority=7)

        if t["prot"] >= protein_goal * 0.85:
            positives.append("A proteína do dia ficou em nível bom para preservar massa magra.")
        elif t["prot"] > 0:
            add_attention("A proteína ficou abaixo do ideal para preservar massa magra com mais segurança.", priority=8)
            add_action("Suba proteína com comida de verdade no almoço e no jantar.", priority=8)

        if len(meals) <= 2:
            add_attention("O dia está com poucas refeições registradas e isso distorce a leitura.", priority=6)
            add_action("Registre tudo, inclusive quando sair do plano.", priority=6)

        whey_count = sum(1 for m in meals if (m.get("food_key") or "") == "whey_dose")
        if whey_count >= 2:
            add_attention("O dia ficou dependente demais de whey para fechar proteína.", priority=5)
            add_action("Distribua melhor a proteína com refeições principais mais fortes.", priority=5)

    if sleep:
        total_hours = float(sleep.get("total_hours") or 0)
        energy = sleep.get("energy_score")
        if total_hours >= 7:
            positives.append("O sono da noite anterior deu uma base melhor para segurar fome e rotina.")
        elif total_hours > 0:
            add_attention("O sono veio curto e isso tende a piorar fome, energia e aderência.", priority=8)
            add_action("Hoje vale evitar compensar cansaço com calorias líquidas ou belisco solto.", priority=6)
        if energy is not None and int(energy) <= 3:
            add_attention("Sua energia do dia está baixa, então o risco de desorganizar a rotina sobe.", priority=7)
    else:
        add_attention("O sono da noite anterior ainda não foi registrado.", priority=8)
        add_action("Preencha o sono antes de fechar a leitura do dia.", priority=8)

    if water_ml >= water_goal * 0.85:
        positives.append("A água do dia está numa faixa boa para sustentar aderência, treino e sensação de controle.")
    elif water_ml > 0:
        add_attention("A água do dia ficou abaixo da meta. Isso pesa em saciedade, energia e disciplina do processo.", priority=7)
        add_action("Suba água de forma simples: feche o dia com mais 500 ml e abra amanhã já com uma garrafa definida.", priority=7)
    else:
        add_attention("A água do dia ainda não foi registrada. Sem isso, a leitura do seu padrão fica pela metade.", priority=6)
        add_action("Registre a água total do dia ou pelo menos um valor honesto de partida.", priority=6)

    if trained:
        workout_type = workout.get("workout_type")
        split = workout.get("strength_split")
        duration = workout.get("duration_min")
        detail_parts = []
        if workout_type:
            detail_parts.append(workout_type.lower())
        if split:
            detail_parts.append(split.lower())
        if duration:
            detail_parts.append(f"{duration} min")
        detail = " · ".join(detail_parts)
        if detail:
            positives.append(f"Você marcou treino hoje ({detail}), o que ajuda a sustentar força, gasto e consistência.")
        else:
            positives.append("Você marcou treino hoje, o que ajuda a sustentar força, gasto e consistência.")
    else:
        add_attention("Hoje ficou sem treino marcado. Num processo de emagrecimento como o seu, isso pesa porque a frequência de treino ajuda a preservar massa magra e reduz a chance de o corte virar só perda de peso sem qualidade.", priority=9)
        add_action("Se musculação não couber hoje, escolha uma alternativa mínima agora: 20 a 30 minutos de caminhada, cardio leve ou já deixe amanhã definido com horário e tipo de treino.", priority=9)

    if total:
        if done >= max(1, int(total * 0.8)):
            positives.append("A rotina de remédios e suplementos ficou bem executada.")
        elif done < max(1, int(total * 0.5)):
            add_attention("A aderência da rotina ficou baixa no que era previsível executar.", priority=6)
            add_action("Use o checklist como fechamento do dia, não só como lembrete solto.", priority=6)

    if weight is None:
        add_action("Registre o peso do dia para manter o histórico consistente.", priority=4)

    positives = positives[:2] or ["Você já tem dados suficientes para não operar no escuro hoje."]
    attention_items = sorted(attention_items, key=lambda x: x[0], reverse=True)
    action_items = sorted(action_items, key=lambda x: x[0], reverse=True)
    primary_attention = attention_items[0][1] if attention_items else "Nada crítico apareceu hoje, mas ainda vale manter o dia completo."
    primary_action = action_items[0][1] if action_items else "O próximo passo é repetir o básico sem abrir muitas exceções."

    extra_attention = attention_items[1][1] if len(attention_items) > 1 else None
    extra_action = action_items[1][1] if len(action_items) > 1 else None

    html = '<div class="analysis-box"><div class="t">Leitura do dia</div>'
    html += '<div style="font-size:14px;line-height:1.65">'
    html += f"<p style='margin:0 0 10px'><strong>Ponto positivo.</strong> {positives[0]}</p>"
    html += f"<p style='margin:0 0 10px'><strong>Ponto de atenção.</strong> {primary_attention}</p>"
    if extra_attention and extra_attention != primary_attention:
        html += f"<p style='margin:0 0 10px'><strong>Outro sinal do dia.</strong> {extra_attention}</p>"
    html += f"<p style='margin:0 0 10px'><strong>Próximo ajuste.</strong> {primary_action}</p>"
    if extra_action and extra_action != primary_action:
        html += f"<p style='margin:0'><strong>Dica prática.</strong> {extra_action}</p>"
    html += '</div></div>'
    return html


# ==================================================
# OPENAI HELPER
# ==================================================
def ask_openai(system_text, user_text, max_tokens=350):
    if ai is None:
        return "A chave da OpenAI não está configurada."
    try:
        response = ai.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text},
            ],
            max_output_tokens=max_tokens,
        )
        text = getattr(response, "output_text", None)
        if text:
            return text
    except Exception:
        pass
    try:
        response = ai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text},
            ],
            max_completion_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao gerar análise: {e}"


# ==================================================
# UI HELPERS
# ==================================================
def macro_pills(kcal, prot, carb, fat):
    st.markdown(
        f"""
        <div class="kpi-row">
            <div class="kpi"><div class="l">kcal</div><div class="v">{kcal:.0f}</div></div>
            <div class="kpi"><div class="l">prot</div><div class="v">{prot:.0f}g</div></div>
            <div class="kpi"><div class="l">carb</div><div class="v">{carb:.0f}g</div></div>
            <div class="kpi"><div class="l">gord</div><div class="v">{fat:.0f}g</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )




def render_strategy_current(goals, current_weight=None):
    t = target_snapshot(goals)
    long_goal = t["weight_long"]
    interim_goal = t["weight_goal"]
    kcal = t["kcal"]
    protein = t["protein"]
    carb = t["carb"]
    fat = t["fat"]
    water_ml = t["water_ml"]

    left = '<div class="strategy-card">'
    left += '<div class="strategy-kicker">Estratégia atual</div>'
    left += f'<div class="strategy-title">{STRATEGY_TEXT["title"]}</div>'
    left += f'<div class="strategy-copy">{STRATEGY_TEXT["copy"]}</div>'
    left += '<div class="tag-row">'
    left += '<div class="tag">Meta 2026: sair dos 3 dígitos</div>'
    left += '<div class="tag">Foco: preservar massa magra</div>'
    left += '<div class="tag">Evitar perda caótica e flacidez piorada</div>'
    left += '</div></div>'

    right = '<div class="strategy-card">'
    right += '<div class="strategy-kicker">Metas oficiais da fase</div>'
    right += '<div class="target-grid">'
    right += f'<div class="target-card"><div class="target-label">Calorias</div><div class="target-value">{kcal:.0f}</div><div class="target-sub">Faixa boa 2250–2500</div></div>'
    right += f'<div class="target-card"><div class="target-label">Proteína</div><div class="target-value">{protein:.0f} g</div><div class="target-sub">Faixa boa 180–210 g</div></div>'
    right += f'<div class="target-card"><div class="target-label">Carbo</div><div class="target-value">{carb:.0f} g</div><div class="target-sub">Faixa base 160–220 g</div></div>'
    right += f'<div class="target-card"><div class="target-label">Gordura</div><div class="target-value">{fat:.0f} g</div><div class="target-sub">Faixa base 60–80 g</div></div>'
    right += '</div>'
    if current_weight is not None:
        right += f'<div class="strategy-copy">Peso atual {current_weight:.1f} kg · Meta intermediária {interim_goal:.1f} kg · Meta longa {long_goal:.1f} kg.</div>'
    else:
        right += f'<div class="strategy-copy">Meta intermediária {interim_goal:.1f} kg · Meta longa {long_goal:.1f} kg.</div>'
    right += '</div>'

    st.markdown(f'<div class="strategy-grid">{left}{right}</div>', unsafe_allow_html=True)


def render_hydration_card(dt_iso, hydration, goals):
    water_goal = float(goals.get("water_daily_ml", {}).get("target_value", 4000))
    current = float(hydration.get("water_ml") or 0)
    pct = 0 if water_goal <= 0 else min(100, (current / water_goal) * 100)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown('<div class="section-title">Água do dia</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'**{current/1000:.1f} L** registrados · meta **{water_goal/1000:.1f} L**')
        st.markdown(f'<div class="progress-bar"><div class="progress-fill" style="width:{pct:.1f}%"></div></div>', unsafe_allow_html=True)
        st.caption("Água entra como meta formal porque melhora leitura do dia, treino, saciedade e consistência.")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        wv = st.number_input("Água total do dia (ml)", 0, 10000, int(current), 250, key=f"water_{dt_iso}")
        r1, r2 = st.columns(2)
        if r1.button("+300 ml", key=f"w300_{dt_iso}", use_container_width=True):
            save_hydration(dt_iso, int(current + 300))
            st.rerun()
        if r2.button("+500 ml", key=f"w500_{dt_iso}", use_container_width=True):
            save_hydration(dt_iso, int(current + 500))
            st.rerun()
        if st.button("Salvar água", key=f"save_water_{dt_iso}", use_container_width=True):
            ok, msg = save_hydration(dt_iso, int(wv))
            if ok:
                st.success("Água salva.")
                st.rerun()
            else:
                st.warning("A tabela de água ainda não existe no banco. Rode o SQL abaixo no Supabase.")
                st.code("""create table if not exists public.hydration_daily (
  date date primary key,
  water_ml integer
);""")


def render_day_summary_band(current_weight, goal_weight, meals, checklist, sleep, workout):
    routine_items = [i for i in get_checklist_items() if is_routine_item(i)]
    done_count = sum(1 for i in routine_items if checklist.get(i["item_key"], {}).get("done"))
    routine_text = f"{done_count}/{len(routine_items)} rotina" if routine_items else "rotina sem base"
    trained = bool(checklist.get("treino", {}).get("done")) or bool((workout or {}).get("workout_type"))
    treino_text = "treino feito" if trained else "sem treino"
    sleep_hours = sleep.get("total_hours") if sleep else None
    sleep_text = f"{float(sleep_hours):.1f}h sono" if sleep_hours else "sono pendente"
    meal_text = f"{len(meals)} registros" if meals else "sem refeições"
    remaining = None if current_weight is None else current_weight - goal_weight

    left = '<div class="hero-card">'
    left += '<div class="hero-kicker">Hoje</div>'
    if current_weight is not None:
        left += f'<div class="hero-main">{current_weight:.1f} kg</div>'
        left += f'<div class="hero-sub">Meta {goal_weight:.0f} kg · faltam {remaining:.1f} kg para a meta cadastrada.</div>'
    else:
        left += '<div class="hero-main">Sem peso</div>'
        left += '<div class="hero-sub">Registre o peso para manter o histórico e o gráfico consistentes.</div>'
    left += '<div class="summary-chip-row">'
    for label in [routine_text, meal_text, sleep_text, treino_text]:
        left += f'<div class="summary-chip">{label}</div>'
    left += '</div></div>'

    if meals:
        totals = meal_totals(meals)
        right = '<div class="stack-card">'
        right += '<div class="stack-title">Leitura rápida do dia</div>'
        right += f'<div class="stack-value">{totals["kcal"]:.0f} kcal</div>'
        right += f'<div class="stack-sub">Proteína {totals["prot"]:.0f} g · Carbo {totals["carb"]:.0f} g · Gordura {totals["fat"]:.0f} g.</div>'
        right += '</div>'
    else:
        right = '<div class="stack-card">'
        right += '<div class="stack-title">Leitura rápida do dia</div>'
        right += '<div class="stack-value">abrir o dia</div>'
        right += '<div class="stack-sub">Comece por peso, sono e a primeira refeição para o app conseguir ler melhor o contexto.</div>'
        right += '</div>'

    st.markdown(f'<div class="hero-grid">{left}{right}</div>', unsafe_allow_html=True)


def render_period_cards():
    summaries = [period_summary(7), period_summary(15), period_summary(30)]
    cards = []
    for s in summaries:
        delta_txt = 'sem peso' if s['first_weight'] is None or s['last_weight'] is None else f"{s['first_weight']:.1f} → {s['last_weight']:.1f} kg"
        card = '<div class="period-card">'
        card += f'<div class="top">Últimos {s["days"]} dias</div>'
        card += f'<div class="big">{s["avg_routine_adherence"]:.0f}%</div>'
        card += '<div class="small">Rotina média</div>'
        card += f'<div class="small">Treino em {s["treino_days"]}/{s["days"]} dias</div>'
        card += f'<div class="small">Sono em {s["sleep_days"]}/{s["days"]} dias</div>'
        card += f'<div class="small">{delta_txt}</div>'
        card += '</div>'
        cards.append(card)
    st.markdown('<div class="period-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)


def date_bar():
    today = local_today()
    d = st.session_state.sel_date
    c1, c2, c3, c4 = st.columns([1, 1.2, 3.6, 1])
    with c1:
        if st.button("◀", key=f"prev_{st.session_state.page}", use_container_width=True):
            st.session_state.sel_date = d - timedelta(days=1)
            st.rerun()
    with c2:
        if st.button("Hoje", key=f"today_{st.session_state.page}", use_container_width=True, type="secondary"):
            st.session_state.sel_date = today
            st.rerun()
    with c3:
        new_d = st.date_input("Data", value=d, label_visibility="collapsed", key=f"date_{st.session_state.page}")
        if new_d != d:
            st.session_state.sel_date = new_d
            st.rerun()
    with c4:
        next_disabled = d >= today + timedelta(days=30)
        if st.button("▶", key=f"next_{st.session_state.page}", use_container_width=True, disabled=next_disabled):
            st.session_state.sel_date = d + timedelta(days=1)
            st.rerun()
    subtitle = "Você pode voltar e preencher qualquer dia retroativamente."
    st.markdown(f'<div class="top-date"><div class="main">{format_date_label(d)}</div><div class="sub">{subtitle}</div></div>', unsafe_allow_html=True)
    return d.isoformat()


def nav_bar():
    st.markdown("<div class='nav-caption'>Navegação principal</div>", unsafe_allow_html=True)
    cols = st.columns(5)
    items = [
        ("hoje", "Hoje"),
        ("alimentacao", "Alimentação"),
        ("corpo", "Corpo & Sono"),
        ("historico", "Histórico"),
        ("ia", "IA"),
    ]
    for i, (key, label) in enumerate(items):
        with cols[i]:
            active = st.session_state.page == key
            if st.button(label, key=f"nav_{key}", use_container_width=True, type="primary" if active else "secondary"):
                st.session_state.page = key
                st.rerun()



def render_graph(end_date, goal_weight):
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)

    project_start = PROJECT_PROFILE["start_date"]
    if end_date < project_start:
        project_start = end_date

    total_days = max(1, (end_date - project_start).days + 1)
    hist = get_weight_history(total_days, end_date=end_date)

    df = pd.DataFrame({"date": pd.date_range(start=project_start, end=end_date, freq="D")})
    df["curva_min"] = df["date"].apply(lambda d: get_projected_weight(d.date(), PROJECT_PROFILE["expected_loss_per_week_min"]))
    df["curva_ideal"] = df["date"].apply(lambda d: get_projected_weight(d.date(), PROJECT_PROFILE["expected_loss_per_week_ideal"]))

    if hist:
        hist_df = pd.DataFrame(hist)
        hist_df["date"] = pd.to_datetime(hist_df["date"])
        hist_df["weight_kg"] = hist_df["weight_kg"].astype(float)
        hist_df = hist_df.groupby("date", as_index=False)["weight_kg"].last()
        df = df.merge(hist_df.rename(columns={"weight_kg": "peso_real"}), on="date", how="left")
    else:
        df["peso_real"] = float("nan")

    plot_df = df.set_index("date")[["peso_real", "curva_ideal", "curva_min"]]
    st.line_chart(plot_df, height=260, use_container_width=True)

    monthly_targets = get_monthly_target_rows(end_date)
    current_real = df["peso_real"].dropna()
    if not current_real.empty:
        last_real = float(current_real.iloc[-1])
        curve_info = get_weight_curve_status(last_real, end_date)
        st.caption(
            f"Peso inicial {PROJECT_PROFILE['start_weight']:.1f} kg · peso atual {last_real:.1f} kg · "
            f"curva ideal hoje {curve_info['projected_ideal']:.1f} kg · status: {curve_info['label']}."
        )
    else:
        st.caption(
            f"Peso inicial {PROJECT_PROFILE['start_weight']:.1f} kg · sem linha real suficiente ainda."
        )

    if monthly_targets:
        st.markdown("**Metas mensais da curva ideal**")
        cols = st.columns(min(4, len(monthly_targets)))
        for idx, row in enumerate(monthly_targets[:4]):
            cols[idx].metric(row["month_label"], f"{row['target_weight']:.1f} kg")

# ==================================================
# PAGE: HOJE
# ==================================================
def page_hoje():
    target = date_bar()
    target_date = st.session_state.sel_date
    goals = get_goals()
    goal_weight = float(PROJECT_PROFILE["goal_weight_intermediate"])
    current_weight = get_weight(target)
    display_weight = current_weight if current_weight is not None else get_last_known_weight(target)
    curve_info = get_weight_curve_status(current_weight, target_date)
    sleep = get_sleep(target)
    workout = get_workout(target)
    hydration = get_hydration(target)
    checklist = get_checklist(target)
    meals = get_meals(target)
    closure = get_daily_closure(target)

    st.markdown('<div class="section-title">Hoje</div>', unsafe_allow_html=True)
    render_day_summary_band(display_weight, goal_weight, meals, checklist, sleep, workout)

    curve_class_map = {
        "sem_peso": "b",
        "claramente_atrasado": "r",
        "queda_rapida_demais": "y",
        "na_curva_ideal": "g",
        "dentro_da_faixa": "b",
    }
    curve_class = curve_class_map.get(curve_info["status"], "b")

    st.markdown(
        f"""
        <div class="card card-tight">
            <div class="meal-name">Ritmo do peso</div>
            <div class="meal-detail">Status: <span class="status {curve_class}">{curve_info['label']}</span></div>
            <div class="meal-detail" style="margin-top:8px;">Hoje a curva ideal projeta {curve_info['projected_ideal']:.1f} kg e o mínimo aceitável projeta {curve_info['projected_min']:.1f} kg.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([2.2, 1])
    with c1:
        pv = float(display_weight or PROJECT_PROFILE["start_weight"])
        weight_input = st.number_input("Peso do dia", 50.0, 250.0, pv, 0.1, format="%.1f", key="today_weight")
    with c2:
        st.write("")
        if st.button("Salvar peso", use_container_width=True, key="save_today_weight"):
            save_weight(target, weight_input)
            st.rerun()

    st.markdown('<div class="section-title">Gráfico de ritmo</div>', unsafe_allow_html=True)
    render_graph(st.session_state.sel_date, goal_weight)

    st.markdown('<div class="section-title">Sono + CPAP</div>', unsafe_allow_html=True)
    page_sono_quick(target, sleep)

    st.markdown('<div class="section-title">Treino, água e alimentação</div>', unsafe_allow_html=True)
    left, right = st.columns([1.1, 1])
    with left:
        trained = bool(checklist.get("treino", {}).get("done")) or bool(workout.get("workout_type"))
        if trained:
            summary = []
            if workout.get("workout_type"):
                summary.append(workout["workout_type"])
            if workout.get("strength_split"):
                summary.append(workout["strength_split"])
            if workout.get("duration_min"):
                summary.append(f"{workout['duration_min']} min")
            if workout.get("distance_km"):
                summary.append(f"{float(workout['distance_km']):.1f} km")
            detail = " · ".join(summary) if summary else "Treino registrado"
            st.markdown(f'<div class="meal-card"><div class="meal-name">Treino</div><div class="meal-detail">{detail}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="meal-card"><div class="meal-name">Treino</div><div class="meal-detail">Sem treino marcado hoje.</div></div>', unsafe_allow_html=True)
        render_hydration_card(target, hydration, goals)

    with right:
        totals = meal_totals(meals)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('**Alimentação resumida**')
        macro_pills(totals["kcal"], totals["prot"], totals["carb"], totals["fat"])
        klass, label = food_status_class(totals["kcal"], totals["prot"], goals)
        if label:
            st.markdown(f'<span class="status {klass}">{label}</span>', unsafe_allow_html=True)
        if meals:
            meal_groups = []
            for mk, mc in MEAL_CONFIG.items():
                mk_items = [m for m in meals if m["meal_type"] == mk]
                if mk_items:
                    meal_groups.append(f"{mc['label']} ({sum(float(m.get('kcal') or 0) for m in mk_items):.0f} kcal)")
            st.caption(" · ".join(meal_groups))
        else:
            st.caption("Nenhuma refeição registrada ainda.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Rotina do dia</div>', unsafe_allow_html=True)
    checklist_items = [i for i in get_checklist_items() if is_routine_item(i)]
    slots = {"jejum": "☀️ Jejum", "manha": "Manhã", "almoco": "Almoço", "jantar": "Jantar", "noite": "Noite", "variavel": "Variável"}
    current_slot = None
    done_count = 0
    for item in checklist_items:
        slot = item.get("time_slot") or "variavel"
        if slot != current_slot:
            current_slot = slot
            st.markdown(f"**{slots.get(slot, slot)}**")
        checked = checklist.get(item["item_key"], {}).get("done", False)
        if checked:
            done_count += 1
        dose = f" · {item['dosage']}" if item.get("dosage") else ""
        instruction = item.get("instruction") or ""
        st.markdown('<div class="check-card">', unsafe_allow_html=True)
        new_val = st.checkbox(f"{item['name']}{dose}", value=checked, key=f"check_{target}_{item['item_key']}")
        if instruction:
            st.caption(instruction)
        st.markdown('</div>', unsafe_allow_html=True)
        if new_val != checked:
            save_check(target, item["item_key"], new_val)
            st.rerun()
    if checklist_items:
        pct = int((done_count / len(checklist_items)) * 100)
        st.caption(f"Aderência da rotina: {done_count}/{len(checklist_items)} ({pct}%)")

    st.markdown('<div class="section-title">Leitura do dia</div>', unsafe_allow_html=True)
    review_html = build_day_review(target, goals, meals, checklist, sleep, current_weight, workout=workout, hydration=hydration)
    st.markdown(review_html, unsafe_allow_html=True)

    score_data = compute_daily_score(goals, meals, checklist, sleep, workout=workout, hydration=hydration)

    st.markdown('<div class="section-title">Finalizar dia</div>', unsafe_allow_html=True)
    if st.button("Finalizar dia e gerar score", key=f"finalize_{target}", use_container_width=True):
        analysis_text = re.sub(r'<[^>]+>', ' ', review_html)
        payload = {
            "date": target,
            "score_total": score_data["total"],
            "score_label": score_data["label"],
            "score_breakdown": json.dumps(score_data["breakdown"], ensure_ascii=False),
            "analysis_text": analysis_text.strip(),
            "closed_at": datetime.now(APP_TZ).isoformat(),
        }
        ok, msg = save_daily_closure(payload)
        if ok:
            st.success("Dia finalizado.")
        else:
            st.warning("Não foi possível salvar o fechamento no banco ainda. Rode o SQL da tabela daily_closure no Supabase.")
            st.code("""create table if not exists public.daily_closure (
  date date primary key,
  score_total integer,
  score_label text,
  score_breakdown jsonb,
  analysis_text text,
  closed_at timestamptz
);""", language="sql")
        st.rerun()

    closure = get_daily_closure(target)
    if closure:
        saved_score = {
            "total": int(closure.get("score_total") or 0),
            "label": closure.get("score_label") or "dia parcial",
            "class": "g" if int(closure.get("score_total") or 0) >= 70 else "y" if int(closure.get("score_total") or 0) >= 55 else "r",
            "breakdown": json.loads(closure.get("score_breakdown") or "{}") if isinstance(closure.get("score_breakdown"), str) else (closure.get("score_breakdown") or {}),
        }
        for key in ["alimentacao", "proteina", "treino", "sono_cpap", "rotina", "agua"]:
            saved_score["breakdown"].setdefault(key, 0)
        render_score_card(saved_score)
        st.markdown('<div class="card"><div class="section-title" style="margin-top:0">Análise final salva</div><div class="muted">' + (closure.get("analysis_text") or "") + '</div></div>', unsafe_allow_html=True)
    else:
        render_score_card(score_data)

# ==================================================
# QUICK SLEEP ON TODAY
# ==================================================
def page_sono_quick(target, data):
    bed_default = parse_time_field(data.get("bed_time"), time(0, 0))
    wake_default = parse_time_field(data.get("wake_time"), time(7, 0))
    with st.expander("Preencher ou editar sono", expanded=not bool(data)):
        c1, c2 = st.columns(2)
        with c1:
            bt = st.time_input("Dormiu às", value=bed_default, key=f"quick_bed_{target}")
            use_cpap = st.checkbox("Usou CPAP?", value=bool(data.get("used_cpap", True)), key=f"quick_cpap_{target}")
            cpap_hours = st.number_input("Horas de uso do CPAP", 0.0, 16.0, float(data.get("cpap_hours") or 0.0), 0.1, key=f"quick_cpap_h_{target}")
        with c2:
            wt = st.time_input("Acordou às", value=wake_default, key=f"quick_wake_{target}")
            ahi = st.number_input("AHI", 0.0, 100.0, float(data.get("ahi") or 0.0), 0.1, key=f"quick_ahi_{target}")
            energy = st.slider("Energia hoje", 0, 10, int(data.get("energy_score") or 5), key=f"quick_energy_{target}")

        hours = compute_sleep_hours(bt, wt)
        c3, c4, c5 = st.columns(3)
        with c3:
            leak = st.number_input("Vazamento", 0.0, 100.0, float(data.get("leak_rate") or 0.0), 0.1, key=f"quick_leak_{target}")
        with c4:
            events = st.number_input("Eventos/hora", 0.0, 100.0, float(data.get("events_per_hour") or 0.0), 0.1, key=f"quick_events_{target}")
        with c5:
            tired = st.slider("Cansaço ao acordar", 0, 10, int(data.get("tiredness_score") or 5), key=f"quick_tired_{target}")

        removed = st.checkbox("Tirou a máscara?", value=bool(data.get("removed_mask", False)), key=f"quick_removed_{target}")
        seal_opts = ["boa", "regular", "ruim"]
        seal_index = seal_opts.index(data.get("mask_seal") or "boa") if (data.get("mask_seal") or "boa") in seal_opts else 0
        seal = st.selectbox("Vedação da máscara", seal_opts, index=seal_index, key=f"quick_seal_{target}")
        notes = st.text_area("Observações", value=data.get("notes") or "", height=70, key=f"quick_notes_{target}")
        if hours is not None:
            st.info(f"Horas totais calculadas automaticamente: **{hours:.2f} h**")

        if st.button("Salvar sono", key=f"save_sleep_{target}", use_container_width=True):
            db.table("sleep_cpap").upsert(
                {
                    "date": target,
                    "bed_time": bt.isoformat() if bt else None,
                    "wake_time": wt.isoformat() if wt else None,
                    "total_hours": hours,
                    "used_cpap": use_cpap,
                    "cpap_hours": cpap_hours,
                    "ahi": ahi,
                    "leak_rate": leak,
                    "mask_seal": seal,
                    "removed_mask": removed,
                    "events_per_hour": events,
                    "tiredness_score": tired,
                    "energy_score": energy,
                    "notes": notes,
                },
                on_conflict="date",
            ).execute()
            st.success("Sono salvo.")
            st.rerun()

    if data:
        total_hours = data.get("total_hours")
        ahi = data.get("ahi")
        energy = data.get("energy_score")
        cpap_hours = data.get("cpap_hours")
        st.markdown(
            f'<div class="card card-tight"><div class="muted">{(f"{float(total_hours):.2f}h" if total_hours else "—")} de sono · AHI {ahi if ahi is not None else "—"} · Energia {energy if energy is not None else "—"}/10 · CPAP {(f"{float(cpap_hours):.1f}h" if cpap_hours else "—")}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="card card-tight"><div class="muted">Sem registro de sono para essa data.</div></div>', unsafe_allow_html=True)


# ==================================================
# PAGE: ALIMENTAÇÃO
# ==================================================
def page_alimentacao():
    target = date_bar()
    st.markdown('<div class="section-title">Alimentação por refeição</div>', unsafe_allow_html=True)
    goals = get_goals()
    render_strategy_current(goals)
    foods = get_foods()
    food_map = {f["food_key"]: f for f in foods}
    all_meals = get_meals(target)
    totals = meal_totals(all_meals)
    macro_pills(totals["kcal"], totals["prot"], totals["carb"], totals["fat"])
    klass, label = food_status_class(totals["kcal"], totals["prot"], goals)
    if label:
        st.markdown(f'<span class="status {klass}">{label}</span>', unsafe_allow_html=True)

    for meal_key, cfg in MEAL_CONFIG.items():
        meal_items = [m for m in all_meals if m["meal_type"] == meal_key]
        subtotal = sum(float(m.get("kcal") or 0) for m in meal_items)
        subtitle = f" · {subtotal:.0f} kcal" if meal_items else ""
        with st.expander(f"{cfg['label']}{subtitle}", expanded=meal_key in ["cafe", "almoco"]):
            if meal_items:
                for item in meal_items:
                    name = food_map.get(item["food_key"], {}).get("name", item["food_key"])
                    st.markdown(
                        f'<div class="meal-card"><div class="meal-name">{name}</div><div class="meal-detail">{float(item.get("quantity_g") or 0):.0f} g · {float(item.get("kcal") or 0):.0f} kcal · P {float(item.get("protein_g") or 0):.0f}g · C {float(item.get("carbs_g") or 0):.0f}g · G {float(item.get("fat_g") or 0):.0f}g</div></div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(f"Apagar {name}", key=f"del_{item['id']}", use_container_width=True):
                        db.table("meals").delete().eq("id", item["id"]).execute()
                        st.rerun()
            else:
                st.caption("Nada lançado nessa refeição ainda.")

            show_all = st.checkbox("Mostrar todos os alimentos", value=False, key=f"showall_{meal_key}_{target}")
            options = meal_context_options(meal_key, foods, show_all=show_all)
            if not options:
                st.info("Nenhum alimento disponível nessa categoria.")
                continue
            labels = [f["name"] for f in options]
            selected_label = st.selectbox("Escolha o item", [""] + labels, key=f"sel_{meal_key}_{target}")
            if selected_label:
                selected = next(f for f in options if f["name"] == selected_label)
                default_g = float(selected.get("default_portion_g") or 100)
                qty = st.number_input(
                    f"Quantidade em gramas · porção padrão {default_g:.0f} g",
                    1.0,
                    5000.0,
                    default_g,
                    5.0,
                    key=f"qty_{meal_key}_{target}",
                )
                factor = qty / 100
                kcal = float(selected.get("kcal_per_100g") or 0) * factor
                prot = float(selected.get("protein_per_100g") or 0) * factor
                carb = float(selected.get("carbs_per_100g") or 0) * factor
                fat = float(selected.get("fat_per_100g") or 0) * factor
                st.caption(f"Estimativa: {kcal:.0f} kcal · P {prot:.0f}g · C {carb:.0f}g · G {fat:.0f}g")
                if st.button("Adicionar item", key=f"add_{meal_key}_{target}", use_container_width=True):
                    db.table("meals").insert(
                        {
                            "date": target,
                            "meal_type": meal_key,
                            "food_key": selected["food_key"],
                            "quantity_g": qty,
                            "portions": qty / default_g if default_g else 1,
                            "kcal": kcal,
                            "protein_g": prot,
                            "carbs_g": carb,
                            "fat_g": fat,
                        }
                    ).execute()
                    st.success("Item adicionado.")
                    st.rerun()

            st.markdown('<div class="food-search-box">', unsafe_allow_html=True)
            st.markdown("**Item que não está na base**")
            custom_desc = st.text_input("Descreva o item real que você comeu", key=f"custom_desc_{meal_key}_{target}", placeholder="Ex.: Big Mac + metade da batata / marmita de churrasco / miojo / combo do aeroporto")
            custom_portion = st.number_input("Porção estimada (g ou ml)", 1.0, 5000.0, 150.0, 10.0, key=f"custom_portion_{meal_key}_{target}")
            estimate_key = f"custom_estimate_{meal_key}_{target}"
            if st.button("Estimar com IA", key=f"estimate_{meal_key}_{target}", use_container_width=True):
                if not custom_desc.strip():
                    st.warning("Descreva o item antes de estimar.")
                else:
                    with st.spinner("Estimando macros e calorias..."):
                        st.session_state[estimate_key] = estimate_custom_food(custom_desc.strip(), custom_portion)
                        st.rerun()
            est = st.session_state.get(estimate_key)
            if est:
                if est.get("error"):
                    st.error(est["error"])
                else:
                    st.markdown('<div class="custom-estimate">', unsafe_allow_html=True)
                    st.markdown(f"**{est.get('name') or custom_desc}** · {float(est.get('portion_g') or custom_portion):.0f} g/ml")
                    st.markdown(f"{float(est.get('kcal') or 0):.0f} kcal · P {float(est.get('protein_g') or 0):.1f} g · C {float(est.get('carbs_g') or 0):.1f} g · G {float(est.get('fat_g') or 0):.1f} g")
                    if est.get("rationale"):
                        st.caption(est.get("rationale"))
                    if st.button("Salvar item customizado", key=f"save_custom_{meal_key}_{target}", use_container_width=True):
                        custom_key = f"custom_{slugify_text(est.get('name') or custom_desc)}"
                        db.table("meals").insert(
                            {
                                "date": target,
                                "meal_type": meal_key,
                                "food_key": custom_key,
                                "quantity_g": float(est.get("portion_g") or custom_portion),
                                "portions": 1,
                                "kcal": float(est.get("kcal") or 0),
                                "protein_g": float(est.get("protein_g") or 0),
                                "carbs_g": float(est.get("carbs_g") or 0),
                                "fat_g": float(est.get("fat_g") or 0),
                            }
                        ).execute()
                        st.success("Item customizado salvo na refeição.")
                        st.session_state.pop(estimate_key, None)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ==================================================
# PAGE: CORPO & SONO
# ==================================================
def page_corpo():
    target = date_bar()
    tab = st.radio("", ["😴 Sono / CPAP", "⚖️ Peso e medidas", "🏋️ Treino", "🔬 Bio / Exames"], horizontal=True, label_visibility="collapsed")
    if tab == "😴 Sono / CPAP":
        page_sono_inner(target)
    elif tab == "⚖️ Peso e medidas":
        page_peso_inner(target)
    elif tab == "🏋️ Treino":
        page_treino_inner(target)
    else:
        page_bio_inner(target)


def page_sono_inner(target):
    st.markdown('<div class="section-title">Sono / CPAP</div>', unsafe_allow_html=True)
    data = get_sleep(target)
    page_sono_quick(target, data)


def page_peso_inner(target):
    st.markdown('<div class="section-title">Peso e medidas</div>', unsafe_allow_html=True)
    goals = get_goals()
    goal_weight = float(goals.get("weight", {}).get("target_value", 90))
    period = st.selectbox("Período do gráfico", ["30 dias", "60 dias", "90 dias", "Tudo"], key="weight_period")
    days_map = {"30 dias": 30, "60 dias": 60, "90 dias": 90, "Tudo": 3650}
    hist = get_weight_history(days_map[period], end_date=st.session_state.sel_date)
    if hist:
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"])
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["meta"] = goal_weight
        df["media_7d"] = df["weight_kg"].rolling(7, min_periods=1).mean()
        st.line_chart(df.set_index("date")[["weight_kg", "meta", "media_7d"]], height=260, use_container_width=True)

    with st.expander("Registrar peso", expanded=True):
        dt = st.date_input("Data do peso", value=st.session_state.sel_date, key="weight_date")
        current = get_weight(dt.isoformat())
        p = st.number_input("Peso em kg", 50.0, 250.0, float(current or 143.0), 0.1, key="weight_value")
        if st.button("Salvar peso", key="save_weight_inner", use_container_width=True):
            save_weight(dt.isoformat(), p)
            st.success("Peso salvo.")
            st.rerun()

    with st.expander("Registrar medidas"):
        md = st.date_input("Data das medidas", value=st.session_state.sel_date, key="measure_date")
        c1, c2 = st.columns(2)
        with c1:
            waist = st.number_input("Cintura", 0.0, 250.0, 0.0, 0.5, key="m_waist")
            abdomen = st.number_input("Abdômen", 0.0, 250.0, 0.0, 0.5, key="m_abd")
            chest = st.number_input("Peito", 0.0, 250.0, 0.0, 0.5, key="m_chest")
        with c2:
            arm = st.number_input("Braço", 0.0, 100.0, 0.0, 0.5, key="m_arm")
            thigh = st.number_input("Coxa", 0.0, 150.0, 0.0, 0.5, key="m_thigh")
            hip = st.number_input("Quadril", 0.0, 250.0, 0.0, 0.5, key="m_hip")
        if st.button("Salvar medidas", key="save_measurements", use_container_width=True):
            db.table("measurements").insert(
                {
                    "date": md.isoformat(),
                    "waist_cm": waist or None,
                    "abdomen_cm": abdomen or None,
                    "chest_cm": chest or None,
                    "arm_cm": arm or None,
                    "thigh_cm": thigh or None,
                    "hip_cm": hip or None,
                }
            ).execute()
            st.success("Medidas salvas.")

    if hist:
        st.markdown("**Últimos pesos registrados**")
        for item in reversed(hist[-7:]):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.caption(f"{item['date']} · {item['weight_kg']} kg")
            with c2:
                if st.button("Apagar", key=f"delete_weight_{item['date']}"):
                    db.table("daily_weight").delete().eq("date", item["date"]).execute()
                    st.rerun()


def page_treino_inner(target):
    st.markdown('<div class="section-title">Treino</div>', unsafe_allow_html=True)
    ck = get_checklist(target)
    treino_done = ck.get("treino", {}).get("done", False)
    workout = get_workout(target)

    trained = st.checkbox("Treinei hoje", value=treino_done, key=f"trained_{target}")
    if trained != treino_done:
        save_check(target, "treino", trained)
        st.rerun()

    if not trained:
        st.caption("Sem treino marcado nessa data. Se quiser, marque quando treinar ou planeje o próximo.")
        st.markdown('<div class="meal-card"><div class="meal-name">Sugestão útil</div><div class="meal-detail">Mesmo sem musculação, registrar 20–30 minutos de caminhada já melhora consistência e leitura do período.</div></div>', unsafe_allow_html=True)
        return

    workout_type_options = ["Musculação", "Caminhada", "Corrida", "Bike", "Escada / cardio", "Mobilidade / alongamento", "Outro"]
    split_options = ["Superior", "Inferior", "Push", "Pull", "Full body", "Outro"]
    default_type = workout.get("workout_type") if workout.get("workout_type") in workout_type_options else "Musculação"
    workout_type = st.selectbox("Tipo de treino", workout_type_options, index=workout_type_options.index(default_type), key=f"wtype_{target}")

    c1, c2 = st.columns(2)
    with c1:
        duration = st.number_input("Duração total (min)", 0, 300, int(workout.get("duration_min") or 0), 5, key=f"wdur_{target}")
        intensity = st.slider("Intensidade percebida", 1, 10, int(workout.get("intensity") or 6), key=f"wint_{target}")
    with c2:
        distance = st.number_input("Distância (km, se fizer sentido)", 0.0, 100.0, float(workout.get("distance_km") or 0.0), 0.1, key=f"wdist_{target}")
        calories = st.number_input("Calorias do aparelho / relógio (opcional)", 0, 5000, int(workout.get("device_kcal") or 0), 10, key=f"wkcal_{target}")

    split = None
    if workout_type == "Musculação":
        default_split = workout.get("strength_split") if workout.get("strength_split") in split_options else "Superior"
        split = st.selectbox("Divisão do treino", split_options, index=split_options.index(default_split), key=f"wsplit_{target}")

    notes = st.text_area("Observações do treino", value=workout.get("notes") or "", height=90, key=f"wnotes_{target}", placeholder="Ex.: superior, 45 min de musculação; 25 min de caminhada; corrida leve 5 km...")

    if st.button("Salvar detalhes do treino", key=f"save_workout_{target}", use_container_width=True):
        ok, msg = save_workout(
            target,
            {
                "workout_type": workout_type,
                "strength_split": split,
                "duration_min": duration or None,
                "distance_km": distance or None,
                "device_kcal": calories or None,
                "intensity": intensity,
                "notes": notes or None,
            },
        )
        if ok:
            st.success("Detalhes do treino salvos.")
            st.rerun()
        else:
            st.warning("Os detalhes do treino precisam de uma tabela específica no Supabase. O treino como feito/não feito continua funcionando.")
            st.code("""create table if not exists public.workout_logs (
  date date primary key,
  workout_type text,
  strength_split text,
  duration_min integer,
  distance_km numeric,
  device_kcal integer,
  intensity integer,
  notes text
);""", language="sql")

    if workout:
        summary = [workout.get("workout_type") or "Treino"]
        if workout.get("strength_split"):
            summary.append(workout["strength_split"])
        if workout.get("duration_min"):
            summary.append(f"{workout['duration_min']} min")
        if workout.get("distance_km"):
            summary.append(f"{float(workout['distance_km']):.1f} km")
        st.markdown(f'<div class="meal-card"><div class="meal-name">Treino registrado</div><div class="meal-detail">{" · ".join(summary)}</div></div>', unsafe_allow_html=True)


def page_bio_inner(target):
    st.markdown('<div class="section-title">Bioimpedância e exames</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Bioimpedância", "Exames"])
    with tab1:
        with st.expander("Nova bioimpedância"):
            with st.form("bio_form"):
                dt = st.date_input("Data", key="bio_date")
                c1, c2 = st.columns(2)
                with c1:
                    weight = st.number_input("Peso (kg)", 50.0, 250.0, 143.0, 0.1)
                    fat_pct = st.number_input("% gordura", 0.0, 80.0, 50.0, 0.1)
                    visceral = st.number_input("Gordura visceral", 0, 60, 31)
                with c2:
                    muscle = st.number_input("Massa muscular esquelética (kg)", 0.0, 100.0, 39.0, 0.1)
                    lean = st.number_input("Massa livre de gordura (kg)", 0.0, 150.0, 64.0, 0.1)
                    bmr = st.number_input("TMB (kcal)", 0.0, 5000.0, 2681.0, 1.0)
                note = st.text_area("Observação", height=60)
                if st.form_submit_button("Salvar bioimpedância"):
                    db.table("bioimpedance").insert(
                        {
                            "date": dt.isoformat(),
                            "weight_kg": weight,
                            "fat_pct": fat_pct,
                            "visceral_fat": visceral,
                            "skeletal_muscle_kg": muscle,
                            "fat_free_mass_kg": lean,
                            "bmr_kcal": bmr,
                            "notes": note,
                        }
                    ).execute()
                    st.success("Bio salva.")
        bios = db.table("bioimpedance").select("*").order("date", desc=True).limit(5).execute().data or []
        for b in bios:
            st.markdown(f'<div class="card card-tight"><div class="muted">📅 {b["date"]} · {b["weight_kg"]} kg · Gord {b["fat_pct"]}% · Visc {b["visceral_fat"]} · Musc {b["skeletal_muscle_kg"]} kg</div></div>', unsafe_allow_html=True)

    with tab2:
        with st.expander("Novos exames"):
            with st.form("labs_form"):
                dt = st.date_input("Data", key="lab_date")
                c1, c2, c3 = st.columns(3)
                with c1:
                    glucose = st.number_input("Glicose", 0.0, 500.0, 0.0, 1.0)
                    hba1c = st.number_input("HbA1c", 0.0, 15.0, 0.0, 0.1)
                    insulin = st.number_input("Insulina", 0.0, 100.0, 0.0, 0.1)
                    homa = st.number_input("HOMA-IR", 0.0, 20.0, 0.0, 0.01)
                    tsh = st.number_input("TSH", 0.0, 50.0, 0.0, 0.01)
                with c2:
                    t4 = st.number_input("T4 livre", 0.0, 10.0, 0.0, 0.01)
                    trig = st.number_input("Triglicérides", 0.0, 1000.0, 0.0, 1.0)
                    ggt = st.number_input("GGT", 0.0, 500.0, 0.0, 1.0)
                    total_chol = st.number_input("Colesterol total", 0.0, 500.0, 0.0, 1.0)
                    ldl = st.number_input("LDL", 0.0, 300.0, 0.0, 1.0)
                with c3:
                    hdl = st.number_input("HDL", 0.0, 150.0, 0.0, 1.0)
                    magnesium = st.number_input("Magnésio", 0.0, 10.0, 0.0, 0.1)
                    b12 = st.number_input("B12", 0.0, 2000.0, 0.0, 1.0)
                    vitamin_d = st.number_input("Vitamina D", 0.0, 150.0, 0.0, 0.1)
                    testo = st.number_input("Testosterona", 0.0, 1500.0, 0.0, 1.0)
                note = st.text_area("Observação", height=60)
                if st.form_submit_button("Salvar exames"):
                    db.table("lab_results").insert(
                        {
                            "date": dt.isoformat(),
                            "glucose": glucose or None,
                            "hba1c": hba1c or None,
                            "insulin": insulin or None,
                            "homa_ir": homa or None,
                            "tsh": tsh or None,
                            "t4_free": t4 or None,
                            "triglycerides": trig or None,
                            "ggt": ggt or None,
                            "total_cholesterol": total_chol or None,
                            "ldl": ldl or None,
                            "hdl": hdl or None,
                            "magnesium": magnesium or None,
                            "b12": b12 or None,
                            "vitamin_d": vitamin_d or None,
                            "testosterone": testo or None,
                            "notes": note,
                        }
                    ).execute()
                    st.success("Exames salvos.")
        labs = db.table("lab_results").select("*").order("date", desc=True).limit(3).execute().data or []
        for l in labs:
            parts = []
            if l.get("glucose"):
                parts.append(f"Glic {l['glucose']}")
            if l.get("hba1c"):
                parts.append(f"HbA1c {l['hba1c']}")
            if l.get("tsh"):
                parts.append(f"TSH {l['tsh']}")
            if l.get("triglycerides"):
                parts.append(f"Trig {l['triglycerides']}")
            st.markdown(f'<div class="card card-tight"><div class="muted">📅 {l["date"]} · ' + " · ".join(parts) + '</div></div>', unsafe_allow_html=True)


# ==================================================
# PAGE: HISTÓRICO
# ==================================================
def page_historico():
    st.markdown('<div class="section-title">Histórico / calendário</div>', unsafe_allow_html=True)
    st.markdown('<div class="card card-tight"><strong>Leitura rápida do histórico</strong><div class="muted">Aqui você enxerga consistência recente e pode abrir qualquer dia para corrigir ou preencher retroativamente.</div></div>', unsafe_allow_html=True)
    render_period_cards()

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Abrir análise 7 dias", use_container_width=True, key="hist_go_7"):
            st.session_state["analysis_days"] = 7
            st.session_state.page = "ia"
            st.rerun()
    with c2:
        if st.button("Abrir análise 15 dias", use_container_width=True, key="hist_go_15"):
            st.session_state["analysis_days"] = 15
            st.session_state.page = "ia"
            st.rerun()
    with c3:
        if st.button("Abrir análise 30 dias", use_container_width=True, key="hist_go_30"):
            st.session_state["analysis_days"] = 30
            st.session_state.page = "ia"
            st.rerun()

    st.markdown('<div class="legend-wrap"><div class="legend-badge">🟢 dia bem preenchido</div><div class="legend-badge">🟡 dia parcial</div><div class="legend-badge">🔴 quase vazio</div><div class="legend-badge">⚫ sem registro</div></div>', unsafe_allow_html=True)

    today = local_today()
    months = []
    base = today.replace(day=1)
    for i in range(6):
        month_ref = (base - timedelta(days=32 * i)).replace(day=1)
        months.append(month_ref)
    labels = [m.strftime("%B %Y") for m in months]
    idx = st.selectbox("Mês", range(len(months)), format_func=lambda i: labels[i], key="hist_month")
    selected_month = months[idx]
    cal = calendar.monthcalendar(selected_month.year, selected_month.month)

    cols = st.columns(7)
    for col, lbl in zip(cols, ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]):
        col.markdown(f"<div class='small-label' style='text-align:center'>{lbl}</div>", unsafe_allow_html=True)
    for week in cal:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            with cols[i]:
                if not day_num:
                    st.write("")
                    continue
                d = date(selected_month.year, selected_month.month, day_num)
                if d > today:
                    st.write(day_num)
                    continue
                status = day_completeness(d.isoformat())
                emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚫"}[status]
                if st.button(f"{emoji} {day_num}", key=f"hist_{d.isoformat()}", use_container_width=True):
                    st.session_state.sel_date = d
                    st.session_state.page = "hoje"
                    st.rerun()
    st.markdown("<div class='calendar-note'>Clique em um dia para abrir, completar ou corrigir retroativamente. O histórico foi pensado para não te punir se você esquecer de preencher no dia.</div>", unsafe_allow_html=True)


# ==================================================
# PAGE: IA
# ==================================================
def build_context(days=14):
    end_d = st.session_state.sel_date
    start = (end_d - timedelta(days=days - 1)).isoformat()
    end_s = end_d.isoformat()
    weights = get_weight_history(days, end_date=end_d)
    meals = db.table("meals").select("date,meal_type,food_key,kcal,protein_g,carbs_g,fat_g").gte("date", start).lte("date", end_s).order("date").execute().data or []
    sleep = db.table("sleep_cpap").select("date,total_hours,ahi,energy_score,tiredness_score").gte("date", start).lte("date", end_s).order("date").execute().data or []
    checks = db.table("checklist_daily").select("date,item_key,done").gte("date", start).lte("date", end_s).order("date").execute().data or []
    try:
        hydration = db.table("hydration_daily").select("date,water_ml").gte("date", start).lte("date", end_s).order("date").execute().data or []
    except Exception:
        hydration = []
    try:
        workouts = db.table("workout_logs").select("*").gte("date", start).lte("date", end_s).order("date").execute().data or []
    except Exception:
        workouts = []
    bio = db.table("bioimpedance").select("*").order("date", desc=True).limit(1).execute().data or []
    labs = db.table("lab_results").select("*").order("date", desc=True).limit(1).execute().data or []
    summary = period_summary(days)
    return f"""
Contexto do usuário:
- Homem, 34 anos, 174 cm.
- Objetivo: emagrecer preservando massa magra.
- Janela analisada: {start} até {end_s}.
- Resumo determinístico do período: {json.dumps(summary, default=str)}

Peso: {json.dumps(weights, default=str)}
Refeições: {json.dumps(meals, default=str)}
Sono: {json.dumps(sleep, default=str)}
Checklist: {json.dumps(checks, default=str)}
Treinos detalhados: {json.dumps(workouts, default=str)}
Água: {json.dumps(hydration, default=str)}
Bio mais recente: {json.dumps(bio, default=str)}
Exames mais recentes: {json.dumps(labs, default=str)}
"""


def page_ia():
    st.markdown('<div class="section-title">IA / perguntas</div>', unsafe_allow_html=True)
    st.caption("Aqui a IA faz mais sentido para analisar consistência, aderência de treino, água, sono, alimentação e tendência do período com foco em perder gordura sem desmontar massa magra.")
    render_period_cards()

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Analisar 7 dias", use_container_width=True):
            st.session_state["analysis_days"] = 7
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 7 dias com foco em consistência de treino, alimentação, sono e execução da rotina."})
    with c2:
        if st.button("Analisar 15 dias", use_container_width=True):
            st.session_state["analysis_days"] = 15
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 15 dias com foco em consistência, aderência da rotina e padrão de treino."})
    with c3:
        if st.button("Analisar 30 dias", use_container_width=True):
            st.session_state["analysis_days"] = 30
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 30 dias com foco em consistência, o que mais travou meu resultado e o que preciso corrigir primeiro."})

    days = st.session_state.get("analysis_days", 7)
    render_period_summary_card(period_summary(days))

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='card card-tight'><strong>Você</strong><div class='muted'>{msg['content']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='analysis-box'><div class='t'>IA</div>{msg['content']}</div>", unsafe_allow_html=True)

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.spinner("Analisando seus dados..."):
            ctx = build_context(days)
            system = """Você é um assistente analítico de saúde pessoal. Seja direto, prático e nada coach. O objetivo central do usuário é perder gordura preservando massa magra, reduzir risco de flacidez por perda mal conduzida e sair dos 3 dígitos com consistência. Foque em calorias, proteína, água, treino, sono, aderência e padrões do período. Não repita exame antigo sem motivo. Não invente fatos. Estruture em: leitura objetiva, consistência do período, principal gargalo, impacto sobre composição corporal, prioridade prática da próxima semana."""
            user = ctx + "\n\nPergunta do usuário: " + st.session_state.chat_history[-1]["content"]
            result = ask_openai(system, user, max_tokens=650)
            st.session_state.chat_history.append({"role": "assistant", "content": result})
            st.rerun()

    prompt = st.chat_input("Pergunte sobre seus dados...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.rerun()
    if st.session_state.chat_history and st.button("Limpar conversa", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


# ==================================================
# ROUTING
# ==================================================
PAGES = {
    "hoje": page_hoje,
    "alimentacao": page_alimentacao,
    "corpo": page_corpo,
    "historico": page_historico,
    "ia": page_ia,
}

PAGES[st.session_state.page]()
nav_bar()
