import streamlit as st
from supabase import create_client
from datetime import date, timedelta, datetime
import pandas as pd

# ============================================
# CONEXÃO SUPABASE
# ============================================
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

db = get_supabase()

# ============================================
# CONFIGURAÇÃO
# ============================================
st.set_page_config(
    page_title="MyGrubinessPal",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================
# CSS — MOBILE FIRST, LIMPO
# ============================================
st.markdown("""
<style>
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 4rem;
        max-width: 600px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .card {
        background: #1A1D23;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #2D3139;
    }
    .card-value {
        font-size: 28px;
        font-weight: 700;
        color: #FAFAFA;
    }
    .card-sub {
        font-size: 13px;
        color: #888;
        margin-top: 4px;
    }
    .macro-row {
        display: flex;
        gap: 8px;
        margin: 8px 0 12px 0;
    }
    .macro-pill {
        background: #2D3139;
        border-radius: 8px;
        padding: 8px 12px;
        text-align: center;
        flex: 1;
    }
    .macro-pill .label {
        font-size: 11px;
        color: #888;
        text-transform: uppercase;
    }
    .macro-pill .value {
        font-size: 18px;
        font-weight: 600;
        color: #FAFAFA;
    }
    .badge-green {
        background: #1B5E20; color: #81C784;
        padding: 4px 12px; border-radius: 20px; font-size: 13px; display: inline-block;
    }
    .badge-yellow {
        background: #4E3A00; color: #FFD54F;
        padding: 4px 12px; border-radius: 20px; font-size: 13px; display: inline-block;
    }
    .badge-red {
        background: #4E0000; color: #E57373;
        padding: 4px 12px; border-radius: 20px; font-size: 13px; display: inline-block;
    }
    .stNumberInput input, .stSelectbox select, .stTextArea textarea {
        font-size: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ESTADO
# ============================================
if "page" not in st.session_state:
    st.session_state.page = "hoje"
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()

# ============================================
# SELETOR DE DATA GLOBAL
# ============================================
def date_selector():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("◀", key=f"prev_{st.session_state.page}", use_container_width=True):
            st.session_state.selected_date -= timedelta(days=1)
            st.rerun()
    with col2:
        new_date = st.date_input(
            "Data", value=st.session_state.selected_date,
            label_visibility="collapsed", key=f"dp_{st.session_state.page}"
        )
        if new_date != st.session_state.selected_date:
            st.session_state.selected_date = new_date
            st.rerun()
    with col3:
        if st.button("▶", key=f"next_{st.session_state.page}", use_container_width=True):
            st.session_state.selected_date += timedelta(days=1)
            st.rerun()
    d = st.session_state.selected_date
    if d == date.today():
        st.caption("📅 Hoje")
    elif d == date.today() - timedelta(days=1):
        st.caption("📅 Ontem")
    else:
        dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        st.caption(f"📅 {dias[d.weekday()]}, {d.strftime('%d/%m/%Y')}")
    return d.isoformat()

# ============================================
# FUNÇÕES DE DADOS
# ============================================
def get_weight_history(days=30):
    start = (date.today() - timedelta(days=days)).isoformat()
    r = db.table("daily_weight").select("date, weight_kg").gte("date", start).order("date").execute()
    return r.data or []

def get_goals():
    r = db.table("goals").select("*").eq("active", True).execute()
    return {g["metric"]: g for g in r.data} if r.data else {}

def get_checklist_items():
    r = db.table("checklist_items").select("*").eq("active", True).order("sort_order").execute()
    return r.data or []

def get_daily_checklist(target_date):
    r = db.table("checklist_daily").select("*").eq("date", target_date).execute()
    return {x["item_key"]: x for x in r.data} if r.data else {}

def upsert_checklist(target_date, item_key, done):
    db.table("checklist_daily").upsert(
        {"date": target_date, "item_key": item_key, "done": done},
        on_conflict="date,item_key"
    ).execute()

def upsert_weight(target_date, weight_kg):
    db.table("daily_weight").upsert(
        {"date": target_date, "weight_kg": weight_kg},
        on_conflict="date"
    ).execute()

def get_daily_meals(target_date):
    r = db.table("meals").select("*").eq("date", target_date).execute()
    return r.data or []

def get_food_library():
    r = db.table("food_library").select("*").eq("active", True).order("name").execute()
    return r.data or []

def get_weight_for_date(target_date):
    r = db.table("daily_weight").select("weight_kg").eq("date", target_date).execute()
    return float(r.data[0]["weight_kg"]) if r.data else None

def get_sleep_for_date(target_date):
    r = db.table("sleep_cpap").select("*").eq("date", target_date).execute()
    return r.data[0] if r.data else {}

# ============================================
# ALIMENTOS SUGERIDOS POR REFEIÇÃO
# ============================================
MEAL_FOOD_MAP = {
    "cafe": {
        "sugestoes": ["ovo_cozido", "whey_dose", "suco_verde", "leite_desnatado",
                      "pao_integral", "banana", "aveia", "iogurte_grego", "cafe_puro", "queijo_branco"],
        "label": "☕ Café da manhã / Pós-treino"
    },
    "almoco": {
        "sugestoes": ["arroz_branco", "feijao_cozido", "arroz_feijao", "frango_grelhado",
                      "patinho_moido", "carne_magra", "lombo_suino", "batata_cozida",
                      "mandioca_cozida", "alface", "rucula", "tomate", "cenoura_crua",
                      "beterraba", "chuchu", "vagem", "couve_cozida", "azeite",
                      "agua", "refri_zero", "lentilha"],
        "label": "🍽️ Almoço"
    },
    "lanche": {
        "sugestoes": ["pao_integral", "whey_dose", "iogurte_grego", "banana",
                      "queijo_branco", "castanhas", "cafe_puro", "leite_desnatado",
                      "requeijao_light", "aveia"],
        "label": "🥪 Lanche da tarde"
    },
    "jantar": {
        "sugestoes": ["macarrao_cozido", "arroz_branco", "frango_grelhado", "patinho_moido",
                      "carne_magra", "hamburguer_caseiro", "mussarela", "pao_integral",
                      "alface", "rucula", "tomate", "cenoura_crua", "couve_cozida",
                      "azeite", "sopa_lentilha", "caldo_abobora", "agua", "refri_zero"],
        "label": "🌙 Jantar"
    },
    "ceia": {
        "sugestoes": ["iogurte_grego", "whey_dose", "queijo_branco", "banana",
                      "leite_desnatado", "castanhas"],
        "label": "🫖 Ceia"
    },
    "bebida": {
        "sugestoes": ["cerveja_lata", "cerveja_long", "cerveja_600", "vinho_taca",
                      "destilado_dose", "chopp", "xeque_mate_lata", "aperol_spritz"],
        "label": "🍺 Bebidas alcoólicas"
    }
}

# ============================================
# NAVEGAÇÃO
# ============================================
def nav_bar():
    st.markdown("---")
    cols = st.columns(5)
    nav_items = [
        ("hoje", "📋", "Hoje"),
        ("alimentacao", "🍽️", "Alim"),
        ("peso", "⚖️", "Peso"),
        ("sono", "😴", "Sono"),
        ("ia", "🤖", "IA"),
    ]
    for i, (key, icon, label) in enumerate(nav_items):
        with cols[i]:
            tp = "primary" if st.session_state.page == key else "secondary"
            if st.button(f"{icon}\n{label}", key=f"nav_{key}", use_container_width=True, type=tp):
                st.session_state.page = key
                st.rerun()

# ============================================
# PÁGINA: HOJE
# ============================================
def page_hoje():
    st.markdown("# 📋 Meu dia")
    target = date_selector()
    goals = get_goals()
    weight_goal = float(goals.get("weight", {}).get("target_value", 90))

    # --- PESO ---
    current_weight = get_weight_for_date(target)
    st.markdown("#### ⚖️ Peso")
    c1, c2 = st.columns([3, 1])
    with c1:
        pv = current_weight if current_weight else 143.0
        peso = st.number_input("kg", 50.0, 250.0, pv, 0.1, format="%.1f",
                               key="peso_hoje", label_visibility="collapsed")
    with c2:
        if st.button("💾", key="btn_peso", use_container_width=True):
            upsert_weight(target, peso)
            st.rerun()

    if current_weight:
        diff = current_weight - weight_goal
        st.markdown(
            f'<div class="card"><div class="card-value">{current_weight:.1f} kg</div>'
            f'<div class="card-sub">Meta: {weight_goal:.0f} kg · faltam {diff:.1f} kg</div></div>',
            unsafe_allow_html=True
        )

    history = get_weight_history(30)
    if len(history) > 1:
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])
        df["weight_kg"] = df["weight_kg"].astype(float)
        df["meta"] = weight_goal
        st.line_chart(df.set_index("date")[["weight_kg", "meta"]], height=180)

    # --- CHECKLIST ---
    st.markdown("#### 💊 Medicação e hábitos")
    items = get_checklist_items()
    daily = get_daily_checklist(target)
    skip_keys = {"suco_verde", "whey"}
    items = [i for i in items if i["item_key"] not in skip_keys]

    slot_labels = {
        "jejum": "☀️ Jejum", "manha": "🌅 Manhã", "almoco": "🍽️ Almoço",
        "jantar": "🌙 Jantar", "noite": "🌑 Noite", "variavel": "🔄 Quando fizer"
    }
    current_slot = ""
    for item in items:
        slot = item["time_slot"]
        if slot != current_slot:
            current_slot = slot
            st.markdown(f"**{slot_labels.get(slot, slot.upper())}**")
        checked = daily.get(item["item_key"], {}).get("done", False)
        dosage = f" · {item['dosage']}" if item.get("dosage") else ""
        label = f"{item['name']}{dosage}"
        if item.get("instruction"):
            label += f"  \n↳ _{item['instruction']}_"
        new_val = st.checkbox(label, value=checked, key=f"ck_{item['item_key']}_{target}")
        if new_val != checked:
            upsert_checklist(target, item["item_key"], new_val)

    # --- RESUMO ALIMENTAÇÃO ---
    st.markdown("#### 🍽️ Alimentação do dia")
    meals = get_daily_meals(target)
    if meals:
        tk = sum(float(m.get("kcal") or 0) for m in meals)
        tp = sum(float(m.get("protein_g") or 0) for m in meals)
        tc = sum(float(m.get("carbs_g") or 0) for m in meals)
        tf = sum(float(m.get("fat_g") or 0) for m in meals)
        kcal_goal = float(goals.get("kcal_daily", {}).get("target_value", 2067))
        prot_goal = float(goals.get("protein_daily", {}).get("target_value", 180))
        st.markdown(
            f'<div class="macro-row">'
            f'<div class="macro-pill"><div class="label">kcal</div><div class="value">{tk:.0f}</div></div>'
            f'<div class="macro-pill"><div class="label">prot</div><div class="value">{tp:.0f}g</div></div>'
            f'<div class="macro-pill"><div class="label">carb</div><div class="value">{tc:.0f}g</div></div>'
            f'<div class="macro-pill"><div class="label">gord</div><div class="value">{tf:.0f}g</div></div>'
            f'</div>', unsafe_allow_html=True
        )
        if tk <= kcal_goal * 1.1 and tp >= prot_goal * 0.9:
            st.markdown('<span class="badge-green">🟢 Dia coerente</span>', unsafe_allow_html=True)
        elif tk <= kcal_goal * 1.25 or tp >= prot_goal * 0.7:
            st.markdown('<span class="badge-yellow">🟡 Atenção</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-red">🔴 Fora da estratégia</span>', unsafe_allow_html=True)
    else:
        st.caption("Nenhuma refeição registrada.")

    # --- SONO RESUMO ---
    sleep = get_sleep_for_date(target)
    if sleep:
        st.markdown("#### 😴 Sono")
        hrs = sleep.get("total_hours") or "—"
        ahi_v = sleep.get("ahi") or "—"
        en = sleep.get("energy_score") or "—"
        st.markdown(
            f'<div class="card"><div class="card-sub">'
            f'{hrs}h de sono · AHI {ahi_v} · Energia {en}/10</div></div>',
            unsafe_allow_html=True
        )

# ============================================
# PÁGINA: ALIMENTAÇÃO
# ============================================
def page_alimentacao():
    st.markdown("# 🍽️ Alimentação")
    target = date_selector()

    foods = get_food_library()
    food_map = {f["food_key"]: f for f in foods}
    food_names = {f["food_key"]: f["name"] for f in foods}
    goals = get_goals()
    kcal_goal = float(goals.get("kcal_daily", {}).get("target_value", 2067))
    prot_goal = float(goals.get("protein_daily", {}).get("target_value", 180))
    all_meals = get_daily_meals(target)

    # Totais no topo
    tk = sum(float(m.get("kcal") or 0) for m in all_meals)
    tp = sum(float(m.get("protein_g") or 0) for m in all_meals)
    tc = sum(float(m.get("carbs_g") or 0) for m in all_meals)
    tf = sum(float(m.get("fat_g") or 0) for m in all_meals)
    st.markdown(
        f'<div class="macro-row">'
        f'<div class="macro-pill"><div class="label">kcal</div><div class="value">{tk:.0f}</div></div>'
        f'<div class="macro-pill"><div class="label">prot</div><div class="value">{tp:.0f}g</div></div>'
        f'<div class="macro-pill"><div class="label">carb</div><div class="value">{tc:.0f}g</div></div>'
        f'<div class="macro-pill"><div class="label">gord</div><div class="value">{tf:.0f}g</div></div>'
        f'</div>', unsafe_allow_html=True
    )
    if tk > 0:
        st.caption(f"Calorias: {tk/kcal_goal*100:.0f}% da meta · Proteína: {tp/prot_goal*100:.0f}% da meta")
    st.markdown("---")

    for meal_key, meal_info in MEAL_FOOD_MAP.items():
        meal_items = [m for m in all_meals if m["meal_type"] == meal_key]
        meal_kcal = sum(float(m.get("kcal") or 0) for m in meal_items)
        header = meal_info["label"]
        if meal_items:
            header += f"  ·  {meal_kcal:.0f} kcal"

        with st.expander(header, expanded=False):
            if meal_items:
                for mi in meal_items:
                    fname = food_names.get(mi["food_key"], mi["food_key"])
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(
                            f"**{fname}** — {float(mi['quantity_g']):.0f}g  \n"
                            f"_{float(mi.get('kcal') or 0):.0f}kcal · "
                            f"P:{float(mi.get('protein_g') or 0):.0f}g · "
                            f"C:{float(mi.get('carbs_g') or 0):.0f}g · "
                            f"G:{float(mi.get('fat_g') or 0):.0f}g_"
                        )
                    with c2:
                        if st.button("🗑️", key=f"del_{mi['id']}"):
                            db.table("meals").delete().eq("id", mi["id"]).execute()
                            st.rerun()
                st.markdown("---")

            # Seletor de alimento — sugeridos primeiro
            sugestoes = meal_info["sugestoes"]
            fs = [f for f in foods if f["food_key"] in sugestoes]
            fo = [f for f in foods if f["food_key"] not in sugestoes]
            ok = [""] + [f["food_key"] for f in fs]
            ol = ["Selecione..."] + [f["name"] for f in fs]
            if fo:
                ok.append("__sep__")
                ol.append("── Outros ──")
                for f in fo:
                    ok.append(f["food_key"])
                    ol.append(f["name"])

            sel = st.selectbox("Adicionar", options=ok,
                               format_func=lambda x: ol[ok.index(x)],
                               key=f"sel_{meal_key}_{target}", label_visibility="collapsed")

            if sel and sel != "__sep__":
                food = food_map[sel]
                dg = float(food["default_portion_g"])
                qty = st.number_input(f"Quantidade (g) · porção: {dg:.0f}g",
                                      1.0, 5000.0, dg, 10.0, key=f"qty_{meal_key}_{target}")
                fac = qty / 100.0
                ek = float(food["kcal_per_100g"]) * fac
                ep = float(food["protein_per_100g"]) * fac
                ec = float(food["carbs_per_100g"]) * fac
                ef = float(food["fat_per_100g"]) * fac
                st.caption(f"→ {ek:.0f} kcal · P:{ep:.0f}g · C:{ec:.0f}g · G:{ef:.0f}g")

                if st.button("✅ Adicionar", key=f"add_{meal_key}_{target}", use_container_width=True):
                    db.table("meals").insert({
                        "date": target, "meal_type": meal_key, "food_key": sel,
                        "quantity_g": qty, "portions": qty / dg,
                        "kcal": ek, "protein_g": ep, "carbs_g": ec, "fat_g": ef
                    }).execute()
                    st.rerun()

# ============================================
# PÁGINA: SONO / CPAP
# ============================================
def page_sono():
    st.markdown("# 😴 Sono / CPAP")
    target = date_selector()
    data = get_sleep_for_date(target)

    with st.form("form_sono"):
        st.markdown("**Horários**")
        c1, c2 = st.columns(2)
        with c1:
            bed_time = st.time_input("Dormiu às", value=None, key="bed")
        with c2:
            wake_time = st.time_input("Acordou às", value=None, key="wake")
        total_hours = st.number_input("Horas totais", 0.0, 16.0,
                                      value=float(data.get("total_hours") or 0), step=0.5)

        st.markdown("**CPAP**")
        c1, c2 = st.columns(2)
        with c1:
            used_cpap = st.checkbox("Usou CPAP?", value=bool(data.get("used_cpap", True)))
            cpap_hours = st.number_input("Horas de uso", 0.0, 16.0,
                                         value=float(data.get("cpap_hours") or 0), step=0.5)
            ahi = st.number_input("AHI", 0.0, 100.0,
                                  value=float(data.get("ahi") or 0), step=0.1)
        with c2:
            leak_rate = st.number_input("Vazamento", 0.0, 100.0,
                                        value=float(data.get("leak_rate") or 0), step=0.1)
            mo = ["boa", "regular", "ruim"]
            mask_seal = st.selectbox("Vedação", mo,
                                     index=mo.index(data.get("mask_seal") or "boa"))
            removed = st.checkbox("Tirou a máscara?", value=bool(data.get("removed_mask", False)))

        events = st.number_input("Eventos/hora", 0.0, 100.0,
                                 value=float(data.get("events_per_hour") or 0), step=0.1)

        st.markdown("**Como você está?**")
        c1, c2 = st.columns(2)
        with c1:
            tiredness = st.slider("Cansaço (0=exausto, 10=descansado)", 0, 10,
                                  value=int(data.get("tiredness_score") or 5))
        with c2:
            energy = st.slider("Energia (0=zero, 10=máxima)", 0, 10,
                               value=int(data.get("energy_score") or 5))

        notes = st.text_area("Observações", value=data.get("notes") or "", height=60)

        if st.form_submit_button("💾 Salvar", use_container_width=True):
            rec = {
                "date": target,
                "bed_time": bed_time.isoformat() if bed_time else None,
                "wake_time": wake_time.isoformat() if wake_time else None,
                "total_hours": total_hours, "used_cpap": used_cpap,
                "cpap_hours": cpap_hours, "ahi": ahi, "leak_rate": leak_rate,
                "mask_seal": mask_seal, "removed_mask": removed,
                "events_per_hour": events, "tiredness_score": tiredness,
                "energy_score": energy, "notes": notes
            }
            db.table("sleep_cpap").upsert(rec, on_conflict="date").execute()
            st.success("Salvo ✓")

# ============================================
# PÁGINA: PESO E MEDIDAS
# ============================================
def page_peso():
    st.markdown("# ⚖️ Peso e Medidas")
    goals = get_goals()
    wg = float(goals.get("weight", {}).get("target_value", 90))

    tab1, tab2, tab3 = st.tabs(["📈 Gráfico", "📝 Registrar", "📏 Medidas"])

    with tab1:
        period = st.selectbox("Período", ["30 dias", "60 dias", "90 dias", "Tudo"])
        dm = {"30 dias": 30, "60 dias": 60, "90 dias": 90, "Tudo": 3650}
        history = get_weight_history(dm[period])
        if history:
            df = pd.DataFrame(history)
            df["date"] = pd.to_datetime(df["date"])
            df["weight_kg"] = df["weight_kg"].astype(float)
            df["meta"] = wg
            st.line_chart(df.set_index("date")[["weight_kg", "meta"]], height=300)
            if len(history) > 1:
                fi = float(history[0]["weight_kg"])
                la = float(history[-1]["weight_kg"])
                di = la - fi
                st.caption(f"Primeiro: {fi:.1f} kg · Último: {la:.1f} kg · Variação: {'+'if di>0 else ''}{di:.1f} kg")
        else:
            st.caption("Nenhum peso registrado.")

    with tab2:
        dt = st.date_input("Data", value=date.today(), key="dt_peso_r")
        peso = st.number_input("Peso (kg)", 50.0, 250.0, 143.0, 0.1, key="peso_r")
        if st.button("💾 Salvar", use_container_width=True, key="btn_save_peso"):
            upsert_weight(dt.isoformat(), peso)
            st.success("Salvo ✓")
        st.markdown("**Últimos registros**")
        for h in reversed(get_weight_history(30)):
            c1, c2 = st.columns([3, 1])
            c1.text(f"{h['date']}  →  {h['weight_kg']} kg")
            with c2:
                if st.button("🗑️", key=f"dw_{h['date']}"):
                    db.table("daily_weight").delete().eq("date", h["date"]).execute()
                    st.rerun()

    with tab3:
        dt_m = st.date_input("Data", value=date.today(), key="dt_med")
        c1, c2 = st.columns(2)
        with c1:
            cin = st.number_input("Cintura (cm)", 0.0, 250.0, 0.0, 0.5, key="mc")
            abd = st.number_input("Abdômen (cm)", 0.0, 250.0, 0.0, 0.5, key="ma")
            pei = st.number_input("Peito (cm)", 0.0, 250.0, 0.0, 0.5, key="mp")
        with c2:
            bra = st.number_input("Braço (cm)", 0.0, 100.0, 0.0, 0.5, key="mb")
            cox = st.number_input("Coxa (cm)", 0.0, 150.0, 0.0, 0.5, key="mx")
            qua = st.number_input("Quadril (cm)", 0.0, 250.0, 0.0, 0.5, key="mq")
        if st.button("💾 Salvar medidas", use_container_width=True):
            db.table("measurements").insert({
                "date": dt_m.isoformat(),
                "waist_cm": cin or None, "abdomen_cm": abd or None,
                "chest_cm": pei or None, "arm_cm": bra or None,
                "thigh_cm": cox or None, "hip_cm": qua or None
            }).execute()
            st.success("Salvo ✓")

# ============================================
# PÁGINA: IA
# ============================================
def page_ia():
    st.markdown("# 🤖 IA")
    st.markdown("Módulo em construção. Use o export para análise no Claude.")
    if st.button("📦 Exportar últimos 30 dias", use_container_width=True):
        import json
        start = (date.today() - timedelta(days=30)).isoformat()
        export = {
            "peso": get_weight_history(30),
            "refeicoes": (db.table("meals").select("*").gte("date", start).order("date").execute()).data or [],
            "sono": (db.table("sleep_cpap").select("*").gte("date", start).order("date").execute()).data or [],
            "checklist": (db.table("checklist_daily").select("*").gte("date", start).order("date").execute()).data or [],
        }
        js = json.dumps(export, indent=2, ensure_ascii=False, default=str)
        st.download_button("⬇️ Baixar JSON", data=js,
                           file_name=f"export_{date.today().isoformat()}.json",
                           mime="application/json", use_container_width=True)

# ============================================
# ROTEAMENTO
# ============================================
page_map = {
    "hoje": page_hoje,
    "alimentacao": page_alimentacao,
    "sono": page_sono,
    "peso": page_peso,
    "ia": page_ia,
}
page_map[st.session_state.page]()
nav_bar()
