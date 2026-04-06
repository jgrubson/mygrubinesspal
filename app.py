import streamlit as st
from supabase import create_client
from datetime import date, timedelta, datetime
import pandas as pd
import json
from openai import OpenAI

# ============================================
# CONEXÃO
# ============================================
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_resource
def get_openai():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

db = get_supabase()
ai = get_openai()

# ============================================
# CONFIG
# ============================================
st.set_page_config(page_title="MyGrubinessPal", page_icon="💪", layout="centered", initial_sidebar_state="collapsed")

# ============================================
# CSS
# ============================================
st.markdown("""
<style>
    /* Reset */
    .block-container { padding-top: 0.25rem; padding-bottom: 5rem; max-width: 600px; }
    #MainMenu, footer, header { visibility: hidden; }

    /* Date bar */
    .date-bar {
        background: #161921;
        border-radius: 12px;
        padding: 8px 4px;
        margin-bottom: 16px;
        text-align: center;
        border: 1px solid #2D3139;
    }
    .date-bar .date-label {
        font-size: 15px;
        font-weight: 600;
        color: #FAFAFA;
    }
    .date-bar .date-sub {
        font-size: 12px;
        color: #666;
    }

    /* Cards */
    .card {
        background: #161921;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #2D3139;
    }
    .card-header {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .card-big {
        font-size: 32px;
        font-weight: 700;
        color: #FAFAFA;
        line-height: 1.1;
    }
    .card-sub {
        font-size: 13px;
        color: #888;
        margin-top: 4px;
    }

    /* Macro row */
    .macro-row {
        display: flex;
        gap: 6px;
        margin: 8px 0;
    }
    .mp {
        background: #1E2128;
        border-radius: 10px;
        padding: 10px 6px;
        text-align: center;
        flex: 1;
    }
    .mp .l { font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
    .mp .v { font-size: 20px; font-weight: 700; color: #FAFAFA; }

    /* Badges */
    .bg { padding: 4px 14px; border-radius: 20px; font-size: 13px; display: inline-block; margin: 4px 0; }
    .bg-g { background: #1B3A1B; color: #81C784; }
    .bg-y { background: #3A3200; color: #FFD54F; }
    .bg-r { background: #3A1B1B; color: #E57373; }
    .bg-b { background: #1B2A3A; color: #64B5F6; }

    /* Section titles */
    .section-title {
        font-size: 13px;
        font-weight: 700;
        color: #4CAF50;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 20px 0 8px 0;
        padding-bottom: 4px;
        border-bottom: 1px solid #2D3139;
    }

    /* Meal card */
    .meal-card {
        background: #161921;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 8px;
        border-left: 3px solid #4CAF50;
    }
    .meal-card.empty { border-left-color: #333; }
    .meal-name { font-weight: 600; color: #FAFAFA; font-size: 14px; }
    .meal-detail { font-size: 12px; color: #888; margin-top: 2px; }

    /* Calendar */
    .cal-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
        margin: 8px 0;
    }
    .cal-day {
        aspect-ratio: 1;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
    }
    .cal-header {
        font-size: 11px;
        color: #666;
        text-align: center;
        padding: 4px 0;
        font-weight: 600;
    }
    .cal-green { background: #1B3A1B; color: #81C784; }
    .cal-yellow { background: #3A3200; color: #FFD54F; }
    .cal-red { background: #3A1B1B; color: #E57373; }
    .cal-gray { background: #1A1D23; color: #444; }
    .cal-today { outline: 2px solid #4CAF50; outline-offset: -2px; }
    .cal-empty { background: transparent; }

    /* Chat */
    .chat-msg {
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        font-size: 14px;
        line-height: 1.5;
    }
    .chat-user {
        background: #1B3A1B;
        color: #C8E6C9;
        margin-left: 40px;
    }
    .chat-ai {
        background: #161921;
        color: #E0E0E0;
        margin-right: 20px;
        border: 1px solid #2D3139;
    }

    /* AI message of the day */
    .ai-msg {
        background: linear-gradient(135deg, #1a2a1a, #161921);
        border-radius: 12px;
        padding: 14px 16px;
        margin: 8px 0;
        border: 1px solid #2D3139;
        font-size: 14px;
        color: #C8E6C9;
        line-height: 1.5;
    }
    .ai-msg .ai-label {
        font-size: 11px;
        color: #4CAF50;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }

    /* Mobile touch targets */
    .stButton > button { min-height: 44px; }
    .stCheckbox label { font-size: 15px; padding: 4px 0; }
    .stNumberInput input { font-size: 16px !important; }

    /* Nav active state */
    div[data-testid="stHorizontalBlock"] > div > div > button[kind="primary"] {
        border-bottom: 3px solid #4CAF50;
    }

    /* Expander cleaner */
    .streamlit-expanderHeader { font-size: 15px; font-weight: 600; }
    .streamlit-expanderContent { padding-top: 0; }
</style>
""", unsafe_allow_html=True)

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
# DATE BAR — TOPO DE TODAS AS TELAS
# ============================================
def date_bar():
    d = st.session_state.sel_date
    c1, c2, c3, c4, c5 = st.columns([1, 1, 3, 1, 1])
    with c1:
        if st.button("◀", key=f"db_prev_{st.session_state.page}", use_container_width=True, help="Dia anterior"):
            st.session_state.sel_date -= timedelta(days=1)
            st.rerun()
    with c2:
        if d != date.today():
            if st.button("Hoje", key=f"db_today_{st.session_state.page}", use_container_width=True):
                st.session_state.sel_date = date.today()
                st.rerun()
    with c3:
        new_d = st.date_input("d", value=d, label_visibility="collapsed", key=f"db_cal_{st.session_state.page}")
        if new_d != d:
            st.session_state.sel_date = new_d
            st.rerun()
    with c4:
        pass
    with c5:
        if st.button("▶", key=f"db_next_{st.session_state.page}", use_container_width=True, help="Próximo dia"):
            st.session_state.sel_date += timedelta(days=1)
            st.rerun()

    dias_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    if d == date.today():
        label = f"Hoje — {d.strftime('%d/%m/%Y')}"
    elif d == date.today() - timedelta(days=1):
        label = f"Ontem — {d.strftime('%d/%m/%Y')}"
    else:
        label = f"{dias_pt[d.weekday()]} — {d.strftime('%d/%m/%Y')}"
    st.markdown(f'<div class="date-bar"><div class="date-label">{label}</div></div>', unsafe_allow_html=True)
    return d.isoformat()

# ============================================
# DATA FUNCTIONS
# ============================================
def q(table, select="*", **filters):
    """Query helper."""
    query = db.table(table).select(select)
    for k, v in filters.items():
        query = query.eq(k, v)
    r = query.execute()
    return r.data or []

def get_goals():
    r = q("goals", active=True)
    return {g["metric"]: g for g in r}

def get_weight_history(days=30):
    start = (date.today() - timedelta(days=days)).isoformat()
    r = db.table("daily_weight").select("date,weight_kg").gte("date", start).order("date").execute()
    return r.data or []

def get_weight(dt):
    r = q("daily_weight", date=dt)
    return float(r[0]["weight_kg"]) if r else None

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
    r = q("meals", date=dt)
    return r

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

def day_completeness(dt):
    """Retorna nível de preenchimento do dia: green/yellow/red/gray."""
    score = 0
    if get_weight(dt): score += 1
    meals = get_meals(dt)
    if len(meals) >= 3: score += 2
    elif len(meals) >= 1: score += 1
    ck = get_checklist(dt)
    done_count = sum(1 for v in ck.values() if v.get("done"))
    if done_count >= 8: score += 2
    elif done_count >= 4: score += 1
    sleep = get_sleep(dt)
    if sleep: score += 1
    if score >= 5: return "green"
    if score >= 3: return "yellow"
    if score >= 1: return "red"
    return "gray"

# ============================================
# MACROS HTML
# ============================================
def macro_pills(kcal, prot, carb, fat):
    st.markdown(
        f'<div class="macro-row">'
        f'<div class="mp"><div class="l">kcal</div><div class="v">{kcal:.0f}</div></div>'
        f'<div class="mp"><div class="l">prot</div><div class="v">{prot:.0f}g</div></div>'
        f'<div class="mp"><div class="l">carb</div><div class="v">{carb:.0f}g</div></div>'
        f'<div class="mp"><div class="l">gord</div><div class="v">{fat:.0f}g</div></div>'
        f'</div>', unsafe_allow_html=True)

def food_status(kcal, prot, goals):
    kg = float(goals.get("kcal_daily", {}).get("target_value", 2067))
    pg = float(goals.get("protein_daily", {}).get("target_value", 180))
    if kcal == 0:
        return
    if kcal <= kg * 1.1 and prot >= pg * 0.9:
        st.markdown('<span class="bg bg-g">🟢 Dia coerente com a estratégia</span>', unsafe_allow_html=True)
    elif kcal <= kg * 1.25 or prot >= pg * 0.7:
        st.markdown('<span class="bg bg-y">🟡 Revise calorias ou proteína</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="bg bg-r">🔴 Dia fora da estratégia</span>', unsafe_allow_html=True)

# ============================================
# MEAL SUGGESTIONS PER TIME
# ============================================
MEAL_CONFIG = {
    "cafe": {
        "label": "☕ Café da manhã",
        "foods": ["ovo_cozido", "whey_dose", "suco_verde", "leite_desnatado", "pao_integral",
                  "banana", "aveia", "iogurte_grego", "cafe_puro", "queijo_branco"]
    },
    "almoco": {
        "label": "🍚 Almoço",
        "foods": ["arroz_branco", "feijao_cozido", "arroz_feijao", "frango_grelhado", "patinho_moido",
                  "carne_magra", "lombo_suino", "batata_cozida", "mandioca_cozida", "lentilha",
                  "alface", "rucula", "tomate", "cenoura_crua", "beterraba", "chuchu", "vagem",
                  "couve_cozida", "azeite", "agua", "refri_zero"]
    },
    "lanche": {
        "label": "🥪 Lanche / Pré-treino",
        "foods": ["pao_integral", "whey_dose", "iogurte_grego", "banana", "queijo_branco",
                  "castanhas", "cafe_puro", "leite_desnatado", "requeijao_light", "aveia"]
    },
    "jantar": {
        "label": "🍽️ Jantar",
        "foods": ["macarrao_cozido", "arroz_branco", "frango_grelhado", "patinho_moido", "carne_magra",
                  "hamburguer_caseiro", "mussarela", "pao_integral", "sopa_lentilha", "caldo_abobora",
                  "alface", "rucula", "tomate", "cenoura_crua", "couve_cozida", "azeite", "agua", "refri_zero"]
    },
    "ceia": {
        "label": "🌙 Ceia",
        "foods": ["iogurte_grego", "whey_dose", "queijo_branco", "banana", "leite_desnatado", "castanhas"]
    },
    "bebida": {
        "label": "🍺 Bebidas",
        "foods": ["cerveja_lata", "cerveja_long", "cerveja_600", "vinho_taca", "destilado_dose",
                  "chopp", "xeque_mate_lata", "aperol_spritz", "agua", "cafe_puro", "refri_zero"]
    },
}

# Items to exclude from checklist (they live in Alimentação only)
FOOD_ONLY_KEYS = {"suco_verde", "whey"}

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
            if st.button(f"{icon} {label}", key=f"n_{key}", use_container_width=True, type=tp):
                st.session_state.page = key
                st.rerun()

# ============================================
# PAGE: HOJE
# ============================================
def page_hoje():
    target = date_bar()
    goals = get_goals()
    wg = float(goals.get("weight", {}).get("target_value", 90))

    # --- Peso ---
    st.markdown('<div class="section-title">⚖️ Peso</div>', unsafe_allow_html=True)
    cw = get_weight(target)
    c1, c2 = st.columns([3, 1])
    with c1:
        pv = cw if cw else 143.0
        peso = st.number_input("kg", 50.0, 250.0, pv, 0.1, "%.1f", key="ph", label_visibility="collapsed")
    with c2:
        if st.button("💾", key="sp", use_container_width=True):
            save_weight(target, peso)
            st.rerun()
    if cw:
        diff = cw - wg
        st.markdown(f'<div class="card"><div class="card-big">{cw:.1f} kg</div>'
                    f'<div class="card-sub">Meta {wg:.0f} kg · faltam {diff:.1f} kg</div></div>', unsafe_allow_html=True)

    # Mini gráfico
    hist = get_weight_history(30)
    if len(hist) > 1:
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"])
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["meta"] = wg
        st.line_chart(df.set_index("date")[["weight_kg", "meta"]], height=150, use_container_width=True)

    # --- Alimentação resumo ---
    st.markdown('<div class="section-title">🍽️ Alimentação</div>', unsafe_allow_html=True)
    meals = get_meals(target)
    if meals:
        t = meal_totals(meals)
        macro_pills(t["kcal"], t["prot"], t["carb"], t["fat"])
        food_status(t["kcal"], t["prot"], goals)
        # Resumo por refeição
        for mk, mc in MEAL_CONFIG.items():
            mi = [m for m in meals if m["meal_type"] == mk]
            if mi:
                mk_kcal = sum(float(m.get("kcal") or 0) for m in mi)
                names = ", ".join(m.get("food_key", "").replace("_", " ") for m in mi)
                st.markdown(f'<div class="meal-card"><div class="meal-name">{mc["label"]} · {mk_kcal:.0f} kcal</div>'
                           f'<div class="meal-detail">{names}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="meal-card empty"><div class="meal-detail">Nenhuma refeição registrada</div></div>',
                   unsafe_allow_html=True)

    # --- Checklist ---
    st.markdown('<div class="section-title">💊 Rotina do dia</div>', unsafe_allow_html=True)
    items = get_checklist_items()
    daily = get_checklist(target)
    items = [i for i in items if i["item_key"] not in FOOD_ONLY_KEYS]

    slots = {"jejum": "☀️ Jejum", "manha": "Manhã", "almoco": "Almoço",
             "jantar": "Jantar", "noite": "Noite", "variavel": "Variável"}
    cur_slot = ""
    done_count = 0
    total_count = len(items)

    for item in items:
        s = item["time_slot"]
        if s != cur_slot:
            cur_slot = s
            st.markdown(f"**{slots.get(s, s)}**")
        checked = daily.get(item["item_key"], {}).get("done", False)
        if checked: done_count += 1
        dose = f" · {item['dosage']}" if item.get("dosage") else ""
        lbl = f"{item['name']}{dose}"
        if item.get("instruction"):
            lbl += f"  \n↳ _{item['instruction']}_"
        nv = st.checkbox(lbl, value=checked, key=f"c_{item['item_key']}_{target}")
        if nv != checked:
            save_check(target, item["item_key"], nv)

    if total_count > 0:
        pct = done_count / total_count * 100
        st.caption(f"Aderência: {done_count}/{total_count} ({pct:.0f}%)")

    # --- Sono resumo ---
    st.markdown('<div class="section-title">😴 Sono</div>', unsafe_allow_html=True)
    sleep = get_sleep(target)
    if sleep:
        hrs = sleep.get("total_hours") or "—"
        ahi_v = sleep.get("ahi") or "—"
        en = sleep.get("energy_score") or "—"
        st.markdown(f'<div class="card"><div class="card-sub">{hrs}h de sono · AHI {ahi_v} · Energia {en}/10</div></div>',
                   unsafe_allow_html=True)
    else:
        st.caption("Sono não registrado.")

    # --- Fechamento do dia ---
    st.markdown('<div class="section-title">💬 Mensagem do dia</div>', unsafe_allow_html=True)
    if st.button("Gerar análise do dia", key="gen_msg", use_container_width=True):
        with st.spinner("Analisando seu dia..."):
            msg = generate_day_message(target, goals, meals, daily, sleep, cw)
            st.markdown(f'<div class="ai-msg"><div class="ai-label">IA · Análise do dia</div>{msg}</div>',
                       unsafe_allow_html=True)


def generate_day_message(target, goals, meals, checklist, sleep, weight):
    """Gera mensagem de análise do dia usando OpenAI."""
    t = meal_totals(meals) if meals else {"kcal": 0, "prot": 0, "carb": 0, "fat": 0}
    done = sum(1 for v in checklist.values() if v.get("done"))
    total_items = len([i for i in get_checklist_items() if i["item_key"] not in FOOD_ONLY_KEYS])

    context = f"""Dados do dia {target} de João (34 anos, 174cm, objetivo: emagrecer de 143kg para 90kg preservando massa magra):
- Peso: {weight or 'não registrado'} kg
- Meta calórica: {goals.get('kcal_daily', {}).get('target_value', 2067)} kcal
- Meta proteína: {goals.get('protein_daily', {}).get('target_value', 180)} g
- Calorias consumidas: {t['kcal']:.0f} kcal
- Proteína: {t['prot']:.0f}g | Carb: {t['carb']:.0f}g | Gordura: {t['fat']:.0f}g
- Refeições registradas: {len(meals)}
- Checklist: {done}/{total_items} itens completados
- Sono: {'registrado' if sleep else 'não registrado'}
- Quadro clínico: resistência insulínica (HOMA-IR 4.17), TSH 8.14, triglicérides 313, testosterona 202, gordura visceral 31
- Medicações: Euthyrox 25mcg, Sertralina 200mg, Pantoprazol, Rosucor EZE, Lipidil 160mg, Trazodona 50mg
- Suplementos: B12, Creatina, Vitamina D 5000UI, Magnésio, Ômega-3"""

    try:
        response = ai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """Você é um assistente de saúde pessoal de João. Seja direto, prático, crítico quando necessário.
Não use linguagem de coach. Não use clichês. Não seja genérico. Use os dados concretos dele.
Fale em português do Brasil. Máximo 4 frases curtas. Destaque 1 ponto positivo e 1 ponto de atenção.
Se os dados estão incompletos, diga isso diretamente. Não invente dados."""},
                {"role": "user", "content": context}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao gerar análise: {str(e)}"


# ============================================
# PAGE: ALIMENTAÇÃO
# ============================================
def page_alimentacao():
    target = date_bar()
    st.markdown('<div class="section-title">🍽️ Alimentação do dia</div>', unsafe_allow_html=True)

    foods = get_foods()
    food_map = {f["food_key"]: f for f in foods}
    food_names = {f["food_key"]: f["name"] for f in foods}
    goals = get_goals()
    all_meals = get_meals(target)

    # Totais no topo
    t = meal_totals(all_meals)
    macro_pills(t["kcal"], t["prot"], t["carb"], t["fat"])
    food_status(t["kcal"], t["prot"], goals)

    kg = float(goals.get("kcal_daily", {}).get("target_value", 2067))
    pg = float(goals.get("protein_daily", {}).get("target_value", 180))
    if t["kcal"] > 0:
        st.caption(f"Calorias: {t['kcal']/kg*100:.0f}% · Proteína: {t['prot']/pg*100:.0f}%")

    # Refeições
    for mk, mc in MEAL_CONFIG.items():
        mi = [m for m in all_meals if m["meal_type"] == mk]
        mk_kcal = sum(float(m.get("kcal") or 0) for m in mi)
        hdr = mc["label"]
        if mi:
            hdr += f"  ·  {mk_kcal:.0f} kcal"

        with st.expander(hdr, expanded=False):
            # Items registered
            if mi:
                for m in mi:
                    fn = food_names.get(m["food_key"], m["food_key"])
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"**{fn}** · {float(m['quantity_g']):.0f}g  \n"
                                   f"_{float(m.get('kcal') or 0):.0f}kcal · P:{float(m.get('protein_g') or 0):.0f}g · "
                                   f"C:{float(m.get('carbs_g') or 0):.0f}g · G:{float(m.get('fat_g') or 0):.0f}g_")
                    with c2:
                        if st.button("✕", key=f"d_{m['id']}"):
                            db.table("meals").delete().eq("id", m["id"]).execute()
                            st.rerun()

            # Add item
            sug = mc["foods"]
            fs = [f for f in foods if f["food_key"] in sug]
            fo = [f for f in foods if f["food_key"] not in sug]

            ok = [""] + [f["food_key"] for f in fs]
            ol = ["+ Adicionar alimento..."] + [f["name"] for f in fs]
            if fo:
                ok.append("__s__")
                ol.append("── Todos ──")
                for f in fo:
                    ok.append(f["food_key"])
                    ol.append(f["name"])

            sel = st.selectbox("add", ok, format_func=lambda x: ol[ok.index(x)],
                              key=f"s_{mk}_{target}", label_visibility="collapsed")

            if sel and sel != "__s__":
                fd = food_map[sel]
                dg = float(fd["default_portion_g"])
                qty = st.number_input(f"Gramas (porção padrão: {dg:.0f}g)", 1.0, 5000.0, dg, 10.0,
                                      key=f"q_{mk}_{target}")
                fac = qty / 100
                ek = float(fd["kcal_per_100g"]) * fac
                ep = float(fd["protein_per_100g"]) * fac
                ec = float(fd["carbs_per_100g"]) * fac
                ef = float(fd["fat_per_100g"]) * fac
                st.caption(f"→ {ek:.0f} kcal · P:{ep:.0f}g · C:{ec:.0f}g · G:{ef:.0f}g")

                if st.button("✅ Adicionar", key=f"a_{mk}_{target}", use_container_width=True):
                    db.table("meals").insert({
                        "date": target, "meal_type": mk, "food_key": sel,
                        "quantity_g": qty, "portions": qty/dg,
                        "kcal": ek, "protein_g": ep, "carbs_g": ec, "fat_g": ef
                    }).execute()
                    st.rerun()


# ============================================
# PAGE: CORPO & SONO
# ============================================
def page_corpo():
    target = date_bar()
    tab = st.radio("", ["⚖️ Peso", "😴 Sono", "🏋️ Treino", "🔬 Bio/Exames"],
                   horizontal=True, label_visibility="collapsed", key="corpo_tab")

    if tab == "⚖️ Peso":
        page_peso_inner(target)
    elif tab == "😴 Sono":
        page_sono_inner(target)
    elif tab == "🏋️ Treino":
        page_treino_inner(target)
    elif tab == "🔬 Bio/Exames":
        page_bio_inner(target)


def page_peso_inner(target):
    st.markdown('<div class="section-title">⚖️ Peso e Medidas</div>', unsafe_allow_html=True)
    goals = get_goals()
    wg = float(goals.get("weight", {}).get("target_value", 90))

    # Gráfico
    period = st.selectbox("Período", ["30 dias", "60 dias", "90 dias", "Tudo"], key="pp")
    dm = {"30 dias": 30, "60 dias": 60, "90 dias": 90, "Tudo": 3650}
    hist = get_weight_history(dm[period])
    if hist:
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"])
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["meta"] = wg
        st.line_chart(df.set_index("date")[["weight_kg", "meta"]], height=250)

    # Registrar
    with st.expander("📝 Registrar peso"):
        dt = st.date_input("Data", value=st.session_state.sel_date, key="dpr")
        p = st.number_input("kg", 50.0, 250.0, 143.0, 0.1, key="pr")
        if st.button("💾 Salvar", key="spr", use_container_width=True):
            save_weight(dt.isoformat(), p)
            st.success("✓")

    # Medidas
    with st.expander("📏 Registrar medidas"):
        dm = st.date_input("Data", value=st.session_state.sel_date, key="dmr")
        c1, c2 = st.columns(2)
        with c1:
            cin = st.number_input("Cintura", 0.0, 250.0, 0.0, 0.5, key="c1m")
            abd = st.number_input("Abdômen", 0.0, 250.0, 0.0, 0.5, key="c2m")
            pei = st.number_input("Peito", 0.0, 250.0, 0.0, 0.5, key="c3m")
        with c2:
            bra = st.number_input("Braço", 0.0, 100.0, 0.0, 0.5, key="c4m")
            cox = st.number_input("Coxa", 0.0, 150.0, 0.0, 0.5, key="c5m")
            qua = st.number_input("Quadril", 0.0, 250.0, 0.0, 0.5, key="c6m")
        if st.button("💾 Salvar medidas", key="smr", use_container_width=True):
            db.table("measurements").insert({
                "date": dm.isoformat(), "waist_cm": cin or None, "abdomen_cm": abd or None,
                "chest_cm": pei or None, "arm_cm": bra or None,
                "thigh_cm": cox or None, "hip_cm": qua or None
            }).execute()
            st.success("✓")

    # Últimos pesos
    if hist:
        st.markdown("**Últimos registros**")
        for h in reversed(hist[-7:]):
            c1, c2 = st.columns([4, 1])
            c1.caption(f"{h['date']} → {h['weight_kg']} kg")
            with c2:
                if st.button("✕", key=f"dw_{h['date']}"):
                    db.table("daily_weight").delete().eq("date", h["date"]).execute()
                    st.rerun()


def page_sono_inner(target):
    st.markdown('<div class="section-title">😴 Sono / CPAP</div>', unsafe_allow_html=True)
    data = get_sleep(target)

    with st.form("fs"):
        c1, c2 = st.columns(2)
        with c1:
            bt = st.time_input("Dormiu às", value=None, key="bt")
            th = st.number_input("Horas totais", 0.0, 16.0, float(data.get("total_hours") or 0), 0.5)
            uc = st.checkbox("Usou CPAP?", value=bool(data.get("used_cpap", True)))
            ch = st.number_input("Horas CPAP", 0.0, 16.0, float(data.get("cpap_hours") or 0), 0.5)
        with c2:
            wt = st.time_input("Acordou às", value=None, key="wt")
            ahi = st.number_input("AHI", 0.0, 100.0, float(data.get("ahi") or 0), 0.1)
            lr = st.number_input("Vazamento", 0.0, 100.0, float(data.get("leak_rate") or 0), 0.1)
            mo = ["boa", "regular", "ruim"]
            ms = st.selectbox("Vedação", mo, index=mo.index(data.get("mask_seal") or "boa"))

        rm = st.checkbox("Tirou a máscara?", value=bool(data.get("removed_mask", False)))
        ev = st.number_input("Eventos/hora", 0.0, 100.0, float(data.get("events_per_hour") or 0), 0.1)

        c1, c2 = st.columns(2)
        with c1:
            ts = st.slider("Cansaço (0=exausto, 10=descansado)", 0, 10, int(data.get("tiredness_score") or 5))
        with c2:
            es = st.slider("Energia (0=zero, 10=máxima)", 0, 10, int(data.get("energy_score") or 5))
        nt = st.text_area("Observações", value=data.get("notes") or "", height=60)

        if st.form_submit_button("💾 Salvar", use_container_width=True):
            db.table("sleep_cpap").upsert({
                "date": target, "bed_time": bt.isoformat() if bt else None,
                "wake_time": wt.isoformat() if wt else None,
                "total_hours": th, "used_cpap": uc, "cpap_hours": ch, "ahi": ahi,
                "leak_rate": lr, "mask_seal": ms, "removed_mask": rm,
                "events_per_hour": ev, "tiredness_score": ts, "energy_score": es, "notes": nt
            }, on_conflict="date").execute()
            st.success("✓")


def page_treino_inner(target):
    st.markdown('<div class="section-title">🏋️ Treino</div>', unsafe_allow_html=True)
    ck = get_checklist(target)
    treino_done = ck.get("treino", {}).get("done", False)

    treinou = st.checkbox("Treinei hoje", value=treino_done, key="tr_done")
    if treinou != treino_done:
        save_check(target, "treino", treinou)

    if treinou:
        horario = st.radio("Horário", ["Manhã (7h)", "Tarde", "Fim de semana (10-11h)"],
                          horizontal=True, key="tr_hor")
        obs = st.text_area("O que treinou / observações", height=80, key="tr_obs",
                          placeholder="Ex: Peito e tríceps, 1h15min")
        st.caption("Registro de treino detalhado será expandido nas próximas versões.")


def page_bio_inner(target):
    st.markdown('<div class="section-title">🔬 Bioimpedância e Exames</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Bioimpedância", "Exames"])

    with tab1:
        with st.expander("➕ Nova bioimpedância"):
            with st.form("fb"):
                dt = st.date_input("Data", key="bdt")
                c1, c2 = st.columns(2)
                with c1:
                    bw = st.number_input("Peso (kg)", 50.0, 250.0, 143.0, 0.1, key="bw")
                    bf = st.number_input("% Gordura", 0.0, 80.0, 50.0, 0.1, key="bf")
                    bv = st.number_input("Gordura visceral", 0, 60, 31, key="bv")
                with c2:
                    bm = st.number_input("Musc. esquelética (kg)", 0.0, 100.0, 39.0, 0.1, key="bm")
                    bff = st.number_input("Massa livre gord. (kg)", 0.0, 150.0, 64.0, 0.1, key="bff")
                    bb = st.number_input("TMB (kcal)", 0.0, 5000.0, 2681.0, 1.0, key="bb")
                bn = st.text_area("Observação", key="bn", height=60)
                if st.form_submit_button("💾 Salvar"):
                    db.table("bioimpedance").insert({
                        "date": dt.isoformat(), "weight_kg": bw, "fat_pct": bf,
                        "visceral_fat": bv, "skeletal_muscle_kg": bm,
                        "fat_free_mass_kg": bff, "bmr_kcal": bb, "notes": bn
                    }).execute()
                    st.success("✓")

        bios = db.table("bioimpedance").select("*").order("date", desc=True).limit(5).execute()
        if bios.data:
            st.markdown("**Histórico**")
            for b in bios.data:
                st.markdown(f'<div class="card"><div class="card-sub">'
                           f'📅 {b["date"]} · {b["weight_kg"]}kg · Gord {b["fat_pct"]}% · '
                           f'Visc {b["visceral_fat"]} · Musc {b["skeletal_muscle_kg"]}kg · '
                           f'TMB {b["bmr_kcal"]}kcal</div></div>', unsafe_allow_html=True)

    with tab2:
        with st.expander("➕ Novos exames"):
            with st.form("fl"):
                dt = st.date_input("Data", key="ldt")
                c1, c2, c3 = st.columns(3)
                with c1:
                    gl = st.number_input("Glicose", 0.0, 500.0, 0.0, 1.0, key="lg")
                    ha = st.number_input("HbA1c", 0.0, 15.0, 0.0, 0.1, key="lh")
                    ins = st.number_input("Insulina", 0.0, 100.0, 0.0, 0.1, key="li")
                    hm = st.number_input("HOMA-IR", 0.0, 20.0, 0.0, 0.01, key="lhm")
                    tsh = st.number_input("TSH", 0.0, 50.0, 0.0, 0.01, key="lt")
                with c2:
                    t4 = st.number_input("T4 livre", 0.0, 10.0, 0.0, 0.01, key="lt4")
                    tri = st.number_input("Triglicérides", 0.0, 1000.0, 0.0, 1.0, key="ltr")
                    ggt = st.number_input("GGT", 0.0, 500.0, 0.0, 1.0, key="lgg")
                    ct = st.number_input("Col. total", 0.0, 500.0, 0.0, 1.0, key="lct")
                    ldl = st.number_input("LDL", 0.0, 300.0, 0.0, 1.0, key="ll")
                with c3:
                    hdl = st.number_input("HDL", 0.0, 150.0, 0.0, 1.0, key="lhdl")
                    mg = st.number_input("Magnésio", 0.0, 10.0, 0.0, 0.1, key="lmg")
                    b12 = st.number_input("B12", 0.0, 2000.0, 0.0, 1.0, key="lb12")
                    vd = st.number_input("Vit. D", 0.0, 150.0, 0.0, 0.1, key="lvd")
                    tes = st.number_input("Testosterona", 0.0, 1500.0, 0.0, 1.0, key="ltes")
                ln = st.text_area("Observação", key="ln", height=60)
                if st.form_submit_button("💾 Salvar"):
                    db.table("lab_results").insert({
                        "date": dt.isoformat(), "glucose": gl or None, "hba1c": ha or None,
                        "insulin": ins or None, "homa_ir": hm or None, "tsh": tsh or None,
                        "t4_free": t4 or None, "triglycerides": tri or None, "ggt": ggt or None,
                        "total_cholesterol": ct or None, "ldl": ldl or None, "hdl": hdl or None,
                        "magnesium": mg or None, "b12": b12 or None, "vitamin_d": vd or None,
                        "testosterone": tes or None, "notes": ln
                    }).execute()
                    st.success("✓")

        labs = db.table("lab_results").select("*").order("date", desc=True).limit(3).execute()
        if labs.data:
            st.markdown("**Últimos exames**")
            for l in labs.data:
                parts = []
                if l.get("glucose"): parts.append(f"Glic {l['glucose']}")
                if l.get("hba1c"): parts.append(f"HbA1c {l['hba1c']}")
                if l.get("tsh"): parts.append(f"TSH {l['tsh']}")
                if l.get("triglycerides"): parts.append(f"Trig {l['triglycerides']}")
                if l.get("testosterone"): parts.append(f"Testo {l['testosterone']}")
                st.caption(f"📅 {l['date']} · {' · '.join(parts)}")


# ============================================
# PAGE: HISTÓRICO (CALENDÁRIO)
# ============================================
def page_historico():
    st.markdown('<div class="section-title">📅 Histórico</div>', unsafe_allow_html=True)

    # Month selector
    today = date.today()
    months = []
    for i in range(6):
        d = today.replace(day=1) - timedelta(days=30*i)
        d = d.replace(day=1)
        months.append(d)
    month_labels = [m.strftime("%B %Y") for m in months]
    sel_idx = st.selectbox("Mês", range(len(months)), format_func=lambda i: month_labels[i], key="hm")
    sel_month = months[sel_idx]

    # Build calendar
    import calendar
    cal = calendar.monthcalendar(sel_month.year, sel_month.month)

    # Header
    st.markdown('<div class="cal-grid">'
               '<div class="cal-header">Seg</div><div class="cal-header">Ter</div>'
               '<div class="cal-header">Qua</div><div class="cal-header">Qui</div>'
               '<div class="cal-header">Sex</div><div class="cal-header">Sáb</div>'
               '<div class="cal-header">Dom</div></div>', unsafe_allow_html=True)

    # Days - use buttons for navigation
    for week in cal:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            with cols[i]:
                if day_num == 0:
                    st.write("")
                else:
                    d = date(sel_month.year, sel_month.month, day_num)
                    if d > today:
                        st.markdown(f"<div style='text-align:center;color:#333;padding:8px;'>{day_num}</div>",
                                   unsafe_allow_html=True)
                    else:
                        status = day_completeness(d.isoformat())
                        colors = {
                            "green": "🟢", "yellow": "🟡", "red": "🔴", "gray": "⚫"
                        }
                        btn_label = f"{colors[status]} {day_num}"
                        if st.button(btn_label, key=f"cal_{d.isoformat()}", use_container_width=True):
                            st.session_state.sel_date = d
                            st.session_state.page = "hoje"
                            st.rerun()

    st.markdown("---")
    st.caption("🟢 Bem preenchido · 🟡 Incompleto · 🔴 Quase vazio · ⚫ Sem registro")
    st.caption("Clique em um dia para abrir e editar.")


# ============================================
# PAGE: IA
# ============================================
def page_ia():
    st.markdown('<div class="section-title">🤖 Assistente de saúde</div>', unsafe_allow_html=True)

    # Context builder
    def build_context(days=7):
        start = (date.today() - timedelta(days=days)).isoformat()
        weights = get_weight_history(days)
        meals_data = db.table("meals").select("date,meal_type,food_key,kcal,protein_g,carbs_g,fat_g").gte("date", start).order("date").execute().data or []
        sleep_data = db.table("sleep_cpap").select("date,total_hours,ahi,energy_score,tiredness_score").gte("date", start).order("date").execute().data or []
        checks = db.table("checklist_daily").select("date,item_key,done").gte("date", start).order("date").execute().data or []
        bio = db.table("bioimpedance").select("*").order("date", desc=True).limit(1).execute().data or []
        labs = db.table("lab_results").select("*").order("date", desc=True).limit(1).execute().data or []

        return f"""CONTEXTO DO PACIENTE — João, 34 anos, 174cm
Objetivo: emagrecer de ~143kg para 90kg preservando massa magra
Quadro: resistência insulínica (HOMA-IR 4.17), TSH 8.14, triglicérides 313, GGT 108, testosterona 202, gordura visceral 31
Meta calórica: ~2067 kcal/dia | Meta proteína: ~180g/dia

PESO (últimos {days} dias): {json.dumps(weights, default=str)}
REFEIÇÕES: {json.dumps(meals_data, default=str)}
SONO: {json.dumps(sleep_data, default=str)}
CHECKLIST: {json.dumps(checks, default=str)}
BIOIMPEDÂNCIA RECENTE: {json.dumps(bio, default=str)}
EXAMES RECENTES: {json.dumps(labs, default=str)}"""

    # Quick actions
    st.markdown("**Análises rápidas:**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 Últimos 7 dias", key="ia7", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 7 dias de forma prática e direta."})
    with c2:
        if st.button("📊 Últimos 14 dias", key="ia14", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Analise meus últimos 14 dias."})
    c1, c2 = st.columns(2)
    with c1:
        if st.button("❓ Onde estou errando?", key="iaerr", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Onde estou errando? O que preciso corrigir primeiro?"})
    with c2:
        if st.button("😴 Sono vs rotina", key="iasono", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": "Como meu sono influenciou minha semana?"})

    st.markdown("---")

    # Chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg chat-ai">{msg["content"]}</div>', unsafe_allow_html=True)

    # Process pending AI messages
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.spinner("Analisando seus dados..."):
            context = build_context(14)
            messages = [
                {"role": "system", "content": f"""Você é o assistente pessoal de saúde de João. Use os dados concretos dele para responder.

{context}

REGRAS:
- Seja direto, prático, crítico quando necessário
- Não use linguagem de coach ou motivacional
- Não seja genérico — use os números dele
- Fale em português do Brasil
- Não substitua médico — mas ajude a interpretar padrões
- Quando dados faltarem, diga
- Estruture a resposta com clareza
- Máximo 200 palavras por resposta"""},
            ]
            # Add chat history
            for msg in st.session_state.chat_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

            try:
                response = ai.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                ai_msg = response.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": ai_msg})
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {str(e)}")
                st.session_state.chat_history.pop()

    # Free input
    user_input = st.chat_input("Pergunte sobre seus dados...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.rerun()

    # Clear chat
    if st.session_state.chat_history:
        if st.button("🗑️ Limpar conversa", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Export
    st.markdown("---")
    if st.button("📦 Exportar dados (30 dias)", key="exp", use_container_width=True):
        start = (date.today() - timedelta(days=30)).isoformat()
        export = {
            "peso": get_weight_history(30),
            "refeicoes": (db.table("meals").select("*").gte("date", start).execute()).data or [],
            "sono": (db.table("sleep_cpap").select("*").gte("date", start).execute()).data or [],
            "checklist": (db.table("checklist_daily").select("*").gte("date", start).execute()).data or [],
        }
        st.download_button("⬇️ Baixar JSON", json.dumps(export, indent=2, ensure_ascii=False, default=str),
                          f"export_{date.today()}.json", "application/json", use_container_width=True)


# ============================================
# ROUTING
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
