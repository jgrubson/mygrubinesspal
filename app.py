import streamlit as st
from supabase import create_client
from datetime import date, timedelta

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
# CONFIGURAÇÃO DA PÁGINA
# ============================================
st.set_page_config(
    page_title="MyGrubinessPal",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================
# CSS CUSTOMIZADO — MOBILE FIRST
# ============================================
st.markdown("""
<style>
    /* Remove padding excessivo */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 600px;
    }
    /* Sidebar mais limpa */
    [data-testid="stSidebar"] {
        min-width: 200px;
        max-width: 250px;
    }
    /* Esconde menu hamburger e footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Tabs maiores para toque */
    .stTabs [data-baseweb="tab"] {
        padding: 10px 16px;
        font-size: 14px;
    }
    /* Botões mais tocáveis */
    .stButton > button {
        width: 100%;
        padding: 0.5rem;
        margin-bottom: 0.25rem;
    }
    /* Checkboxes maiores */
    .stCheckbox label {
        font-size: 15px;
        padding: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ESTADO DE SESSÃO
# ============================================
if "page" not in st.session_state:
    st.session_state.page = "hoje"

# ============================================
# FUNÇÕES AUXILIARES
# ============================================
def get_today():
    """Retorna data de hoje como string ISO."""
    return date.today().isoformat()

def get_weight_history(days=30):
    """Busca histórico de peso dos últimos N dias."""
    start = (date.today() - timedelta(days=days)).isoformat()
    result = db.table("daily_weight") \
        .select("date, weight_kg") \
        .gte("date", start) \
        .order("date") \
        .execute()
    return result.data if result.data else []

def get_goals():
    """Busca metas ativas."""
    result = db.table("goals") \
        .select("*") \
        .eq("active", True) \
        .execute()
    return {g["metric"]: g for g in result.data} if result.data else {}

def get_checklist_items():
    """Busca itens do checklist ordenados."""
    result = db.table("checklist_items") \
        .select("*") \
        .eq("active", True) \
        .order("sort_order") \
        .execute()
    return result.data if result.data else []

def get_daily_checklist(target_date):
    """Busca checklist preenchido de uma data."""
    result = db.table("checklist_daily") \
        .select("*") \
        .eq("date", target_date) \
        .execute()
    return {r["item_key"]: r for r in result.data} if result.data else {}

def upsert_checklist(target_date, item_key, done):
    """Marca/desmarca item do checklist."""
    db.table("checklist_daily").upsert({
        "date": target_date,
        "item_key": item_key,
        "done": done
    }, on_conflict="date,item_key").execute()

def upsert_weight(target_date, weight_kg, notes=""):
    """Registra ou atualiza peso do dia."""
    db.table("daily_weight").upsert({
        "date": target_date,
        "weight_kg": weight_kg,
        "notes": notes
    }, on_conflict="date").execute()

def get_daily_meals(target_date):
    """Busca refeições de uma data."""
    result = db.table("meals") \
        .select("*") \
        .eq("date", target_date) \
        .execute()
    return result.data if result.data else []

def get_food_library():
    """Busca biblioteca de alimentos."""
    result = db.table("food_library") \
        .select("*") \
        .eq("active", True) \
        .order("name") \
        .execute()
    return result.data if result.data else []

# ============================================
# NAVEGAÇÃO
# ============================================
PAGES = {
    "hoje": "📋 Hoje",
    "alimentacao": "🍽️ Alimentação",
    "sono": "😴 Sono / CPAP",
    "peso": "⚖️ Peso e Medidas",
    "bio": "🔬 Bio e Exames",
    "relatorios": "📊 Relatórios",
    "ia": "🤖 IA"
}

# Barra de navegação inferior
def nav_bar():
    cols = st.columns(4)
    nav_items = [
        ("hoje", "📋", "Hoje"),
        ("alimentacao", "🍽️", "Alim."),
        ("peso", "⚖️", "Dados"),
        ("ia", "🤖", "IA"),
    ]
    for i, (key, icon, label) in enumerate(nav_items):
        with cols[i]:
            if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

# Sub-navegação para "Dados"
def data_sub_nav():
    cols = st.columns(4)
    sub_items = [
        ("peso", "⚖️ Peso"),
        ("sono", "😴 Sono"),
        ("bio", "🔬 Bio"),
        ("relatorios", "📊 Relat."),
    ]
    for i, (key, label) in enumerate(sub_items):
        with cols[i]:
            if st.button(label, key=f"sub_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

# ============================================
# PÁGINAS
# ============================================

def page_hoje():
    today = get_today()
    st.markdown(f"## 📋 Hoje — {date.today().strftime('%d/%m/%Y')}")

    # --- PESO DO DIA ---
    st.markdown("### Peso do dia")
    goals = get_goals()
    weight_goal = goals.get("weight", {}).get("target_value", 90)

    col1, col2 = st.columns([2, 1])
    with col1:
        peso = st.number_input("Peso (kg)", min_value=50.0, max_value=250.0,
                               value=143.0, step=0.1, format="%.1f", key="peso_hoje")
    with col2:
        if st.button("Salvar peso", key="btn_peso"):
            upsert_weight(today, peso)
            st.success("Salvo")

    st.caption(f"Meta: {weight_goal} kg")

    # --- MINI GRÁFICO ---
    history = get_weight_history(30)
    if history:
        import pandas as pd
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])
        df["meta"] = float(weight_goal)
        chart_data = df.set_index("date")[["weight_kg", "meta"]]
        st.line_chart(chart_data, height=200)

    # --- CHECKLIST ---
    st.markdown("### Checklist do dia")
    items = get_checklist_items()
    daily = get_daily_checklist(today)

    current_slot = ""
    slot_labels = {
        "jejum": "☀️ JEJUM",
        "manha": "🌅 MANHÃ",
        "almoco": "🍽️ ALMOÇO",
        "jantar": "🌙 JANTAR",
        "noite": "🌑 NOITE",
        "variavel": "🔄 VARIÁVEL"
    }

    for item in items:
        slot = item["time_slot"]
        if slot != current_slot:
            current_slot = slot
            st.markdown(f"**{slot_labels.get(slot, slot.upper())}**")

        checked = daily.get(item["item_key"], {}).get("done", False)
        dosage = f" — {item['dosage']}" if item.get("dosage") else ""
        instruction = f"  \n_{item['instruction']}_" if item.get("instruction") else ""

        new_val = st.checkbox(
            f"{item['name']}{dosage}{instruction}",
            value=checked,
            key=f"check_{item['item_key']}"
        )
        if new_val != checked:
            upsert_checklist(today, item["item_key"], new_val)

    # --- RESUMO ALIMENTAÇÃO ---
    st.markdown("### Alimentação do dia")
    meals = get_daily_meals(today)
    if meals:
        total_kcal = sum(m.get("kcal", 0) or 0 for m in meals)
        total_prot = sum(m.get("protein_g", 0) or 0 for m in meals)
        total_carb = sum(m.get("carbs_g", 0) or 0 for m in meals)
        total_fat = sum(m.get("fat_g", 0) or 0 for m in meals)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("kcal", f"{total_kcal:.0f}")
        c2.metric("Prot", f"{total_prot:.0f}g")
        c3.metric("Carb", f"{total_carb:.0f}g")
        c4.metric("Gord", f"{total_fat:.0f}g")
    else:
        st.caption("Nenhuma refeição registrada hoje.")

    # --- OBSERVAÇÕES ---
    st.markdown("### Observações")
    st.text_area("Notas do dia", key="obs_hoje", height=80, placeholder="Opcional...")


def page_alimentacao():
    today = get_today()
    st.markdown(f"## 🍽️ Alimentação — {date.today().strftime('%d/%m/%Y')}")

    foods = get_food_library()
    food_map = {f["food_key"]: f for f in foods}
    food_names = {f["food_key"]: f["name"] for f in foods}

    meal_types = [
        ("cafe", "☕ Café da manhã / Pós-treino"),
        ("almoco", "🍽️ Almoço"),
        ("lanche", "🥪 Lanche / Pré-treino"),
        ("jantar", "🌙 Jantar"),
        ("ceia", "🫖 Ceia"),
    ]

    goals = get_goals()
    kcal_goal = goals.get("kcal_daily", {}).get("target_value", 2067)
    prot_goal = goals.get("protein_daily", {}).get("target_value", 180)

    all_meals = get_daily_meals(today)

    for meal_key, meal_label in meal_types:
        with st.expander(meal_label, expanded=False):
            # Itens já registrados nesta refeição
            meal_items = [m for m in all_meals if m["meal_type"] == meal_key]
            if meal_items:
                for mi in meal_items:
                    fname = food_names.get(mi["food_key"], mi["food_key"])
                    st.caption(
                        f"✅ {fname} — {mi['quantity_g']:.0f}g | "
                        f"{mi['kcal']:.0f}kcal | P:{mi['protein_g']:.0f}g "
                        f"C:{mi['carbs_g']:.0f}g G:{mi['fat_g']:.0f}g"
                    )
                    if st.button("🗑️", key=f"del_{mi['id']}"):
                        db.table("meals").delete().eq("id", mi["id"]).execute()
                        st.rerun()

            # Adicionar item
            st.markdown("**Adicionar item:**")
            food_options = [""] + [f["food_key"] for f in foods]
            food_labels = ["Selecione..."] + [f["name"] for f in foods]

            selected = st.selectbox(
                "Alimento", options=food_options,
                format_func=lambda x: food_labels[food_options.index(x)],
                key=f"sel_{meal_key}"
            )

            if selected:
                food = food_map[selected]
                default_g = float(food["default_portion_g"])
                qty = st.number_input(
                    f"Quantidade (g) — porção padrão: {default_g:.0f}g",
                    min_value=1.0, value=default_g, step=10.0,
                    key=f"qty_{meal_key}"
                )
                # Cálculo
                factor = qty / 100.0
                kcal = float(food["kcal_per_100g"]) * factor
                prot = float(food["protein_per_100g"]) * factor
                carb = float(food["carbs_per_100g"]) * factor
                fat = float(food["fat_per_100g"]) * factor

                st.caption(f"→ {kcal:.0f} kcal | P:{prot:.0f}g C:{carb:.0f}g G:{fat:.0f}g")

                if st.button("Adicionar", key=f"add_{meal_key}"):
                    db.table("meals").insert({
                        "date": today,
                        "meal_type": meal_key,
                        "food_key": selected,
                        "quantity_g": qty,
                        "portions": qty / default_g,
                        "kcal": kcal,
                        "protein_g": prot,
                        "carbs_g": carb,
                        "fat_g": fat
                    }).execute()
                    st.rerun()

    # --- TOTAIS DO DIA ---
    st.markdown("---")
    st.markdown("### Totais do dia")
    all_meals = get_daily_meals(today)
    total_kcal = sum(m.get("kcal", 0) or 0 for m in all_meals)
    total_prot = sum(m.get("protein_g", 0) or 0 for m in all_meals)
    total_carb = sum(m.get("carbs_g", 0) or 0 for m in all_meals)
    total_fat = sum(m.get("fat_g", 0) or 0 for m in all_meals)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("kcal", f"{total_kcal:.0f}", delta=f"{total_kcal - float(kcal_goal):.0f}")
    c2.metric("Prot", f"{total_prot:.0f}g", delta=f"{total_prot - float(prot_goal):.0f}")
    c3.metric("Carb", f"{total_carb:.0f}g")
    c4.metric("Gord", f"{total_fat:.0f}g")

    # Sinalização
    if total_kcal == 0:
        st.info("Nenhuma refeição registrada.")
    elif total_kcal <= float(kcal_goal) * 1.1 and total_prot >= float(prot_goal) * 0.9:
        st.success("🟢 Dia coerente com a estratégia.")
    elif total_kcal <= float(kcal_goal) * 1.2 or total_prot >= float(prot_goal) * 0.7:
        st.warning("🟡 Atenção: revise calorias ou proteína.")
    else:
        st.error("🔴 Dia fora da estratégia.")


def page_sono():
    today = get_today()
    st.markdown(f"## 😴 Sono / CPAP — {date.today().strftime('%d/%m/%Y')}")

    # Buscar dados existentes
    existing = db.table("sleep_cpap").select("*").eq("date", today).execute()
    data = existing.data[0] if existing.data else {}

    with st.form("form_sono"):
        col1, col2 = st.columns(2)
        with col1:
            bed_time = st.time_input("Hora que dormiu", value=None, key="bed")
            total_hours = st.number_input("Horas totais", 0.0, 16.0,
                                          value=float(data.get("total_hours", 0) or 0), step=0.5)
            ahi = st.number_input("AHI", 0.0, 100.0,
                                  value=float(data.get("ahi", 0) or 0), step=0.1)
            mask_seal = st.selectbox("Vedação máscara", ["boa", "regular", "ruim"],
                                     index=["boa", "regular", "ruim"].index(data.get("mask_seal", "boa") or "boa"))
            tiredness = st.slider("Acordou cansado? (0=muito, 10=descansado)", 0, 10,
                                  value=int(data.get("tiredness_score", 5) or 5))
        with col2:
            wake_time = st.time_input("Hora que acordou", value=None, key="wake")
            used_cpap = st.checkbox("Usou CPAP?", value=bool(data.get("used_cpap", True)))
            cpap_hours = st.number_input("Horas de CPAP", 0.0, 16.0,
                                         value=float(data.get("cpap_hours", 0) or 0), step=0.5)
            leak_rate = st.number_input("Vazamento", 0.0, 100.0,
                                        value=float(data.get("leak_rate", 0) or 0), step=0.1)
            removed = st.checkbox("Tirou a máscara?", value=bool(data.get("removed_mask", False)))
            energy = st.slider("Energia do dia (0=nenhuma, 10=máxima)", 0, 10,
                               value=int(data.get("energy_score", 5) or 5))

        events = st.number_input("Eventos por hora", 0.0, 100.0,
                                 value=float(data.get("events_per_hour", 0) or 0), step=0.1)
        notes = st.text_area("Observações", value=data.get("notes", "") or "", height=60)

        if st.form_submit_button("Salvar"):
            record = {
                "date": today,
                "bed_time": bed_time.isoformat() if bed_time else None,
                "wake_time": wake_time.isoformat() if wake_time else None,
                "total_hours": total_hours,
                "used_cpap": used_cpap,
                "cpap_hours": cpap_hours,
                "ahi": ahi,
                "leak_rate": leak_rate,
                "mask_seal": mask_seal,
                "removed_mask": removed,
                "events_per_hour": events,
                "tiredness_score": tiredness,
                "energy_score": energy,
                "notes": notes
            }
            db.table("sleep_cpap").upsert(record, on_conflict="date").execute()
            st.success("Sono salvo.")


def page_peso():
    st.markdown("## ⚖️ Peso e Medidas")
    data_sub_nav()

    tab1, tab2 = st.tabs(["Peso", "Medidas"])

    with tab1:
        today = get_today()
        col1, col2 = st.columns([2, 1])
        with col1:
            peso = st.number_input("Peso (kg)", 50.0, 250.0, 143.0, 0.1, key="peso_pg")
        with col2:
            dt = st.date_input("Data", value=date.today(), key="dt_peso")
        if st.button("Salvar peso", key="btn_peso_pg"):
            upsert_weight(dt.isoformat(), peso)
            st.success("Salvo")

        # Gráfico
        goals = get_goals()
        weight_goal = goals.get("weight", {}).get("target_value", 90)
        history = get_weight_history(90)
        if history:
            import pandas as pd
            df = pd.DataFrame(history)
            df["date"] = pd.to_datetime(df["date"])
            df["meta"] = float(weight_goal)
            chart_data = df.set_index("date")[["weight_kg", "meta"]]
            st.line_chart(chart_data, height=300)

        # Histórico editável
        if history:
            st.markdown("### Histórico")
            for h in reversed(history[-10:]):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.text(f"{h['date']} — {h['weight_kg']} kg")
                with c3:
                    if st.button("🗑️", key=f"dw_{h['date']}"):
                        db.table("daily_weight").delete().eq("date", h["date"]).execute()
                        st.rerun()

    with tab2:
        st.markdown("### Registrar medidas")
        dt_m = st.date_input("Data", value=date.today(), key="dt_med")
        col1, col2 = st.columns(2)
        with col1:
            cintura = st.number_input("Cintura (cm)", 0.0, 250.0, 0.0, 0.5, key="m_cin")
            abdomen = st.number_input("Abdômen (cm)", 0.0, 250.0, 0.0, 0.5, key="m_abd")
            peito = st.number_input("Peito (cm)", 0.0, 250.0, 0.0, 0.5, key="m_pei")
        with col2:
            braco = st.number_input("Braço (cm)", 0.0, 100.0, 0.0, 0.5, key="m_bra")
            coxa = st.number_input("Coxa (cm)", 0.0, 150.0, 0.0, 0.5, key="m_cox")
            quadril = st.number_input("Quadril (cm)", 0.0, 250.0, 0.0, 0.5, key="m_qua")

        if st.button("Salvar medidas"):
            db.table("measurements").insert({
                "date": dt_m.isoformat(),
                "waist_cm": cintura or None,
                "abdomen_cm": abdomen or None,
                "chest_cm": peito or None,
                "arm_cm": braco or None,
                "thigh_cm": coxa or None,
                "hip_cm": quadril or None
            }).execute()
            st.success("Medidas salvas.")


def page_bio():
    st.markdown("## 🔬 Bioimpedância e Exames")
    data_sub_nav()

    tab1, tab2 = st.tabs(["Bioimpedância", "Exames"])

    with tab1:
        st.markdown("### Nova bioimpedância")
        with st.form("form_bio"):
            dt = st.date_input("Data")
            c1, c2 = st.columns(2)
            with c1:
                peso = st.number_input("Peso (kg)", 50.0, 250.0, 143.0, 0.1)
                fat_pct = st.number_input("% Gordura", 0.0, 80.0, 50.0, 0.1)
                visc = st.number_input("Gordura visceral", 0, 60, 31)
            with c2:
                muscle = st.number_input("Musc. esquelética (kg)", 0.0, 100.0, 39.0, 0.1)
                ffm = st.number_input("Massa livre gord. (kg)", 0.0, 150.0, 64.0, 0.1)
                bmr = st.number_input("TMB (kcal)", 0.0, 5000.0, 2681.0, 1.0)
            notes = st.text_area("Observação", height=60)
            if st.form_submit_button("Salvar"):
                db.table("bioimpedance").insert({
                    "date": dt.isoformat(), "weight_kg": peso, "fat_pct": fat_pct,
                    "visceral_fat": visc, "skeletal_muscle_kg": muscle,
                    "fat_free_mass_kg": ffm, "bmr_kcal": bmr, "notes": notes
                }).execute()
                st.success("Bioimpedância salva.")

        # Histórico
        bios = db.table("bioimpedance").select("*").order("date", desc=True).limit(5).execute()
        if bios.data:
            st.markdown("### Histórico")
            for b in bios.data:
                st.caption(
                    f"📅 {b['date']} | {b['weight_kg']}kg | "
                    f"Gord: {b['fat_pct']}% | Visc: {b['visceral_fat']} | "
                    f"Musc: {b['skeletal_muscle_kg']}kg"
                )

    with tab2:
        st.markdown("### Novos exames")
        with st.form("form_lab"):
            dt = st.date_input("Data", key="dt_lab")
            c1, c2, c3 = st.columns(3)
            with c1:
                glucose = st.number_input("Glicose", 0.0, 500.0, 0.0, 1.0)
                hba1c = st.number_input("HbA1c", 0.0, 15.0, 0.0, 0.1)
                insulin = st.number_input("Insulina", 0.0, 100.0, 0.0, 0.1)
                homa = st.number_input("HOMA-IR", 0.0, 20.0, 0.0, 0.01)
                tsh = st.number_input("TSH", 0.0, 50.0, 0.0, 0.01)
                t4 = st.number_input("T4 livre", 0.0, 10.0, 0.0, 0.01)
                testo = st.number_input("Testosterona", 0.0, 1500.0, 0.0, 1.0)
            with c2:
                trig = st.number_input("Triglicérides", 0.0, 1000.0, 0.0, 1.0)
                ggt = st.number_input("GGT", 0.0, 500.0, 0.0, 1.0)
                col_t = st.number_input("Colesterol total", 0.0, 500.0, 0.0, 1.0)
                ldl = st.number_input("LDL", 0.0, 300.0, 0.0, 1.0)
                hdl = st.number_input("HDL", 0.0, 150.0, 0.0, 1.0)
                tgo = st.number_input("TGO", 0.0, 500.0, 0.0, 1.0)
                tgp = st.number_input("TGP", 0.0, 500.0, 0.0, 1.0)
            with c3:
                mag = st.number_input("Magnésio", 0.0, 10.0, 0.0, 0.1)
                b12 = st.number_input("B12", 0.0, 2000.0, 0.0, 1.0)
                vitd = st.number_input("Vitamina D", 0.0, 150.0, 0.0, 0.1)
                creat = st.number_input("Creatinina", 0.0, 15.0, 0.0, 0.01)
                egfr = st.number_input("eGFR", 0.0, 150.0, 0.0, 1.0)
                cpk = st.number_input("CPK", 0.0, 1000.0, 0.0, 1.0)
            notes = st.text_area("Observação", key="lab_notes", height=60)
            if st.form_submit_button("Salvar exames"):
                record = {
                    "date": dt.isoformat(),
                    "glucose": glucose or None, "hba1c": hba1c or None,
                    "insulin": insulin or None, "homa_ir": homa or None,
                    "tsh": tsh or None, "t4_free": t4 or None,
                    "triglycerides": trig or None, "ggt": ggt or None,
                    "total_cholesterol": col_t or None, "ldl": ldl or None,
                    "hdl": hdl or None, "tgo": tgo or None, "tgp": tgp or None,
                    "magnesium": mag or None, "b12": b12 or None,
                    "vitamin_d": vitd or None, "creatinine": creat or None,
                    "egfr": egfr or None, "testosterone": testo or None,
                    "cpk": cpk or None, "notes": notes
                }
                db.table("lab_results").insert(record).execute()
                st.success("Exames salvos.")


def page_relatorios():
    st.markdown("## 📊 Relatórios")
    data_sub_nav()
    st.info("Módulo em construção — será ativado após acumular dados.")


def page_ia():
    st.markdown("## 🤖 IA")
    st.info("Módulo em construção — será ativado após acumular dados.")


# ============================================
# ROTEAMENTO
# ============================================
page_map = {
    "hoje": page_hoje,
    "alimentacao": page_alimentacao,
    "sono": page_sono,
    "peso": page_peso,
    "bio": page_bio,
    "relatorios": page_relatorios,
    "ia": page_ia,
}

page_map[st.session_state.page]()

st.markdown("---")
nav_bar()
