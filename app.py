import json
from datetime import date, timedelta, datetime, time

import pandas as pd
import streamlit as st
from openai import OpenAI
from supabase import create_client

# ============================================
# CONEXÃO
# ============================================
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


@st.cache_resource
def get_openai():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def get_openai_model():
    try:
        return st.secrets["OPENAI_MODEL"]
    except Exception:
        return "gpt-5.4"


MODEL_NAME = get_openai_model()
db = get_supabase()
ai = get_openai()

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
# CSS
# ============================================
st.markdown(
    """
<style>
    .block-container {
        padding-top: 0.4rem;
        padding-bottom: 6rem;
        max-width: 760px;
    }
    #MainMenu, footer, header { visibility: hidden; }

    html, body, [class*="css"] {
        color: #F6F8FB;
    }

    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top, #0f1624 0%, #0b1018 55%, #080c12 100%);
    }

    [data-testid="stForm"] {
        border: 1px solid #253246;
        border-radius: 18px;
        padding: 16px 16px 8px 16px;
        background: rgba(14, 20, 31, 0.72);
    }

    .date-shell {
        background: linear-gradient(180deg, rgba(18,25,38,0.92) 0%, rgba(12,17,26,0.92) 100%);
        border: 1px solid #253246;
        border-radius: 18px;
        padding: 12px 14px;
        margin-bottom: 16px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.22);
    }
    .date-main {
        font-size: 20px;
        font-weight: 800;
        color: #F6F8FB;
        margin-top: 4px;
    }
    .date-sub {
        font-size: 12px;
        color: #95A2B8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .section-title {
        font-size: 12px;
        font-weight: 800;
        color: #64D99A;
        text-transform: uppercase;
        letter-spacing: 1.6px;
        margin: 18px 0 8px 0;
    }

    .hero-card, .soft-card, .ai-card {
        background: linear-gradient(180deg, rgba(20,28,42,0.96) 0%, rgba(14,20,31,0.96) 100%);
        border: 1px solid #253246;
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
    }

    .hero-weight {
        font-size: 40px;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 6px;
    }
    .hero-sub {
        color: #9AA7BA;
        font-size: 13px;
    }

    .mini-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-top: 12px;
    }
    .mini-card {
        background: rgba(10,14,21,0.44);
        border: 1px solid #233144;
        border-radius: 14px;
        padding: 12px;
        text-align: center;
    }
    .mini-l {
        font-size: 11px;
        color: #95A2B8;
        text-transform: uppercase;
        letter-spacing: .8px;
        margin-bottom: 6px;
    }
    .mini-v {
        font-size: 20px;
        font-weight: 800;
        color: #F6F8FB;
    }

    .macro-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin: 10px 0 8px 0;
    }
    .mp {
        background: rgba(10,14,21,0.46);
        border: 1px solid #233144;
        border-radius: 14px;
        padding: 12px 8px;
        text-align: center;
    }
    .mp .l {
        font-size: 10px;
        color: #95A2B8;
        text-transform: uppercase;
        letter-spacing: .8px;
    }
    .mp .v {
        font-size: 20px;
        font-weight: 800;
        color: #F6F8FB;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 13px;
        font-weight: 700;
        margin: 4px 0 2px 0;
        border: 1px solid transparent;
    }
    .badge.good { background: rgba(28,63,33,0.9); color: #8BE28E; border-color: rgba(139,226,142,0.14); }
    .badge.warn { background: rgba(74,60,13,0.9); color: #FFD85B; border-color: rgba(255,216,91,0.14); }
    .badge.bad  { background: rgba(68,26,26,0.9); color: #FF9B9B; border-color: rgba(255,155,155,0.14); }
    .badge.info { background: rgba(21,44,70,0.9); color: #89C7FF; border-color: rgba(137,199,255,0.14); }

    .meal-card {
        background: rgba(10,14,21,0.44);
        border: 1px solid #233144;
        border-left: 4px solid #55C46D;
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    .meal-card.empty { border-left-color: #394554; }
    .meal-name {
        font-weight: 800;
        color: #F6F8FB;
        font-size: 14px;
        margin-bottom: 3px;
    }
    .meal-detail {
        font-size: 12px;
        color: #99A7BC;
        line-height: 1.45;
    }

    .slot-title {
        font-size: 13px;
        font-weight: 800;
        color: #D9E3F3;
        margin: 10px 0 6px 0;
    }

    .soft-list {
        background: rgba(10,14,21,0.44);
        border: 1px solid #233144;
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 10px;
    }

    .ai-card {
        background: linear-gradient(135deg, rgba(19,41,27,0.96) 0%, rgba(13,19,29,0.96) 100%);
    }
    .ai-label {
        font-size: 11px;
        color: #64D99A;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .ai-copy {
        font-size: 15px;
        line-height: 1.6;
        color: #E6F4EA;
    }

    .subtle {
        color: #93A0B3;
        font-size: 13px;
    }

    .stButton > button,
    .stDownloadButton > button {
        min-height: 44px;
        border-radius: 12px;
    }

    .stCheckbox label { font-size: 15px; }
    .stNumberInput input, .stTextInput input, .stDateInput input { font-size: 16px !important; }

    div[data-testid="stHorizontalBlock"] > div > div > button[kind="primary"] {
        border: 1px solid #2F7A42;
        background: linear-gradient(180deg, #1C4B28 0%, #173C21 100%);
    }
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
if "day_analysis" not in st.session_state:
    st.session_state.day_analysis = {}

# ============================================
# HELPERS
# ============================================
def _safe_float(v, default=0.0):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def q(table, select="*", **filters):
    query = db.table(table).select(select)
    for k, v in filters.items():
        query = query.eq(k, v)
    r = query.execute()
    return r.data or []


def get_goals():
    r = q("goals", active=True)
    return {g["metric"]: g for g in r}


def get_weight_history(days=30, end_dt=None):
    end_date = end_dt or date.today()
    start = (end_date - timedelta(days=days)).isoformat()
    r = (
        db.table("daily_weight")
        .select("date,weight_kg")
        .gte("date", start)
        .lte("date", end_date.isoformat())
        .order("date")
        .execute()
    )
    return r.data or []


def get_weight(dt):
    r = q("daily_weight", date=dt)
    return _safe_float(r[0]["weight_kg"], None) if r else None


def save_weight(dt, kg):
    db.table("daily_weight").upsert({"date": dt, "weight_kg": kg}, on_conflict="date").execute()


def get_checklist_items():
    r = db.table("checklist_items").select("*").eq("active", True).order("sort_order").execute()
    return r.data or []


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


def get_latest_labs():
    r = db.table("lab_results").select("*").order("date", desc=True).limit(1).execute()
    return r.data[0] if r.data else {}


def get_latest_bio():
    r = db.table("bioimpedance").select("*").order("date", desc=True).limit(1).execute()
    return r.data[0] if r.data else {}


def meal_totals(meals):
    return {
        "kcal": sum(_safe_float(m.get("kcal")) for m in meals),
        "prot": sum(_safe_float(m.get("protein_g")) for m in meals),
        "carb": sum(_safe_float(m.get("carbs_g")) for m in meals),
        "fat": sum(_safe_float(m.get("fat_g")) for m in meals),
    }


def calculate_sleep_hours(bed_t, wake_t):
    if not bed_t or not wake_t:
        return None
    bed_dt = datetime.combine(date.today(), bed_t)
    wake_dt = datetime.combine(date.today(), wake_t)
    if wake_dt <= bed_dt:
        wake_dt += timedelta(days=1)
    return round((wake_dt - bed_dt).total_seconds() / 3600, 2)


def moving_average(values, window=7):
    if not values:
        return []
    series = pd.Series(values)
    return series.rolling(window=window, min_periods=1).mean().tolist()


def day_completeness(dt):
    score = 0
    if get_weight(dt):
        score += 1
    meals = get_meals(dt)
    meal_types = set(m.get("meal_type") for m in meals)
    if len(meal_types) >= 3:
        score += 2
    elif len(meal_types) >= 1:
        score += 1
    ck = get_checklist(dt)
    routine_items = [i for i in get_checklist_items() if item_in_checklist(i)]
    done_count = sum(1 for item in routine_items if ck.get(item["item_key"], {}).get("done"))
    if done_count >= 8:
        score += 2
    elif done_count >= 4:
        score += 1
    sleep = get_sleep(dt)
    if sleep:
        score += 1
    if score >= 5:
        return "green"
    if score >= 3:
        return "yellow"
    if score >= 1:
        return "red"
    return "gray"


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
        "label": "🥪 Lanche / pré-treino",
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
        "label": "🍺 Bebidas fora da refeição",
        "foods": [
            "cerveja_lata", "cerveja_long", "cerveja_600", "vinho_taca", "destilado_dose",
            "chopp", "xeque_mate_lata", "aperol_spritz", "agua", "cafe_puro", "refri_zero",
        ],
    },
}

# alimentação não entra no checklist da tela Hoje
FOOD_ONLY_KEYS = {
    "suco_verde", "whey", "whey_dose", "ovo_cozido", "banana", "aveia", "iogurte_grego",
    "cafe_puro", "leite_desnatado", "agua", "refri_zero",
}

ROUTINE_SLOT_LABELS = {
    "jejum": "☀️ Jejum",
    "manha": "Manhã",
    "almoco": "Almoço",
    "jantar": "Jantar",
    "noite": "Noite",
    "variavel": "Variável",
}


def item_in_checklist(item):
    category = str(item.get("category") or "").strip().lower()
    item_key = item.get("item_key")
    name = str(item.get("name") or "").strip().lower()
    if item_key in FOOD_ONLY_KEYS:
        return False
    if category in {"alimentacao", "alimento", "bebida", "meal", "food"}:
        return False
    if "suco" in name or "whey" in name:
        return False
    return True


def food_status_badge(kcal, prot, goals):
    kcal_goal = _safe_float(goals.get("kcal_daily", {}).get("target_value", 2067), 2067)
    prot_goal = _safe_float(goals.get("protein_daily", {}).get("target_value", 180), 180)
    if kcal == 0:
        return "info", "Sem alimentação registrada"
    if kcal <= kcal_goal * 1.1 and prot >= prot_goal * 0.85:
        return "good", "Dia coerente com a estratégia"
    if kcal <= kcal_goal * 1.25 or prot >= prot_goal * 0.7:
        return "warn", "Dia razoável, mas com pontos a ajustar"
    return "bad", "Dia fora da estratégia"


def render_badge(kind, text):
    st.markdown(f'<span class="badge {kind}">{text}</span>', unsafe_allow_html=True)


def macro_pills(kcal, prot, carb, fat):
    st.markdown(
        f'<div class="macro-row">'
        f'<div class="mp"><div class="l">kcal</div><div class="v">{kcal:.0f}</div></div>'
        f'<div class="mp"><div class="l">prot</div><div class="v">{prot:.0f}g</div></div>'
        f'<div class="mp"><div class="l">carb</div><div class="v">{carb:.0f}g</div></div>'
        f'<div class="mp"><div class="l">gord</div><div class="v">{fat:.0f}g</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def ai_text(prompt: str, max_output_tokens: int = 220) -> str:
    """Uses Responses API for GPT-5 models and falls back to Chat Completions if needed."""
    try:
        response = ai.responses.create(
            model=MODEL_NAME,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
        if getattr(response, "output_text", None):
            return response.output_text.strip()
        return str(response)
    except Exception:
        response = ai.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=max_output_tokens,
        )
        return response.choices[0].message.content.strip()


# ============================================
# DATE BAR
# ============================================
def date_bar():
    d = st.session_state.sel_date
    c1, c2, c3, c4 = st.columns([1, 1.2, 3, 1])
    with c1:
        if st.button("◀", key=f"db_prev_{st.session_state.page}", use_container_width=True):
            st.session_state.sel_date -= timedelta(days=1)
            st.rerun()
    with c2:
        if st.button("Hoje", key=f"db_today_{st.session_state.page}", use_container_width=True, disabled=d == date.today()):
            st.session_state.sel_date = date.today()
            st.rerun()
    with c3:
        new_d = st.date_input("data", value=d, key=f"db_cal_{st.session_state.page}", label_visibility="collapsed")
        if new_d != d:
            st.session_state.sel_date = new_d
            st.rerun()
    with c4:
        if st.button("▶", key=f"db_next_{st.session_state.page}", use_container_width=True):
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
        f'<div class="date-shell"><div class="date-sub">Registro diário</div><div class="date-main">{label}</div></div>',
        unsafe_allow_html=True,
    )
    return d.isoformat()


# ============================================
# NAV BAR
# ============================================
def nav_bar():
    st.markdown("---")
    cols = st.columns(5)
    items = [
        ("hoje", "📋", "Hoje"),
        ("alimentacao", "🍽️", "Alim"),
        ("corpo", "🏋️", "Corpo"),
        ("historico", "📅", "Hist"),
        ("ia", "🤖", "IA"),
    ]
    for i, (key, icon, label) in enumerate(items):
        with cols[i]:
            tp = "primary" if st.session_state.page == key else "secondary"
            if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True, type=tp):
                st.session_state.page = key
                st.rerun()


# ============================================
# AI: DAILY ANALYSIS
# ============================================
def build_day_analysis_prompt(target, goals, meals, checklist, sleep, weight):
    totals = meal_totals(meals) if meals else {"kcal": 0, "prot": 0, "carb": 0, "fat": 0}
    kcal_goal = _safe_float(goals.get("kcal_daily", {}).get("target_value", 2067), 2067)
    prot_goal = _safe_float(goals.get("protein_daily", {}).get("target_value", 180), 180)
    routine_items = [i for i in get_checklist_items() if item_in_checklist(i)]
    done = sum(1 for item in routine_items if checklist.get(item["item_key"], {}).get("done"))
    total_items = len(routine_items)

    meal_lines = []
    for meal_key, meal_cfg in MEAL_CONFIG.items():
        items = [m for m in meals if m.get("meal_type") == meal_key]
        if not items:
            continue
        names = ", ".join(str(m.get("food_key", "")).replace("_", " ") for m in items)
        meal_lines.append(f"- {meal_cfg['label']}: {names}")

    sleep_line = "Sono não registrado."
    if sleep:
        sleep_line = (
            f"Sono: {sleep.get('total_hours') or '—'}h, AHI {sleep.get('ahi') or '—'}, "
            f"energia {sleep.get('energy_score') or '—'}/10."
        )

    return f"""
Você é o assistente diário de João. Analise APENAS o dia {target}.

Regras obrigatórias:
- Não repetir quadro clínico antigo, exames antigos ou bioimpedância antiga na mensagem do dia.
- Só mencionar exame se houve exame novo recente no próprio dia ou se o usuário perguntou disso especificamente.
- Não fazer alarmismo genérico sobre rins, tireoide ou triglicérides.
- O foco é operacional: o que aconteceu hoje e o que ajustar na próxima refeição ou amanhã.
- Fale em português do Brasil.
- Use no máximo 4 frases curtas.
- Estrutura: 1 ponto positivo + 1 ponto de atenção + 1 ajuste prático.
- Se faltar dado, diga com objetividade.

Dados do dia:
- Peso: {weight if weight is not None else 'não registrado'} kg
- Meta calórica: {kcal_goal:.0f} kcal
- Meta de proteína: {prot_goal:.0f} g
- Consumo até agora: {totals['kcal']:.0f} kcal | proteína {totals['prot']:.0f} g | carbo {totals['carb']:.0f} g | gordura {totals['fat']:.0f} g
- Refeições registradas: {len(set(m.get('meal_type') for m in meals))}
- Rotina: {done}/{total_items} itens concluídos
- {sleep_line}

Refeições do dia:
{chr(10).join(meal_lines) if meal_lines else '- Nenhuma refeição registrada.'}
""".strip()


def generate_day_message(target, goals, meals, checklist, sleep, weight):
    prompt = build_day_analysis_prompt(target, goals, meals, checklist, sleep, weight)
    try:
        return ai_text(prompt, max_output_tokens=220)
    except Exception as e:
        return f"Erro ao gerar análise: {e}"


# ============================================
# PAGES
# ============================================
def page_hoje():
    target = date_bar()
    goals = get_goals()
    target_weight = _safe_float(goals.get("weight", {}).get("target_value", 90), 90)

    current_weight = get_weight(target)
    weight_input_default = current_weight if current_weight is not None else 143.0

    st.markdown('<div class="section-title">Visão do dia</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3.5, 1])
    with c1:
        weight_value = st.number_input(
            "Peso do dia",
            min_value=50.0,
            max_value=250.0,
            value=float(weight_input_default),
            step=0.1,
            format="%.1f",
            key="today_weight",
        )
    with c2:
        st.write("")
        if st.button("Salvar peso", key="save_today_weight", use_container_width=True):
            save_weight(target, weight_value)
            st.rerun()

    delta_to_goal = None
    if current_weight is not None:
        delta_to_goal = current_weight - target_weight

    st.markdown(
        f'<div class="hero-card">'
        f'<div class="hero-weight">{(current_weight if current_weight is not None else weight_value):.1f} kg</div>'
        f'<div class="hero-sub">Meta {target_weight:.0f} kg'
        + (f' · faltam {delta_to_goal:.1f} kg' if delta_to_goal is not None else '')
        + f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    hist = get_weight_history(30, end_dt=st.session_state.sel_date)
    if len(hist) > 1:
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"])
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["meta"] = target_weight
        df["media_7"] = moving_average(df["weight_kg"].tolist(), 7)
        st.line_chart(df.set_index("date")[["weight_kg", "meta", "media_7"]], height=220, use_container_width=True)

    meals = get_meals(target)
    totals = meal_totals(meals)
    sleep = get_sleep(target)
    checklist = get_checklist(target)
    routine_items = [i for i in get_checklist_items() if item_in_checklist(i)]
    routine_done = sum(1 for item in routine_items if checklist.get(item["item_key"], {}).get("done"))
    routine_total = len(routine_items)

    st.markdown(
        f'<div class="mini-grid">'
        f'<div class="mini-card"><div class="mini-l">kcal</div><div class="mini-v">{totals["kcal"]:.0f}</div></div>'
        f'<div class="mini-card"><div class="mini-l">proteína</div><div class="mini-v">{totals["prot"]:.0f}g</div></div>'
        f'<div class="mini-card"><div class="mini-l">rotina</div><div class="mini-v">{routine_done}/{routine_total or 0}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if sleep:
        st.markdown(
            f'<div class="soft-card"><span class="subtle">Sono registrado: {sleep.get("total_hours") or "—"}h · '
            f'AHI {sleep.get("ahi") or "—"} · energia {sleep.get("energy_score") or "—"}/10</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="soft-card"><span class="subtle">Sono ainda não registrado para este dia.</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Alimentação do dia</div>', unsafe_allow_html=True)
    macro_pills(totals["kcal"], totals["prot"], totals["carb"], totals["fat"])
    badge_kind, badge_text = food_status_badge(totals["kcal"], totals["prot"], goals)
    render_badge(badge_kind, badge_text)

    if meals:
        for meal_key, meal_cfg in MEAL_CONFIG.items():
            items = [m for m in meals if m.get("meal_type") == meal_key]
            if not items:
                continue
            kcal = sum(_safe_float(m.get("kcal")) for m in items)
            names = ", ".join(str(m.get("food_key", "")).replace("_", " ") for m in items)
            st.markdown(
                f'<div class="meal-card"><div class="meal-name">{meal_cfg["label"]} · {kcal:.0f} kcal</div>'
                f'<div class="meal-detail">{names}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="meal-card empty"><div class="meal-name">Sem alimentação registrada</div>'
            '<div class="meal-detail">Use o módulo Alimentação para lançar as refeições do dia.</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Rotina do dia</div>', unsafe_allow_html=True)
    current_slot = ""
    for item in routine_items:
        slot = item.get("time_slot") or "variavel"
        if slot != current_slot:
            current_slot = slot
            st.markdown(f'<div class="slot-title">{ROUTINE_SLOT_LABELS.get(slot, slot)}</div>', unsafe_allow_html=True)
        checked = checklist.get(item["item_key"], {}).get("done", False)
        dose = f" · {item['dosage']}" if item.get("dosage") else ""
        label = f"{item['name']}{dose}"
        if item.get("instruction"):
            label += f"  \n_{item['instruction']}_"
        new_val = st.checkbox(label, value=checked, key=f"check_{target}_{item['item_key']}")
        if new_val != checked:
            save_check(target, item["item_key"], new_val)
            st.rerun()

    st.caption(f"Aderência: {routine_done}/{routine_total or 0} ({(routine_done / routine_total * 100) if routine_total else 0:.0f}%)")

    st.markdown('<div class="section-title">Atalhos rápidos</div>', unsafe_allow_html=True)
    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        if st.button("🍽️ Alimentação", use_container_width=True):
            st.session_state.page = "alimentacao"
            st.rerun()
    with ac2:
        if st.button("😴 Sono", use_container_width=True):
            st.session_state.page = "corpo"
            st.rerun()
    with ac3:
        if st.button("📅 Histórico", use_container_width=True):
            st.session_state.page = "historico"
            st.rerun()

    st.markdown('<div class="section-title">Mensagem do dia</div>', unsafe_allow_html=True)
    cached = st.session_state.day_analysis.get(target)
    if cached:
        st.markdown(f'<div class="ai-card"><div class="ai-label">IA · análise do dia</div><div class="ai-copy">{cached}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="soft-card"><span class="subtle">A análise agora considera apenas o dia selecionado e não repete exames antigos automaticamente.</span></div>', unsafe_allow_html=True)

    if st.button("Gerar análise do dia", key="generate_day_analysis", use_container_width=True):
        with st.spinner("Analisando seu dia..."):
            msg = generate_day_message(target, goals, meals, checklist, sleep, current_weight)
            st.session_state.day_analysis[target] = msg
            st.rerun()



def page_alimentacao():
    target = date_bar()
    st.markdown('<div class="section-title">Alimentação por refeição</div>', unsafe_allow_html=True)

    foods = get_foods()
    food_map = {f["food_key"]: f for f in foods}
    food_names = {f["food_key"]: f["name"] for f in foods}
    goals = get_goals()
    all_meals = get_meals(target)
    totals = meal_totals(all_meals)

    macro_pills(totals["kcal"], totals["prot"], totals["carb"], totals["fat"])
    badge_kind, badge_text = food_status_badge(totals["kcal"], totals["prot"], goals)
    render_badge(badge_kind, badge_text)

    for meal_key, meal_cfg in MEAL_CONFIG.items():
        items = [m for m in all_meals if m.get("meal_type") == meal_key]
        meal_kcal = sum(_safe_float(m.get("kcal")) for m in items)
        with st.expander(f"{meal_cfg['label']} · {meal_kcal:.0f} kcal", expanded=False):
            if items:
                for m in items:
                    food_name = food_names.get(m.get("food_key"), str(m.get("food_key", "")).replace("_", " "))
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(
                            f"**{food_name}** · {_safe_float(m.get('quantity_g')):.0f}g  \n"
                            f"_{_safe_float(m.get('kcal')):.0f} kcal · P:{_safe_float(m.get('protein_g')):.0f}g · "
                            f"C:{_safe_float(m.get('carbs_g')):.0f}g · G:{_safe_float(m.get('fat_g')):.0f}g_"
                        )
                    with c2:
                        if st.button("✕", key=f"delete_meal_{m['id']}"):
                            db.table("meals").delete().eq("id", m["id"]).execute()
                            st.rerun()
            else:
                st.caption("Nenhum item lançado ainda.")

            suggested = [f for f in foods if f["food_key"] in meal_cfg["foods"]]
            show_all = st.checkbox("Mostrar todos os alimentos", key=f"show_all_{meal_key}_{target}")
            source_list = foods if show_all else suggested
            if not source_list:
                st.info("Nenhum alimento encontrado para este horário.")
                continue

            option_keys = [""] + [f["food_key"] for f in source_list]
            option_names = {"": "+ adicionar alimento..."}
            option_names.update({f["food_key"]: f["name"] for f in source_list})
            selected = st.selectbox(
                "Escolha o alimento",
                options=option_keys,
                format_func=lambda x: option_names[x],
                key=f"select_{meal_key}_{target}",
                label_visibility="collapsed",
            )

            if selected:
                fd = food_map[selected]
                default_g = _safe_float(fd.get("default_portion_g"), 100)
                qty = st.number_input(
                    f"Quantidade em gramas · porção padrão {default_g:.0f}g",
                    min_value=1.0,
                    max_value=2000.0,
                    value=float(default_g),
                    step=10.0,
                    key=f"qty_{meal_key}_{target}_{selected}",
                )
                factor = qty / 100
                kcal = _safe_float(fd.get("kcal_per_100g")) * factor
                prot = _safe_float(fd.get("protein_per_100g")) * factor
                carb = _safe_float(fd.get("carbs_per_100g")) * factor
                fat = _safe_float(fd.get("fat_per_100g")) * factor
                st.caption(f"→ {kcal:.0f} kcal · P:{prot:.0f}g · C:{carb:.0f}g · G:{fat:.0f}g")

                if st.button("Adicionar item", key=f"add_food_{meal_key}_{target}_{selected}", use_container_width=True):
                    db.table("meals").insert(
                        {
                            "date": target,
                            "meal_type": meal_key,
                            "food_key": selected,
                            "quantity_g": qty,
                            "portions": qty / default_g if default_g else None,
                            "kcal": kcal,
                            "protein_g": prot,
                            "carbs_g": carb,
                            "fat_g": fat,
                        }
                    ).execute()
                    st.rerun()



def page_corpo():
    target = date_bar()
    tab = st.radio("", ["⚖️ Peso", "😴 Sono", "🏋️ Treino", "🔬 Bio/Exames"], horizontal=True, label_visibility="collapsed")
    if tab == "⚖️ Peso":
        page_peso_inner(target)
    elif tab == "😴 Sono":
        page_sono_inner(target)
    elif tab == "🏋️ Treino":
        page_treino_inner(target)
    else:
        page_bio_inner(target)



def page_peso_inner(target):
    st.markdown('<div class="section-title">Peso e medidas</div>', unsafe_allow_html=True)
    goals = get_goals()
    target_weight = _safe_float(goals.get("weight", {}).get("target_value", 90), 90)
    period = st.selectbox("Período", ["30 dias", "60 dias", "90 dias", "Tudo"], key="period_weight")
    days_map = {"30 dias": 30, "60 dias": 60, "90 dias": 90, "Tudo": 3650}
    hist = get_weight_history(days_map[period], end_dt=st.session_state.sel_date)
    if hist:
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"])
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["meta"] = target_weight
        df["media_7"] = moving_average(df["weight_kg"].tolist(), 7)
        st.line_chart(df.set_index("date")[["weight_kg", "meta", "media_7"]], height=280)

    with st.expander("Registrar peso", expanded=False):
        dt = st.date_input("Data", value=st.session_state.sel_date, key="weight_form_date")
        p = st.number_input("Peso em kg", 50.0, 250.0, 143.0, 0.1, key="weight_form_value")
        if st.button("Salvar peso", key="save_weight_form", use_container_width=True):
            save_weight(dt.isoformat(), p)
            st.success("Peso salvo.")
            st.rerun()

    with st.expander("Registrar medidas", expanded=False):
        dm = st.date_input("Data das medidas", value=st.session_state.sel_date, key="measure_form_date")
        c1, c2 = st.columns(2)
        with c1:
            waist = st.number_input("Cintura", 0.0, 250.0, 0.0, 0.5, key="m_waist")
            abdomen = st.number_input("Abdômen", 0.0, 250.0, 0.0, 0.5, key="m_abdomen")
            chest = st.number_input("Peito", 0.0, 250.0, 0.0, 0.5, key="m_chest")
        with c2:
            arm = st.number_input("Braço", 0.0, 100.0, 0.0, 0.5, key="m_arm")
            thigh = st.number_input("Coxa", 0.0, 150.0, 0.0, 0.5, key="m_thigh")
            hip = st.number_input("Quadril", 0.0, 250.0, 0.0, 0.5, key="m_hip")
        if st.button("Salvar medidas", key="save_measure_form", use_container_width=True):
            db.table("measurements").insert(
                {
                    "date": dm.isoformat(),
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
    st.markdown('<div class="section-title">Sono / CPAP</div>', unsafe_allow_html=True)
    data = get_sleep(target)
    default_bed = None
    default_wake = None
    try:
        if data.get("bed_time"):
            default_bed = datetime.strptime(data.get("bed_time"), "%H:%M:%S").time()
    except Exception:
        default_bed = None
    try:
        if data.get("wake_time"):
            default_wake = datetime.strptime(data.get("wake_time"), "%H:%M:%S").time()
    except Exception:
        default_wake = None

    with st.form("sleep_form"):
        c1, c2 = st.columns(2)
        with c1:
            bed_t = st.time_input("Dormiu às", value=default_bed, key="sleep_bed")
            used_cpap = st.checkbox("Usou CPAP?", value=bool(data.get("used_cpap", True)))
            cpap_hours = st.number_input("Horas de uso do CPAP", 0.0, 16.0, _safe_float(data.get("cpap_hours"), 0.0), 0.5)
            tired = st.slider("Acordou cansado?", 0, 10, int(data.get("tiredness_score") or 5))
        with c2:
            wake_t = st.time_input("Acordou às", value=default_wake, key="sleep_wake")
            ahi = st.number_input("AHI", 0.0, 100.0, _safe_float(data.get("ahi"), 0.0), 0.1)
            leak = st.number_input("Vazamento", 0.0, 100.0, _safe_float(data.get("leak_rate"), 0.0), 0.1)
            energy = st.slider("Energia do dia", 0, 10, int(data.get("energy_score") or 5))

        auto_hours = calculate_sleep_hours(bed_t, wake_t)
        if auto_hours is not None:
            render_badge("info", f"Sono calculado automaticamente: {auto_hours:.1f}h")
        else:
            st.caption("Preencha horário de dormir e acordar para calcular automaticamente.")

        c3, c4 = st.columns(2)
        with c3:
            mask_seal = st.selectbox("Vedação da máscara", ["boa", "regular", "ruim"], index=["boa", "regular", "ruim"].index(data.get("mask_seal") or "boa"))
        with c4:
            removed_mask = st.checkbox("Tirou a máscara?", value=bool(data.get("removed_mask", False)))
        events = st.number_input("Eventos por hora", 0.0, 100.0, _safe_float(data.get("events_per_hour"), 0.0), 0.1)
        notes = st.text_area("Observações", value=data.get("notes") or "", height=80)

        if st.form_submit_button("Salvar sono / CPAP", use_container_width=True):
            db.table("sleep_cpap").upsert(
                {
                    "date": target,
                    "bed_time": bed_t.isoformat() if bed_t else None,
                    "wake_time": wake_t.isoformat() if wake_t else None,
                    "total_hours": auto_hours,
                    "used_cpap": used_cpap,
                    "cpap_hours": cpap_hours,
                    "ahi": ahi,
                    "leak_rate": leak,
                    "mask_seal": mask_seal,
                    "removed_mask": removed_mask,
                    "events_per_hour": events,
                    "tiredness_score": tired,
                    "energy_score": energy,
                    "notes": notes,
                },
                on_conflict="date",
            ).execute()
            st.success("Sono salvo.")
            st.rerun()



def page_treino_inner(target):
    st.markdown('<div class="section-title">Treino</div>', unsafe_allow_html=True)
    ck = get_checklist(target)
    treino_done = ck.get("treino", {}).get("done", False)
    treinou = st.checkbox("Treinei hoje", value=treino_done, key="workout_done")
    if treinou != treino_done:
        save_check(target, "treino", treinou)
        st.rerun()
    if treinou:
        horario = st.radio("Horário", ["Manhã (7h)", "Tarde", "Fim de semana (10–11h)"], horizontal=True)
        obs = st.text_area("O que treinou / observações", height=90, placeholder="Ex: peito e tríceps, 1h15")
        st.caption("Registro detalhado de treino pode ser expandido depois. Por enquanto, o foco é aderência real de uso.")



def page_bio_inner(target):
    st.markdown('<div class="section-title">Bioimpedância e exames</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Bioimpedância", "Exames"])
    with tab1:
        with st.expander("Nova bioimpedância", expanded=False):
            with st.form("bio_form"):
                dt = st.date_input("Data", key="bio_date")
                c1, c2 = st.columns(2)
                with c1:
                    bw = st.number_input("Peso (kg)", 50.0, 250.0, 143.0, 0.1)
                    bf = st.number_input("% gordura", 0.0, 80.0, 50.0, 0.1)
                    bv = st.number_input("Gordura visceral", 0, 60, 31)
                with c2:
                    bm = st.number_input("Musc. esquelética (kg)", 0.0, 100.0, 39.0, 0.1)
                    bff = st.number_input("Massa livre de gordura (kg)", 0.0, 150.0, 64.0, 0.1)
                    bb = st.number_input("TMB (kcal)", 0.0, 5000.0, 2681.0, 1.0)
                bn = st.text_area("Observação", height=70)
                if st.form_submit_button("Salvar bioimpedância"):
                    db.table("bioimpedance").insert(
                        {
                            "date": dt.isoformat(),
                            "weight_kg": bw,
                            "fat_pct": bf,
                            "visceral_fat": bv,
                            "skeletal_muscle_kg": bm,
                            "fat_free_mass_kg": bff,
                            "bmr_kcal": bb,
                            "notes": bn,
                        }
                    ).execute()
                    st.success("Bioimpedância salva.")
                    st.rerun()

        latest_bio = get_latest_bio()
        if latest_bio:
            st.markdown(
                f'<div class="soft-card"><strong>Mais recente:</strong> {latest_bio.get("date")} · '
                f'{latest_bio.get("weight_kg")}kg · gordura {latest_bio.get("fat_pct")}% · '
                f'visceral {latest_bio.get("visceral_fat")} · músculo {latest_bio.get("skeletal_muscle_kg")}kg</div>',
                unsafe_allow_html=True,
            )

    with tab2:
        with st.expander("Novos exames", expanded=False):
            with st.form("labs_form"):
                dt = st.date_input("Data dos exames", key="labs_date")
                c1, c2, c3 = st.columns(3)
                with c1:
                    glucose = st.number_input("Glicose", 0.0, 500.0, 0.0, 1.0)
                    hba1c = st.number_input("HbA1c", 0.0, 15.0, 0.0, 0.1)
                    insulin = st.number_input("Insulina", 0.0, 100.0, 0.0, 0.1)
                    homa = st.number_input("HOMA-IR", 0.0, 20.0, 0.0, 0.01)
                    tsh = st.number_input("TSH", 0.0, 50.0, 0.0, 0.01)
                with c2:
                    t4 = st.number_input("T4 livre", 0.0, 10.0, 0.0, 0.01)
                    tri = st.number_input("Triglicérides", 0.0, 1000.0, 0.0, 1.0)
                    ggt = st.number_input("GGT", 0.0, 500.0, 0.0, 1.0)
                    total_chol = st.number_input("Colesterol total", 0.0, 500.0, 0.0, 1.0)
                    ldl = st.number_input("LDL", 0.0, 300.0, 0.0, 1.0)
                with c3:
                    hdl = st.number_input("HDL", 0.0, 150.0, 0.0, 1.0)
                    magnesium = st.number_input("Magnésio", 0.0, 10.0, 0.0, 0.1)
                    b12 = st.number_input("B12", 0.0, 2000.0, 0.0, 1.0)
                    vitamin_d = st.number_input("Vitamina D", 0.0, 150.0, 0.0, 0.1)
                    testosterone = st.number_input("Testosterona", 0.0, 1500.0, 0.0, 1.0)
                notes = st.text_area("Observação", height=70)
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
                            "triglycerides": tri or None,
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
                    st.rerun()

        latest_labs = get_latest_labs()
        if latest_labs:
            pieces = []
            if latest_labs.get("glucose"):
                pieces.append(f"Glic {latest_labs['glucose']}")
            if latest_labs.get("hba1c"):
                pieces.append(f"HbA1c {latest_labs['hba1c']}")
            if latest_labs.get("tsh"):
                pieces.append(f"TSH {latest_labs['tsh']}")
            if latest_labs.get("triglycerides"):
                pieces.append(f"Trig {latest_labs['triglycerides']}")
            if latest_labs.get("testosterone"):
                pieces.append(f"Testo {latest_labs['testosterone']}")
            st.markdown(
                f'<div class="soft-card"><strong>Exame mais recente:</strong> {latest_labs.get("date")} · ' + " · ".join(pieces) + "</div>",
                unsafe_allow_html=True,
            )



def page_historico():
    st.markdown('<div class="section-title">Histórico</div>', unsafe_allow_html=True)
    today = date.today()
    months = []
    for i in range(6):
        d = today.replace(day=1) - timedelta(days=30 * i)
        months.append(d.replace(day=1))
    month_labels = [m.strftime("%B %Y") for m in months]
    sel_idx = st.selectbox("Mês", range(len(months)), format_func=lambda i: month_labels[i])
    sel_month = months[sel_idx]

    import calendar
    cal = calendar.monthcalendar(sel_month.year, sel_month.month)
    header = st.columns(7)
    for idx, name in enumerate(["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]):
        header[idx].markdown(f"<div style='text-align:center;color:#95A2B8;font-size:12px;font-weight:700'>{name}</div>", unsafe_allow_html=True)

    for week in cal:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            with cols[i]:
                if day_num == 0:
                    st.write("")
                    continue
                d = date(sel_month.year, sel_month.month, day_num)
                if d > today:
                    st.write("")
                    continue
                status = day_completeness(d.isoformat())
                icons = {"green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚫"}
                if st.button(f"{icons[status]} {day_num}", key=f"hist_{d.isoformat()}", use_container_width=True):
                    st.session_state.sel_date = d
                    st.session_state.page = "hoje"
                    st.rerun()
    st.caption("Clique num dia para abrir e editar retroativamente.")



def page_ia():
    st.markdown('<div class="section-title">IA e relatórios</div>', unsafe_allow_html=True)
    latest_labs = get_latest_labs()
    latest_bio = get_latest_bio()

    def build_context(days=14):
        start = (st.session_state.sel_date - timedelta(days=days - 1)).isoformat()
        weights = get_weight_history(days, end_dt=st.session_state.sel_date)
        meals_data = (
            db.table("meals")
            .select("date,meal_type,food_key,kcal,protein_g,carbs_g,fat_g")
            .gte("date", start)
            .lte("date", st.session_state.sel_date.isoformat())
            .order("date")
            .execute()
            .data
            or []
        )
        sleep_data = (
            db.table("sleep_cpap")
            .select("date,total_hours,ahi,energy_score,tiredness_score")
            .gte("date", start)
            .lte("date", st.session_state.sel_date.isoformat())
            .order("date")
            .execute()
            .data
            or []
        )
        checks = (
            db.table("checklist_daily")
            .select("date,item_key,done")
            .gte("date", start)
            .lte("date", st.session_state.sel_date.isoformat())
            .order("date")
            .execute()
            .data
            or []
        )
        return f"""
Paciente: João, 34 anos, 174cm. Objetivo: emagrecer preservando massa magra.
Janela analisada: {start} até {st.session_state.sel_date.isoformat()}.
Pesos: {json.dumps(weights, default=str)}
Refeições: {json.dumps(meals_data, default=str)}
Sono: {json.dumps(sleep_data, default=str)}
Checklist: {json.dumps(checks, default=str)}
Bio mais recente: {json.dumps(latest_bio, default=str)}
Exames mais recentes: {json.dumps(latest_labs, default=str)}
""".strip()

    st.markdown('<div class="soft-card"><span class="subtle">Aqui, sim, entram bioimpedância e exames quando fizer sentido. Na mensagem do dia, não.</span></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Últimos 7 dias", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 7 dias de forma prática e direta."})
            st.rerun()
    with c2:
        if st.button("Últimos 14 dias", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Compare meus últimos 14 dias e diga o principal gargalo."})
            st.rerun()

    for msg in st.session_state.chat_history:
        role_label = "Você" if msg["role"] == "user" else "IA"
        st.markdown(f"**{role_label}:** {msg['content']}")

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.spinner("Analisando..."):
            prompt = f"""
Você é o assistente de saúde pessoal de João.

{build_context(14)}

Responda à última mensagem do usuário de forma:
- direta
- prática
- sem clichês
- com foco em padrões do período
- sem repetir exame antigo à toa; use exame só se ele realmente ajudar a explicar o período
- no máximo 220 palavras

Pergunta do usuário: {st.session_state.chat_history[-1]['content']}
""".strip()
            try:
                answer = ai_text(prompt, max_output_tokens=420)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
                st.session_state.chat_history.pop()

    user_input = st.chat_input("Pergunte sobre seus dados...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.rerun()

    if st.session_state.chat_history and st.button("Limpar conversa", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


page_map = {
    "hoje": page_hoje,
    "alimentacao": page_alimentacao,
    "corpo": page_corpo,
    "historico": page_historico,
    "ia": page_ia,
}

page_map[st.session_state.page]()
nav_bar()
