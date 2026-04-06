import calendar
import json
from datetime import date, timedelta, datetime, time

import pandas as pd
import streamlit as st
from openai import OpenAI
from supabase import create_client

# ============================================
# CONEXÕES
# ============================================
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_resource
def get_openai():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


db = get_supabase()
ai = get_openai()
OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", "gpt-5.4")

# ============================================
# CONFIG
# ============================================
st.set_page_config(
    page_title="MyGrubinessPal",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================
# VISUAL
# ============================================
st.markdown(
    """
<style>
.block-container { padding-top: 0.3rem; padding-bottom: 5rem; max-width: 700px; }
#MainMenu, footer, header { visibility: hidden; }
body { background: #0f1115; }

.card, .panel {
    background: #161921;
    border: 1px solid #2d3139;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
}

.section-title {
    font-size: 13px;
    font-weight: 800;
    color: #74c69d;
    text-transform: uppercase;
    letter-spacing: 1.3px;
    margin: 20px 0 10px 0;
}

.date-bar {
    background: #161921;
    border-radius: 14px;
    padding: 10px 10px 8px;
    margin-bottom: 14px;
    border: 1px solid #2d3139;
    text-align: center;
}
.date-label {
    color: #fafafa;
    font-size: 16px;
    font-weight: 700;
}
.date-sub {
    color: #9aa1aa;
    font-size: 12px;
    margin-top: 2px;
}

.big-number {
    color: #fafafa;
    font-size: 30px;
    font-weight: 800;
    line-height: 1;
}
.muted { color: #9aa1aa; font-size: 13px; }

.macro-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin: 8px 0 2px;
}
.macro-pill {
    background: #1d212a;
    border: 1px solid #2d3139;
    border-radius: 12px;
    padding: 10px 8px;
    text-align: center;
}
.macro-pill .l { color: #8f96a3; font-size: 10px; text-transform: uppercase; letter-spacing: 0.7px; }
.macro-pill .v { color: #fafafa; font-size: 18px; font-weight: 800; }

.status-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    margin-top: 6px;
}
.status-good { background: #183622; color: #8ee3b1; }
.status-warn { background: #3a3200; color: #ffd54f; }
.status-bad { background: #3a1b1b; color: #ef9a9a; }
.status-info { background: #1b2a3a; color: #90caf9; }

.meal-summary {
    background: #161921;
    border: 1px solid #2d3139;
    border-left: 4px solid #4caf50;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
}
.meal-summary.empty { border-left-color: #454b57; }
.meal-title { color: #fafafa; font-size: 14px; font-weight: 700; }
.meal-detail { color: #9aa1aa; font-size: 12px; margin-top: 3px; }

.quick-note {
    background: linear-gradient(135deg, #142018, #161921);
    border: 1px solid #2d3139;
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 8px;
}
.quick-note-label {
    color: #74c69d;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.quick-note-body {
    color: #e9f3ec;
    font-size: 14px;
    line-height: 1.5;
}

.small-kpi {
    background: #161921;
    border: 1px solid #2d3139;
    border-radius: 12px;
    padding: 12px;
    text-align: center;
}
.small-kpi .label { color: #9aa1aa; font-size: 11px; text-transform: uppercase; }
.small-kpi .value { color: #fafafa; font-size: 18px; font-weight: 800; margin-top: 2px; }

.streamlit-expanderHeader { font-size: 15px; font-weight: 700; }
.stButton > button { min-height: 44px; border-radius: 12px; }
.stCheckbox label { font-size: 14px; }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================
# STATE
# ============================================
if "page" not in st.session_state:
    st.session_state.page = "hoje"
if "sel_date" not in st.session_state:
    st.session_state.sel_date = date.today()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============================================
# REGRAS DE REFEIÇÃO
# ============================================
MEAL_CONFIG = {
    "cafe": {
        "label": "☕ Café da manhã",
        "foods": [
            "ovo_cozido", "whey_dose", "suco_verde", "leite_desnatado", "pao_integral",
            "banana", "aveia", "iogurte_grego", "cafe_puro", "queijo_branco",
        ],
    },
    "almoco": {
        "label": "🍚 Almoço",
        "foods": [
            "arroz_branco", "feijao_cozido", "arroz_feijao", "frango_grelhado", "patinho_moido",
            "carne_magra", "lombo_suino", "batata_cozida", "mandioca_cozida", "lentilha",
            "alface", "rucula", "tomate", "cenoura_crua", "beterraba", "chuchu", "vagem",
            "couve_cozida", "azeite", "agua", "refri_zero",
        ],
    },
    "lanche": {
        "label": "🥪 Lanche / Pré-treino",
        "foods": [
            "pao_integral", "whey_dose", "iogurte_grego", "banana", "queijo_branco",
            "castanhas", "cafe_puro", "leite_desnatado", "requeijao_light", "aveia",
        ],
    },
    "jantar": {
        "label": "🍽️ Jantar",
        "foods": [
            "macarrao_cozido", "arroz_branco", "frango_grelhado", "patinho_moido", "carne_magra",
            "hamburguer_caseiro", "mussarela", "pao_integral", "sopa_lentilha", "caldo_abobora",
            "alface", "rucula", "tomate", "cenoura_crua", "couve_cozida", "azeite", "agua", "refri_zero",
        ],
    },
    "ceia": {
        "label": "🌙 Ceia",
        "foods": ["iogurte_grego", "whey_dose", "queijo_branco", "banana", "leite_desnatado", "castanhas"],
    },
    "bebida": {
        "label": "🥤 Bebidas fora da refeição",
        "foods": [
            "agua", "cafe_puro", "refri_zero", "cerveja_lata", "cerveja_long", "cerveja_600",
            "vinho_taca", "destilado_dose", "chopp", "xeque_mate_lata", "aperol_spritz",
        ],
    },
}

FOOD_ONLY_KEYS = {"suco_verde", "whey", "whey_dose", "agua"}
ROUTINE_CATEGORY_BLACKLIST = {"food", "meal", "drink", "beverage", "alimentacao"}

# ============================================
# HELPERS
# ============================================
def q(table, select="*", **filters):
    query = db.table(table).select(select)
    for k, v in filters.items():
        query = query.eq(k, v)
    r = query.execute()
    return r.data or []


def parse_time_str(value):
    if not value:
        return None
    try:
        return datetime.strptime(value[:5], "%H:%M").time()
    except Exception:
        return None


def calculate_sleep_hours(bed_time, wake_time):
    if not bed_time or not wake_time:
        return None
    bed_dt = datetime.combine(date.today(), bed_time)
    wake_dt = datetime.combine(date.today(), wake_time)
    if wake_dt <= bed_dt:
        wake_dt += timedelta(days=1)
    return round((wake_dt - bed_dt).total_seconds() / 3600, 2)


def infer_selected_date_iso():
    return st.session_state.sel_date.isoformat()


def get_goals():
    r = q("goals", active=True)
    return {g["metric"]: g for g in r}


def get_weight_history(days=30, end_date=None):
    end_date = end_date or st.session_state.sel_date
    start = (end_date - timedelta(days=days)).isoformat()
    end = end_date.isoformat()
    r = (
        db.table("daily_weight")
        .select("date,weight_kg")
        .gte("date", start)
        .lte("date", end)
        .order("date")
        .execute()
    )
    return r.data or []


def get_weight(dt):
    r = q("daily_weight", date=dt)
    return float(r[0]["weight_kg"]) if r else None


def save_weight(dt, kg):
    db.table("daily_weight").upsert({"date": dt, "weight_kg": kg}, on_conflict="date").execute()


def get_checklist_items():
    r = db.table("checklist_items").select("*").eq("active", True).order("sort_order").execute()
    return r.data or []


def is_routine_item(item):
    key = str(item.get("item_key") or "").lower()
    name = str(item.get("name") or "").lower()
    category = str(item.get("category") or item.get("item_type") or "").lower()
    if key in FOOD_ONLY_KEYS:
        return False
    if category in ROUTINE_CATEGORY_BLACKLIST:
        return False
    food_words = ["suco", "whey", "café da manhã", "almoco", "almoço", "jantar", "lanche", "ceia"]
    if any(word in name for word in food_words):
        return False
    return True


def get_checklist(dt):
    r = q("checklist_daily", date=dt)
    return {x["item_key"]: x for x in r}


def save_check(dt, key, done):
    db.table("checklist_daily").upsert({"date": dt, "item_key": key, "done": done}, on_conflict="date,item_key").execute()


def get_meals(dt):
    return q("meals", date=dt)


def get_foods():
    r = db.table("food_library").select("*").eq("active", True).order("name").execute()
    return r.data or []


def get_sleep(dt):
    r = q("sleep_cpap", date=dt)
    return r[0] if r else {}


def meal_totals(meals):
    return {
        "kcal": sum(float(m.get("kcal") or 0) for m in meals),
        "prot": sum(float(m.get("protein_g") or 0) for m in meals),
        "carb": sum(float(m.get("carbs_g") or 0) for m in meals),
        "fat": sum(float(m.get("fat_g") or 0) for m in meals),
    }


def get_day_completion(dt):
    score = 0
    if get_weight(dt):
        score += 1
    meals = get_meals(dt)
    meal_types = {m.get("meal_type") for m in meals}
    if len(meal_types - {"bebida"}) >= 3:
        score += 2
    elif len(meal_types - {"bebida"}) >= 1:
        score += 1
    ck = get_checklist(dt)
    done_count = sum(1 for v in ck.values() if v.get("done"))
    if done_count >= 8:
        score += 2
    elif done_count >= 4:
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


def status_badge_html(text, level):
    level_map = {
        "good": "status-good",
        "warn": "status-warn",
        "bad": "status-bad",
        "info": "status-info",
    }
    return f'<span class="status-badge {level_map[level]}">{text}</span>'


def food_status_level(kcal, prot, goals):
    kg = float(goals.get("kcal_daily", {}).get("target_value", 2067))
    pg = float(goals.get("protein_daily", {}).get("target_value", 180))
    if kcal == 0:
        return "info", "Sem alimentação registrada"
    if kcal <= kg * 1.1 and prot >= pg * 0.85:
        return "good", "Dia coerente com a estratégia"
    if kcal <= kg * 1.25 and prot >= pg * 0.65:
        return "warn", "Quase coerente; revisar calorias ou proteína"
    return "bad", "Dia fora da estratégia"


def macro_pills(kcal, prot, carb, fat):
    st.markdown(
        f"""
        <div class="macro-grid">
            <div class="macro-pill"><div class="l">kcal</div><div class="v">{kcal:.0f}</div></div>
            <div class="macro-pill"><div class="l">prot</div><div class="v">{prot:.0f}g</div></div>
            <div class="macro-pill"><div class="l">carb</div><div class="v">{carb:.0f}g</div></div>
            <div class="macro-pill"><div class="l">gord</div><div class="v">{fat:.0f}g</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def meal_status_text(meal_type, items):
    if not items:
        return "Sem registro"
    kcal = sum(float(i.get("kcal") or 0) for i in items)
    prot = sum(float(i.get("protein_g") or 0) for i in items)
    if meal_type == "bebida":
        alcoholic = any("cerveja" in str(i.get("food_key") or "") or "vinho" in str(i.get("food_key") or "") or "destilado" in str(i.get("food_key") or "") or "aperol" in str(i.get("food_key") or "") or "chopp" in str(i.get("food_key") or "") for i in items)
        return f"{kcal:.0f} kcal" + (" · álcool registrado" if alcoholic else "")
    if prot >= 25 and kcal <= 800:
        return f"{kcal:.0f} kcal · boa base proteica"
    if prot >= 15:
        return f"{kcal:.0f} kcal · refeição intermediária"
    return f"{kcal:.0f} kcal · proteína baixa"


def get_last_lab_and_bio():
    lab = db.table("lab_results").select("date").order("date", desc=True).limit(1).execute().data or []
    bio = db.table("bioimpedance").select("date").order("date", desc=True).limit(1).execute().data or []
    return (lab[0] if lab else None), (bio[0] if bio else None)


# ============================================
# DATA BAR
# ============================================
def date_bar():
    d = st.session_state.sel_date
    c1, c2, c3, c4 = st.columns([1, 1.3, 3.2, 1])
    with c1:
        if st.button("◀", key=f"prev_{st.session_state.page}", use_container_width=True):
            st.session_state.sel_date -= timedelta(days=1)
            st.rerun()
    with c2:
        if st.button("Hoje", key=f"today_{st.session_state.page}", use_container_width=True):
            st.session_state.sel_date = date.today()
            st.rerun()
    with c3:
        new_date = st.date_input("data", value=d, label_visibility="collapsed", key=f"date_{st.session_state.page}")
        if new_date != d:
            st.session_state.sel_date = new_date
            st.rerun()
    with c4:
        if st.button("▶", key=f"next_{st.session_state.page}", use_container_width=True):
            st.session_state.sel_date += timedelta(days=1)
            st.rerun()

    dias_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    if d == date.today():
        label = f"Hoje — {d.strftime('%d/%m/%Y')}"
    elif d == date.today() - timedelta(days=1):
        label = f"Ontem — {d.strftime('%d/%m/%Y')}"
    else:
        label = f"{dias_pt[d.weekday()]} — {d.strftime('%d/%m/%Y')}"
    st.markdown(
        f'<div class="date-bar"><div class="date-label">{label}</div><div class="date-sub">Você pode preencher qualquer dia retroativamente.</div></div>',
        unsafe_allow_html=True,
    )
    return d.isoformat()


# ============================================
# NAVEGAÇÃO
# ============================================
def nav_bar():
    st.markdown("---")
    cols = st.columns(5)
    items = [
        ("hoje", "📋", "Hoje"),
        ("alimentacao", "🍽️", "Alim"),
        ("corpo", "😴", "Corpo"),
        ("historico", "📅", "Hist"),
        ("ia", "🤖", "IA"),
    ]
    for i, (key, icon, label) in enumerate(items):
        with cols[i]:
            kind = "primary" if st.session_state.page == key else "secondary"
            if st.button(f"{icon} {label}", key=f"nav_{key}", type=kind, use_container_width=True):
                st.session_state.page = key
                st.rerun()


# ============================================
# PÁGINA HOJE
# ============================================
def page_hoje():
    target = date_bar()
    goals = get_goals()
    weight_goal = float(goals.get("weight", {}).get("target_value", 90))
    kcal_goal = float(goals.get("kcal_daily", {}).get("target_value", 2067))
    protein_goal = float(goals.get("protein_daily", {}).get("target_value", 180))

    current_weight = get_weight(target)
    meals = get_meals(target)
    totals = meal_totals(meals)
    sleep = get_sleep(target)
    checklist_items = [item for item in get_checklist_items() if is_routine_item(item)]
    checklist_daily = get_checklist(target)

    # Peso e resumo
    st.markdown('<div class="section-title">⚖️ Peso e visão rápida</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        default_weight = current_weight if current_weight is not None else 143.0
        weight_input = st.number_input(
            "Peso do dia",
            min_value=50.0,
            max_value=250.0,
            value=float(default_weight),
            step=0.1,
            format="%.1f",
            key="weight_today_input",
            help="Você pode corrigir depois. O histórico recalcula automaticamente.",
        )
    with c2:
        if st.button("Salvar", key="save_today_weight", use_container_width=True):
            save_weight(target, weight_input)
            st.rerun()

    if current_weight is not None:
        st.markdown(
            f'<div class="panel"><div class="big-number">{current_weight:.1f} kg</div><div class="muted">Meta {weight_goal:.0f} kg · faltam {max(current_weight - weight_goal, 0):.1f} kg</div></div>',
            unsafe_allow_html=True,
        )

    hist = get_weight_history(days=30, end_date=st.session_state.sel_date)
    if len(hist) > 1:
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"])
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["meta"] = weight_goal
        df["media_7"] = df["weight_kg"].rolling(7, min_periods=1).mean()
        st.line_chart(df.set_index("date")[["weight_kg", "meta", "media_7"]], height=220, use_container_width=True)

    # KPIs resumidos
    st.markdown('<div class="section-title">📌 Resumo do dia</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="small-kpi"><div class="label">kcal</div><div class="value">{totals["kcal"]:.0f}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="small-kpi"><div class="label">prot</div><div class="value">{totals["prot"]:.0f}g</div></div>', unsafe_allow_html=True)
    with k3:
        energy = sleep.get("energy_score")
        st.markdown(f'<div class="small-kpi"><div class="label">energia</div><div class="value">{energy if energy is not None else "—"}</div></div>', unsafe_allow_html=True)
    with k4:
        checklist_done = sum(1 for item in checklist_items if checklist_daily.get(item["item_key"], {}).get("done"))
        st.markdown(f'<div class="small-kpi"><div class="label">rotina</div><div class="value">{checklist_done}/{len(checklist_items) if checklist_items else 0}</div></div>', unsafe_allow_html=True)

    macro_pills(totals["kcal"], totals["prot"], totals["carb"], totals["fat"])
    status_level, status_text = food_status_level(totals["kcal"], totals["prot"], goals)
    st.markdown(status_badge_html(status_text, status_level), unsafe_allow_html=True)
    st.caption(f"Meta do dia: {kcal_goal:.0f} kcal · proteína alvo: {protein_goal:.0f} g")

    # Resumo de alimentação por refeição
    st.markdown('<div class="section-title">🍽️ Alimentação do dia</div>', unsafe_allow_html=True)
    for meal_type in ["cafe", "almoco", "lanche", "jantar", "ceia", "bebida"]:
        config = MEAL_CONFIG[meal_type]
        items = [m for m in meals if m.get("meal_type") == meal_type]
        if items:
            names = ", ".join(str(m.get("food_key", "")).replace("_", " ") for m in items)
            detail = meal_status_text(meal_type, items)
            st.markdown(
                f'<div class="meal-summary"><div class="meal-title">{config["label"]}</div><div class="meal-detail">{detail} · {names}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="meal-summary empty"><div class="meal-title">{config["label"]}</div><div class="meal-detail">Sem registro</div></div>',
                unsafe_allow_html=True,
            )

    # Checklist limpo
    st.markdown('<div class="section-title">💊 Rotina do dia</div>', unsafe_allow_html=True)
    slot_labels = {
        "jejum": "☀️ Jejum",
        "manha": "Manhã",
        "almoco": "Almoço",
        "jantar": "Jantar",
        "noite": "Noite",
        "variavel": "Variável",
    }
    current_slot = None
    for item in checklist_items:
        slot = item.get("time_slot", "variavel")
        if slot != current_slot:
            current_slot = slot
            st.markdown(f"**{slot_labels.get(slot, slot)}**")
        checked = checklist_daily.get(item["item_key"], {}).get("done", False)
        label = item.get("name", item.get("item_key", "Item"))
        if item.get("dosage"):
            label += f" · {item['dosage']}"
        help_text = item.get("instruction") or None
        new_value = st.checkbox(label, value=checked, key=f"today_{target}_{item['item_key']}", help=help_text)
        if new_value != checked:
            save_check(target, item["item_key"], new_value)
            st.rerun()
        if help_text:
            st.caption(help_text)

    done_count = sum(1 for item in checklist_items if checklist_daily.get(item["item_key"], {}).get("done"))
    if checklist_items:
        st.caption(f"Aderência da rotina: {done_count}/{len(checklist_items)} ({done_count / len(checklist_items) * 100:.0f}%)")

    # Sono resumido
    st.markdown('<div class="section-title">😴 Sono / CPAP</div>', unsafe_allow_html=True)
    if sleep:
        hours = sleep.get("total_hours")
        ahi = sleep.get("ahi")
        energy = sleep.get("energy_score")
        st.markdown(
            f'<div class="panel"><div class="muted">{hours if hours is not None else "—"} h de sono · AHI {ahi if ahi is not None else "—"} · Energia {energy if energy is not None else "—"}/10</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="panel"><div class="muted">Sono ainda não registrado neste dia.</div></div>', unsafe_allow_html=True)

    # Atalhos
    st.markdown('<div class="section-title">⚡ Atalhos rápidos</div>', unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        if st.button("Alimentação", use_container_width=True):
            st.session_state.page = "alimentacao"
            st.rerun()
    with a2:
        if st.button("Sono", use_container_width=True):
            st.session_state.page = "corpo"
            st.session_state.corpo_tab = "😴 Sono"
            st.rerun()
    with a3:
        if st.button("Histórico", use_container_width=True):
            st.session_state.page = "historico"
            st.rerun()
    with a4:
        if st.button("IA", use_container_width=True):
            st.session_state.page = "ia"
            st.rerun()

    # Mensagem do dia sem repetir exame velho
    st.markdown('<div class="section-title">💬 Mensagem do dia</div>', unsafe_allow_html=True)
    if st.button("Gerar análise do dia", key="generate_day_message", use_container_width=True):
        with st.spinner("Analisando o dia..."):
            msg = generate_day_message(target, goals, meals, checklist_daily, checklist_items, sleep, current_weight)
            st.markdown(
                f'<div class="quick-note"><div class="quick-note-label">IA · análise do dia</div><div class="quick-note-body">{msg}</div></div>',
                unsafe_allow_html=True,
            )


# ============================================
# IA DO DIA
# ============================================
def generate_day_message(target, goals, meals, checklist_daily, checklist_items, sleep, weight):
    totals = meal_totals(meals) if meals else {"kcal": 0, "prot": 0, "carb": 0, "fat": 0}
    checklist_done = sum(1 for item in checklist_items if checklist_daily.get(item["item_key"], {}).get("done"))
    meal_types = sorted({m.get("meal_type") for m in meals}) if meals else []

    context = f"""
Dia selecionado: {target}
Peso do dia: {weight if weight is not None else 'não registrado'}
Meta calórica: {goals.get('kcal_daily', {}).get('target_value', 2067)} kcal
Meta de proteína: {goals.get('protein_daily', {}).get('target_value', 180)} g
Calorias consumidas: {totals['kcal']:.0f} kcal
Proteína: {totals['prot']:.0f} g
Carboidratos: {totals['carb']:.0f} g
Gorduras: {totals['fat']:.0f} g
Refeições registradas: {', '.join(meal_types) if meal_types else 'nenhuma'}
Rotina concluída: {checklist_done}/{len(checklist_items)}
Sono registrado: {'sim' if sleep else 'não'}
Horas de sono: {sleep.get('total_hours') if sleep else 'não registrado'}
Energia: {sleep.get('energy_score') if sleep else 'não registrado'}
"""

    try:
        response = ai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """Você é o assistente diário de saúde do João.
Seu trabalho aqui é analisar o dia operacionalmente, não fazer parecer clínico geral.
Regras obrigatórias:
- Foque só no que aconteceu neste dia.
- Não repita exames antigos, diagnósticos já conhecidos ou alertas crônicos.
- Só mencione exame ou bioimpedância se houver dado novo no próprio dia analisado, o que normalmente não ocorre.
- Seja direto, útil e específico.
- Máximo 4 frases curtas.
- Traga: 1 acerto, 1 ponto de atenção e 1 ajuste prático para hoje/amanhã.
- Não use linguagem de coach.
- Não diga que proteína alta sobrecarrega rins sem contexto clínico específico.
- Se faltar dado, diga objetivamente o que faltou registrar.""",
                },
                {"role": "user", "content": context},
            ],
            max_tokens=220,
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception as exc:
        return f"Erro ao gerar análise: {exc}"


# ============================================
# ALIMENTAÇÃO
# ============================================
def render_meal_selector(target, meal_type, config, foods, food_map):
    meal_items = [m for m in get_meals(target) if m.get("meal_type") == meal_type]
    if meal_items:
        for item in meal_items:
            food_name = food_map.get(item["food_key"], {}).get("name", str(item.get("food_key", "")).replace("_", " "))
            left, right = st.columns([5, 1])
            with left:
                st.markdown(
                    f"**{food_name}** · {float(item.get('quantity_g') or 0):.0f} g  \
_{float(item.get('kcal') or 0):.0f} kcal · P:{float(item.get('protein_g') or 0):.0f}g · C:{float(item.get('carbs_g') or 0):.0f}g · G:{float(item.get('fat_g') or 0):.0f}g_"
                )
            with right:
                if st.button("✕", key=f"delete_meal_{meal_type}_{item['id']}"):
                    db.table("meals").delete().eq("id", item["id"]).execute()
                    st.rerun()
    else:
        st.caption("Sem registro nesta refeição.")

    suggested = [f for f in foods if f["food_key"] in config["foods"]]
    extra = [f for f in foods if f["food_key"] not in config["foods"]]
    options = [""] + [f["food_key"] for f in suggested]
    labels = ["+ Escolha um alimento típico deste horário"] + [f["name"] for f in suggested]

    show_all = st.checkbox(
        "Mostrar todos os alimentos",
        value=False,
        key=f"show_all_{meal_type}_{target}",
        help="Ative só quando quiser buscar algo fora do comum para esse horário.",
    )
    if show_all and extra:
        options += [f["food_key"] for f in extra]
        labels += [f["name"] for f in extra]

    selected = st.selectbox(
        "Alimento",
        options,
        format_func=lambda x: labels[options.index(x)],
        key=f"food_select_{meal_type}_{target}",
        label_visibility="collapsed",
    )

    if selected:
        food = next((f for f in foods if f["food_key"] == selected), None)
        if not food:
            return
        default_portion = float(food.get("default_portion_g") or 100)
        qty = st.number_input(
            f"Quantidade em gramas · padrão {default_portion:.0f} g",
            min_value=1.0,
            max_value=3000.0,
            value=default_portion,
            step=10.0,
            key=f"qty_{meal_type}_{target}",
        )
        factor = qty / 100
        kcal = float(food.get("kcal_per_100g") or 0) * factor
        protein = float(food.get("protein_per_100g") or 0) * factor
        carbs = float(food.get("carbs_per_100g") or 0) * factor
        fat = float(food.get("fat_per_100g") or 0) * factor
        st.caption(f"→ {kcal:.0f} kcal · P:{protein:.0f}g · C:{carbs:.0f}g · G:{fat:.0f}g")
        if st.button("Adicionar item", key=f"add_{meal_type}_{target}", use_container_width=True):
            db.table("meals").insert(
                {
                    "date": target,
                    "meal_type": meal_type,
                    "food_key": selected,
                    "quantity_g": qty,
                    "portions": qty / default_portion if default_portion else None,
                    "kcal": kcal,
                    "protein_g": protein,
                    "carbs_g": carbs,
                    "fat_g": fat,
                }
            ).execute()
            st.rerun()


def page_alimentacao():
    target = date_bar()
    st.markdown('<div class="section-title">🍽️ Alimentação</div>', unsafe_allow_html=True)
    foods = get_foods()
    food_map = {f["food_key"]: f for f in foods}
    all_meals = get_meals(target)
    goals = get_goals()

    totals = meal_totals(all_meals)
    macro_pills(totals["kcal"], totals["prot"], totals["carb"], totals["fat"])
    level, text = food_status_level(totals["kcal"], totals["prot"], goals)
    st.markdown(status_badge_html(text, level), unsafe_allow_html=True)
    st.caption("Os alimentos aparecem primeiro por contexto de horário. Se precisar, você pode abrir a lista completa manualmente.")

    for meal_type in ["cafe", "almoco", "lanche", "jantar", "ceia", "bebida"]:
        config = MEAL_CONFIG[meal_type]
        items = [m for m in all_meals if m.get("meal_type") == meal_type]
        title = config["label"]
        detail = meal_status_text(meal_type, items)
        with st.expander(f"{title} · {detail}", expanded=False):
            render_meal_selector(target, meal_type, config, foods, food_map)


# ============================================
# CORPO & SONO
# ============================================
def page_corpo():
    target = date_bar()
    tab = st.radio(
        "",
        ["⚖️ Peso", "😴 Sono", "🏋️ Treino", "🔬 Bio/Exames"],
        horizontal=True,
        label_visibility="collapsed",
        key="corpo_tab",
    )
    if tab == "⚖️ Peso":
        page_peso_inner(target)
    elif tab == "😴 Sono":
        page_sono_inner(target)
    elif tab == "🏋️ Treino":
        page_treino_inner(target)
    else:
        page_bio_inner(target)


def page_peso_inner(target):
    st.markdown('<div class="section-title">⚖️ Peso e medidas</div>', unsafe_allow_html=True)
    goals = get_goals()
    weight_goal = float(goals.get("weight", {}).get("target_value", 90))
    period = st.selectbox("Período do gráfico", ["30 dias", "60 dias", "90 dias", "Tudo"], key="weight_period")
    days_map = {"30 dias": 30, "60 dias": 60, "90 dias": 90, "Tudo": 3650}
    hist = get_weight_history(days=days_map[period], end_date=st.session_state.sel_date)
    if hist:
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"])
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["meta"] = weight_goal
        df["media_7"] = df["weight_kg"].rolling(7, min_periods=1).mean()
        st.line_chart(df.set_index("date")[["weight_kg", "meta", "media_7"]], height=260, use_container_width=True)

    with st.expander("Registrar peso", expanded=True):
        current = get_weight(target)
        kg = st.number_input("Peso (kg)", 50.0, 250.0, float(current or 143.0), 0.1, key="body_weight_input")
        if st.button("Salvar peso", key="save_body_weight", use_container_width=True):
            save_weight(target, kg)
            st.rerun()

    with st.expander("Registrar medidas", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            waist = st.number_input("Cintura", 0.0, 250.0, 0.0, 0.5, key="measure_waist")
            abdomen = st.number_input("Abdômen", 0.0, 250.0, 0.0, 0.5, key="measure_abdomen")
            chest = st.number_input("Peito", 0.0, 250.0, 0.0, 0.5, key="measure_chest")
        with c2:
            arm = st.number_input("Braço", 0.0, 100.0, 0.0, 0.5, key="measure_arm")
            thigh = st.number_input("Coxa", 0.0, 150.0, 0.0, 0.5, key="measure_thigh")
            hip = st.number_input("Quadril", 0.0, 250.0, 0.0, 0.5, key="measure_hip")
        if st.button("Salvar medidas", key="save_measurements", use_container_width=True):
            db.table("measurements").insert(
                {
                    "date": target,
                    "waist_cm": waist or None,
                    "abdomen_cm": abdomen or None,
                    "chest_cm": chest or None,
                    "arm_cm": arm or None,
                    "thigh_cm": thigh or None,
                    "hip_cm": hip or None,
                }
            ).execute()
            st.success("Medidas salvas.")


def page_sono_inner(target):
    st.markdown('<div class="section-title">😴 Sono / CPAP</div>', unsafe_allow_html=True)
    data = get_sleep(target)
    bed_default = parse_time_str(data.get("bed_time")) or time(0, 0)
    wake_default = parse_time_str(data.get("wake_time")) or time(7, 0)

    with st.form("sleep_form"):
        c1, c2 = st.columns(2)
        with c1:
            bed_time = st.time_input("Dormiu às", value=bed_default)
            used_cpap = st.checkbox("Usou CPAP?", value=bool(data.get("used_cpap", True)))
            cpap_hours = st.number_input("Horas de uso do CPAP", 0.0, 16.0, float(data.get("cpap_hours") or 0), 0.5)
            ahi = st.number_input("AHI", 0.0, 100.0, float(data.get("ahi") or 0), 0.1)
        with c2:
            wake_time = st.time_input("Acordou às", value=wake_default)
            leak_rate = st.number_input("Vazamento", 0.0, 100.0, float(data.get("leak_rate") or 0), 0.1)
            mask_options = ["boa", "regular", "ruim"]
            mask_seal = st.selectbox("Vedação da máscara", mask_options, index=mask_options.index(data.get("mask_seal") or "boa"))
            events_per_hour = st.number_input("Eventos por hora", 0.0, 100.0, float(data.get("events_per_hour") or 0), 0.1)

        total_hours = calculate_sleep_hours(bed_time, wake_time)
        if total_hours is not None:
            st.info(f"Horas totais calculadas automaticamente: {total_hours:.2f} h")
        else:
            st.warning("Preencha horário de dormir e de acordar para calcular automaticamente.")

        removed_mask = st.checkbox("Tirou a máscara durante a noite?", value=bool(data.get("removed_mask", False)))
        c3, c4 = st.columns(2)
        with c3:
            tiredness = st.slider("Acordei cansado?", 0, 10, int(data.get("tiredness_score") or 5))
        with c4:
            energy = st.slider("Energia do dia", 0, 10, int(data.get("energy_score") or 5))
        notes = st.text_area("Observações", value=data.get("notes") or "", height=70)

        if st.form_submit_button("Salvar sono", use_container_width=True):
            db.table("sleep_cpap").upsert(
                {
                    "date": target,
                    "bed_time": bed_time.strftime("%H:%M") if bed_time else None,
                    "wake_time": wake_time.strftime("%H:%M") if wake_time else None,
                    "total_hours": total_hours,
                    "used_cpap": used_cpap,
                    "cpap_hours": cpap_hours,
                    "ahi": ahi,
                    "leak_rate": leak_rate,
                    "mask_seal": mask_seal,
                    "removed_mask": removed_mask,
                    "events_per_hour": events_per_hour,
                    "tiredness_score": tiredness,
                    "energy_score": energy,
                    "notes": notes,
                },
                on_conflict="date",
            ).execute()
            st.success("Sono salvo.")


def page_treino_inner(target):
    st.markdown('<div class="section-title">🏋️ Treino</div>', unsafe_allow_html=True)
    checklist = get_checklist(target)
    trained = checklist.get("treino", {}).get("done", False)
    new_trained = st.checkbox("Treinei neste dia", value=trained, key="trained_checkbox")
    if new_trained != trained:
        save_check(target, "treino", new_trained)
        st.rerun()
    if new_trained:
        period = st.radio("Horário", ["Manhã", "Tarde", "Fim de semana"], horizontal=True)
        notes = st.text_area("O que treinou / observações", placeholder="Ex: peito e tríceps, 1h10.")
        st.caption("Registro detalhado de treino pode crescer depois. Por agora, o objetivo é manter aderência e contexto.")


def page_bio_inner(target):
    st.markdown('<div class="section-title">🔬 Bioimpedância e exames</div>', unsafe_allow_html=True)
    tab_bio, tab_lab = st.tabs(["Bioimpedância", "Exames"])

    with tab_bio:
        with st.expander("Nova bioimpedância", expanded=False):
            with st.form("bio_form"):
                c1, c2 = st.columns(2)
                with c1:
                    weight = st.number_input("Peso (kg)", 50.0, 250.0, 143.0, 0.1)
                    fat_pct = st.number_input("% de gordura", 0.0, 80.0, 50.0, 0.1)
                    visceral = st.number_input("Gordura visceral", 0, 60, 31)
                with c2:
                    muscle = st.number_input("Músculo esquelético (kg)", 0.0, 100.0, 39.0, 0.1)
                    fat_free = st.number_input("Massa livre de gordura (kg)", 0.0, 150.0, 64.0, 0.1)
                    bmr = st.number_input("TMB (kcal)", 0.0, 5000.0, 2681.0, 1.0)
                notes = st.text_area("Observação", height=60)
                if st.form_submit_button("Salvar bio"):
                    db.table("bioimpedance").insert(
                        {
                            "date": target,
                            "weight_kg": weight,
                            "fat_pct": fat_pct,
                            "visceral_fat": visceral,
                            "skeletal_muscle_kg": muscle,
                            "fat_free_mass_kg": fat_free,
                            "bmr_kcal": bmr,
                            "notes": notes,
                        }
                    ).execute()
                    st.success("Bioimpedância salva.")

    with tab_lab:
        with st.expander("Novos exames", expanded=False):
            with st.form("lab_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    glucose = st.number_input("Glicose", 0.0, 500.0, 0.0, 1.0)
                    hba1c = st.number_input("HbA1c", 0.0, 15.0, 0.0, 0.1)
                    insulin = st.number_input("Insulina", 0.0, 100.0, 0.0, 0.1)
                    homa = st.number_input("HOMA-IR", 0.0, 20.0, 0.0, 0.01)
                    tsh = st.number_input("TSH", 0.0, 50.0, 0.0, 0.01)
                with c2:
                    t4 = st.number_input("T4 livre", 0.0, 10.0, 0.0, 0.01)
                    triglycerides = st.number_input("Triglicérides", 0.0, 1000.0, 0.0, 1.0)
                    ggt = st.number_input("GGT", 0.0, 500.0, 0.0, 1.0)
                    total_chol = st.number_input("Colesterol total", 0.0, 500.0, 0.0, 1.0)
                    ldl = st.number_input("LDL", 0.0, 300.0, 0.0, 1.0)
                with c3:
                    hdl = st.number_input("HDL", 0.0, 150.0, 0.0, 1.0)
                    magnesium = st.number_input("Magnésio", 0.0, 10.0, 0.0, 0.1)
                    b12 = st.number_input("B12", 0.0, 3000.0, 0.0, 1.0)
                    vitamin_d = st.number_input("Vitamina D", 0.0, 150.0, 0.0, 0.1)
                    testosterone = st.number_input("Testosterona", 0.0, 1500.0, 0.0, 1.0)
                notes = st.text_area("Observação", height=60)
                if st.form_submit_button("Salvar exames"):
                    db.table("lab_results").insert(
                        {
                            "date": target,
                            "glucose": glucose or None,
                            "hba1c": hba1c or None,
                            "insulin": insulin or None,
                            "homa_ir": homa or None,
                            "tsh": tsh or None,
                            "t4_free": t4 or None,
                            "triglycerides": triglycerides or None,
                            "ggt": ggt or None,
                            "total_cholesterol": total_chol or None,
                            "ldl": ldl or None,
                            "hdl": hdl or None,
                            "magnesium": magnesium or None,
                            "b12": b12 or None,
                            "vitamin_d": vitamin_d or None,
                            "testosterone": testosterone or None,
                            "notes": notes,
                        }
                    ).execute()
                    st.success("Exames salvos.")


# ============================================
# HISTÓRICO
# ============================================
def page_historico():
    st.markdown('<div class="section-title">📅 Histórico</div>', unsafe_allow_html=True)
    today = date.today()
    months = []
    current_month = today.replace(day=1)
    for i in range(6):
        ref = (current_month - timedelta(days=30 * i)).replace(day=1)
        months.append(ref)
    month_labels = [m.strftime("%B %Y") for m in months]
    idx = st.selectbox("Mês", range(len(months)), format_func=lambda i: month_labels[i], key="history_month")
    selected_month = months[idx]

    st.caption("Clique em qualquer dia para abrir e editar. Verde = bem preenchido; amarelo = incompleto; vermelho = quase vazio.")
    headers = st.columns(7)
    for col, label in zip(headers, ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]):
        col.markdown(f"<div class='muted' style='text-align:center;font-size:11px'>{label}</div>", unsafe_allow_html=True)

    cal = calendar.monthcalendar(selected_month.year, selected_month.month)
    icon = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚫"}
    for week in cal:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            with cols[i]:
                if day_num == 0:
                    st.write("")
                else:
                    d = date(selected_month.year, selected_month.month, day_num)
                    if d > today:
                        st.write("")
                    else:
                        dt = d.isoformat()
                        label = f"{icon[get_day_completion(dt)]} {day_num}"
                        if st.button(label, key=f"history_{dt}", use_container_width=True):
                            st.session_state.sel_date = d
                            st.session_state.page = "hoje"
                            st.rerun()


# ============================================
# IA GERAL
# ============================================
def build_context(days=14):
    end = st.session_state.sel_date
    start = (end - timedelta(days=days - 1)).isoformat()
    end_iso = end.isoformat()
    weights = get_weight_history(days=days, end_date=end)
    meals = db.table("meals").select("date,meal_type,food_key,kcal,protein_g,carbs_g,fat_g").gte("date", start).lte("date", end_iso).order("date").execute().data or []
    sleep = db.table("sleep_cpap").select("date,total_hours,ahi,energy_score,tiredness_score").gte("date", start).lte("date", end_iso).order("date").execute().data or []
    checks = db.table("checklist_daily").select("date,item_key,done").gte("date", start).lte("date", end_iso).order("date").execute().data or []
    bio = db.table("bioimpedance").select("*").order("date", desc=True).limit(1).execute().data or []
    labs = db.table("lab_results").select("*").order("date", desc=True).limit(1).execute().data or []
    return f"""
Período analisado: {start} até {end_iso}
Objetivo: emagrecer preservando massa magra.
Peso: {json.dumps(weights, default=str)}
Refeições: {json.dumps(meals, default=str)}
Sono: {json.dumps(sleep, default=str)}
Checklist: {json.dumps(checks, default=str)}
Bio mais recente: {json.dumps(bio, default=str)}
Exame mais recente: {json.dumps(labs, default=str)}
"""


def page_ia():
    st.markdown('<div class="section-title">🤖 IA / perguntas</div>', unsafe_allow_html=True)
    st.caption("Aqui sim faz sentido cruzar rotina, bioimpedância e exames. A mensagem do dia não deve repetir exame antigo.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Analisar últimos 7 dias", key="ia_7", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 7 dias com foco no que devo corrigir primeiro."})
            st.rerun()
    with c2:
        if st.button("Analisar últimos 14 dias", key="ia_14", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 14 dias com foco em aderência, alimentação, sono e peso."})
            st.rerun()

    c3, c4 = st.columns(2)
    with c3:
        if st.button("Peso travado", key="ia_plateau", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Meu peso travou? Onde está o principal gargalo?"})
            st.rerun()
    with c4:
        if st.button("Sono vs rotina", key="ia_sleep", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Como o sono influenciou meu período recente?"})
            st.rerun()

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='panel'><strong>Você</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='panel'><strong>IA</strong><br>{msg['content']}</div>", unsafe_allow_html=True)

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.spinner("Analisando seus dados..."):
            context = build_context(days=14)
            messages = [
                {
                    "role": "system",
                    "content": f"""Você é o assistente pessoal de saúde do João.
Use os dados estruturados abaixo para responder.

{context}

Regras:
- Seja direto, prático e específico.
- Não repita alertas clínicos genéricos sem ligação com os dados do período.
- Diga o que foi bem, o que foi mal e o que corrigir primeiro.
- Não use tom de coach.
- Máximo 220 palavras.""",
                }
            ]
            messages.extend(st.session_state.chat_history)
            try:
                response = ai.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    max_tokens=500,
                    temperature=0.5,
                )
                st.session_state.chat_history.append({"role": "assistant", "content": response.choices[0].message.content})
                st.rerun()
            except Exception as exc:
                st.error(f"Erro ao consultar IA: {exc}")
                st.session_state.chat_history.pop()

    prompt = st.chat_input("Pergunte sobre seus dados...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("Limpar conversa", key="clear_chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


# ============================================
# ROTAS
# ============================================
page_map = {
    "hoje": page_hoje,
    "alimentacao": page_alimentacao,
    "corpo": page_corpo,
    "historico": page_historico,
    "ia": page_ia,
}

page_map[st.session_state.page]()
nav_bar()
