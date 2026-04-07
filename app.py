from datetime import date, timedelta, datetime, time
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
        background: linear-gradient(180deg, #09101d 0%, #0d1220 100%);
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
        background: linear-gradient(135deg, rgba(21,51,42,0.92), rgba(18,25,43,0.98));
        border: 1px solid #24453b;
        color: #dbf9ea;
        border-radius: 16px;
        padding: 14px 16px;
        margin-top: 8px;
    }
    .analysis-box .t {font-size: 11px; text-transform: uppercase; letter-spacing: 1.1px; color: var(--green); font-weight: 800; margin-bottom: 8px;}
    .analysis-box ul {margin: 0; padding-left: 18px;}
    .analysis-box li {margin-bottom: 6px;}
    .calendar-note {font-size:12px; color:var(--muted); margin-top:10px;}
    .small-label {font-size:12px; color:var(--muted); margin-bottom:6px;}
    .streamlit-expanderHeader {font-size: 15px; font-weight: 700;}
    .stButton > button {min-height: 42px; border-radius: 12px;}
    .stNumberInput input, .stTextInput input {font-size: 16px !important;}
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
    query = db.table(table).select(select)
    for k, v in filters.items():
        query = query.eq(k, v)
    res = query.execute()
    return res.data or []


def get_goals():
    rows = q("goals", active=True)
    return {r["metric"]: r for r in rows}


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
    res = db.table("checklist_items").select("*").eq("active", True).order("sort_order").execute()
    return res.data or []


def get_checklist(dt):
    rows = q("checklist_daily", date=dt)
    return {r["item_key"]: r for r in rows}


def save_check(dt, key, done):
    db.table("checklist_daily").upsert({"date": dt, "item_key": key, "done": done}, on_conflict="date,item_key").execute()


def get_meals(dt):
    return q("meals", date=dt)


def get_foods():
    res = db.table("food_library").select("*").eq("active", True).order("name").execute()
    return res.data or []


def get_sleep(dt):
    rows = q("sleep_cpap", date=dt)
    return rows[0] if rows else {}


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
            "ovo_cozido", "whey_dose", "suco_verde", "leite_desnatado", "pao_integral",
            "banana", "aveia", "iogurte_grego", "cafe_puro", "queijo_branco"
        ],
    },
    "almoco": {
        "label": "🍚 Almoço",
        "foods": [
            "arroz_branco", "feijao_cozido", "arroz_feijao", "frango_grelhado", "patinho_moido",
            "carne_magra", "lombo_suino", "batata_cozida", "mandioca_cozida", "lentilha",
            "alface", "rucula", "tomate", "cenoura_crua", "beterraba", "chuchu", "vagem",
            "couve_cozida", "azeite", "agua", "refri_zero"
        ],
    },
    "lanche": {
        "label": "🥪 Lanche / pré-treino",
        "foods": [
            "pao_integral", "whey_dose", "iogurte_grego", "banana", "queijo_branco",
            "castanhas", "cafe_puro", "leite_desnatado", "requeijao_light", "aveia", "agua", "refri_zero"
        ],
    },
    "jantar": {
        "label": "🍽️ Jantar",
        "foods": [
            "macarrao_cozido", "arroz_branco", "frango_grelhado", "patinho_moido", "carne_magra",
            "hamburguer_caseiro", "mussarela", "pao_integral", "sopa_lentilha", "caldo_abobora",
            "alface", "rucula", "tomate", "cenoura_crua", "couve_cozida", "agua", "refri_zero"
        ],
    },
    "ceia": {
        "label": "🌙 Ceia",
        "foods": [
            "iogurte_grego", "whey_dose", "queijo_branco", "banana", "leite_desnatado", "castanhas", "agua"
        ],
    },
    "bebida": {
        "label": "🥤 Bebidas fora da refeição",
        "foods": [
            "agua", "cafe_puro", "refri_zero", "cerveja_lata", "cerveja_long", "cerveja_600",
            "vinho_taca", "destilado_dose", "chopp", "xeque_mate_lata", "aperol_spritz"
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


def food_status_class(kcal, prot, goals):
    kcal_goal = float(goals.get("kcal_daily", {}).get("target_value", 2067))
    protein_goal = float(goals.get("protein_daily", {}).get("target_value", 180))
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
        if t["kcal"] <= float(goals.get("kcal_daily", {}).get("target_value", 2067)) * 1.1:
            score += 35
        else:
            score += 18
        if t["prot"] >= float(goals.get("protein_daily", {}).get("target_value", 180)) * 0.85:
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


def build_day_review(dt_iso, goals, meals, checklist, sleep, weight):
    t = meal_totals(meals)
    kcal_goal = float(goals.get("kcal_daily", {}).get("target_value", 2067))
    protein_goal = float(goals.get("protein_daily", {}).get("target_value", 180))
    routine_items = [i for i in get_checklist_items() if is_routine_item(i)]
    done = sum(1 for i in routine_items if checklist.get(i["item_key"], {}).get("done"))
    total = len(routine_items)

    positives = []
    attentions = []
    actions = []

    if t["kcal"] == 0:
        attentions.append("Você ainda não registrou alimentação suficiente para ler o dia com segurança.")
        actions.append("Preencha as refeições antes de confiar na análise.")
    else:
        if t["kcal"] <= kcal_goal * 1.08:
            positives.append("As calorias do dia ficaram dentro de uma faixa coerente para o objetivo.")
        else:
            attentions.append("As calorias passaram do ponto para um dia de corte controlado.")
            actions.append("Amanhã concentre o ajuste na refeição que mais pesou no total do dia.")

        if t["prot"] >= protein_goal * 0.85:
            positives.append("A proteína do dia ficou em nível bom para preservar massa magra.")
        elif t["prot"] > 0:
            attentions.append("A proteína ficou abaixo do que seria ideal para o seu objetivo.")
            actions.append("Suba proteína com comida de verdade nas refeições principais, não só suplemento.")

        if len(meals) <= 2:
            attentions.append("O dia está com poucas refeições registradas e isso distorce a leitura.")
            actions.append("Registre todas as refeições, mesmo quando fugir do plano.")

        whey_count = sum(1 for m in meals if (m.get("food_key") or "") == "whey_dose")
        if whey_count >= 2:
            attentions.append("O dia ficou dependente demais de whey para fechar proteína.")
            actions.append("Distribua melhor a proteína com almoço e jantar mais fortes.")

    if sleep:
        total_hours = float(sleep.get("total_hours") or 0)
        energy = sleep.get("energy_score")
        if total_hours >= 7:
            positives.append("O sono da noite anterior já permite começar o dia com base melhor.")
        elif total_hours > 0:
            attentions.append("O sono veio curto e isso pode piorar fome, energia e aderência.")
            actions.append("Hoje vale evitar compensar cansaço com calorias líquidas ou belisco solto.")
        if energy is not None and int(energy) <= 3:
            attentions.append("Sua energia do dia está baixa, então o risco de desorganizar rotina sobe.")
    else:
        attentions.append("O sono da noite anterior ainda não foi registrado.")
        actions.append("Preencha o sono antes de fechar a leitura do dia.")

    if total:
        if done >= max(1, int(total * 0.8)):
            positives.append("A rotina de remédios e suplementos ficou bem executada.")
        elif done < max(1, int(total * 0.5)):
            attentions.append("A aderência da rotina ficou baixa no que era previsível executar.")
            actions.append("Use o checklist como fechamento do dia, não só como lembrete solto.")

    if weight is None:
        actions.append("Registre o peso do dia para manter o histórico consistente.")

    positives = positives[:2] or ["Você já tem alguns dados do dia salvos, o que é melhor do que operar no escuro."]
    attentions = attentions[:2] or ["Nada crítico apareceu no dia, mas ainda vale manter o registro completo."]
    actions = actions[:1] or ["O próximo passo é só repetir o básico sem abrir muitas exceções."]

    html = '<div class="analysis-box"><div class="t">Leitura do dia</div><ul>'
    html += f"<li><strong>Ponto positivo:</strong> {positives[0]}</li>"
    html += f"<li><strong>Ponto de atenção:</strong> {attentions[0]}</li>"
    html += f"<li><strong>Próximo ajuste:</strong> {actions[0]}</li>"
    html += "</ul></div>"
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
    st.markdown("---")
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
    hist = get_weight_history(30, end_date=end_date)
    if not hist:
        st.info("Ainda não há histórico suficiente de peso para o gráfico.")
        return
    df = pd.DataFrame(hist)
    df["date"] = pd.to_datetime(df["date"])
    df["weight_kg"] = df["weight_kg"].astype(float)
    df["meta"] = goal_weight
    df["media_7d"] = df["weight_kg"].rolling(7, min_periods=1).mean()
    st.line_chart(df.set_index("date")[["weight_kg", "meta", "media_7d"]], height=220, use_container_width=True)


# ==================================================
# PAGE: HOJE
# ==================================================
def page_hoje():
    target = date_bar()
    goals = get_goals()
    goal_weight = float(goals.get("weight", {}).get("target_value", 90))

    st.markdown('<div class="section-title">Resumo do dia</div>', unsafe_allow_html=True)
    current_weight = get_weight(target)
    c1, c2 = st.columns([2.4, 1])
    with c1:
        pv = float(current_weight or 143.0)
        weight_input = st.number_input("Peso do dia", 50.0, 250.0, pv, 0.1, format="%.1f", key="today_weight")
    with c2:
        st.write("")
        if st.button("Salvar peso", use_container_width=True, key="save_today_weight"):
            save_weight(target, weight_input)
            st.rerun()
    if current_weight is not None:
        remaining = current_weight - goal_weight
        st.markdown(f'<div class="card"><div class="big">{current_weight:.1f} kg</div><div class="muted">Meta {goal_weight:.0f} kg · faltam {remaining:.1f} kg</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Gráfico</div>', unsafe_allow_html=True)
    render_graph(st.session_state.sel_date, goal_weight)

    st.markdown('<div class="section-title">Sono da noite anterior</div>', unsafe_allow_html=True)
    sleep = get_sleep(target)
    page_sono_quick(target, sleep)

    st.markdown('<div class="section-title">Alimentação do dia</div>', unsafe_allow_html=True)
    meals = get_meals(target)
    totals = meal_totals(meals)
    macro_pills(totals["kcal"], totals["prot"], totals["carb"], totals["fat"])
    klass, label = food_status_class(totals["kcal"], totals["prot"], goals)
    if label:
        st.markdown(f'<span class="status {klass}">{label}</span>', unsafe_allow_html=True)
    if meals:
        for mk, mc in MEAL_CONFIG.items():
            mi = [m for m in meals if m["meal_type"] == mk]
            if not mi:
                continue
            mk_kcal = sum(float(m.get("kcal") or 0) for m in mi)
            names = ", ".join((m.get("food_key") or "").replace("_", " ") for m in mi)
            st.markdown(f'<div class="meal-card"><div class="meal-name">{mc["label"]} · {mk_kcal:.0f} kcal</div><div class="meal-detail">{names}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="meal-card"><div class="meal-detail">Nenhuma refeição registrada ainda.</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Rotina do dia</div>', unsafe_allow_html=True)
    checklist_items = [i for i in get_checklist_items() if is_routine_item(i)]
    checklist = get_checklist(target)
    slots = {
        "jejum": "☀️ Jejum",
        "manha": "Manhã",
        "almoco": "Almoço",
        "jantar": "Jantar",
        "noite": "Noite",
        "variavel": "Variável",
    }
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
    st.markdown(build_day_review(target, goals, meals, checklist, sleep, current_weight), unsafe_allow_html=True)


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
    foods = get_foods()
    food_map = {f["food_key"]: f for f in foods}
    all_meals = get_meals(target)
    goals = get_goals()
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
    trained = st.checkbox("Treinei hoje", value=treino_done, key=f"trained_{target}")
    if trained != treino_done:
        save_check(target, "treino", trained)
        st.rerun()
    if trained:
        when = st.radio("Horário", ["Manhã", "Tarde", "Fim de semana"], horizontal=True, key=f"train_when_{target}")
        obs = st.text_area("O que treinou / observações", height=80, key=f"train_obs_{target}")
        st.caption(f"Treino marcado como feito · {when}")
    else:
        st.caption("Sem treino marcado nessa data.")


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
    st.markdown("<div class='calendar-note'>Clique em um dia para abrir, completar ou corrigir retroativamente.</div>", unsafe_allow_html=True)


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
    bio = db.table("bioimpedance").select("*").order("date", desc=True).limit(1).execute().data or []
    labs = db.table("lab_results").select("*").order("date", desc=True).limit(1).execute().data or []
    return f"""
Contexto do usuário:
- Homem, 34 anos, 174 cm.
- Objetivo: emagrecer preservando massa magra.
- Janela analisada: {start} até {end_s}.

Peso: {json.dumps(weights, default=str)}
Refeições: {json.dumps(meals, default=str)}
Sono: {json.dumps(sleep, default=str)}
Checklist: {json.dumps(checks, default=str)}
Bio mais recente: {json.dumps(bio, default=str)}
Exames mais recentes: {json.dumps(labs, default=str)}
"""


def page_ia():
    st.markdown('<div class="section-title">IA / perguntas</div>', unsafe_allow_html=True)
    st.caption("A IA faz mais sentido para analisar período, comparar padrões e interpretar exames. A leitura do dia fica na tela Hoje.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Analisar últimos 7 dias", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 7 dias de forma direta e prática."})
    with c2:
        if st.button("Onde estou errando?", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Onde estou errando? O que devo corrigir primeiro?"})

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='card card-tight'><strong>Você</strong><div class='muted'>{msg['content']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='analysis-box'><div class='t'>IA</div>{msg['content']}</div>", unsafe_allow_html=True)

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.spinner("Analisando seus dados..."):
            ctx = build_context(14)
            system = """Você é um assistente analítico de saúde pessoal. Seja direto, prático e nada coach. Use o contexto de período. Não repita exame antigo em toda resposta sem motivo. Não invente fatos. Estruture em: leitura objetiva, principal gargalo, próximo ajuste."""
            user = ctx + "\n\nPergunta do usuário: " + st.session_state.chat_history[-1]["content"]
            result = ask_openai(system, user, max_tokens=500)
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
