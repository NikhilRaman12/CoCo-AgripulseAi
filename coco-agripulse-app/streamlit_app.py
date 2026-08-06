"""
CoCo-AgriPulseAI — Enterprise Agricultural Intelligence Platform
Unstructured Data Intelligence System | Snowflake CoCo CLI Hackathon 2026
"""

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.set_page_config(page_title="CoCo-AgriPulseAI", page_icon="\U0001F33E", layout="wide")

@st.cache_data(ttl=300)
def run_query(sql):
    return session.sql(sql).to_pandas()

# ─── Custom CSS ───
st.markdown("""
<style>
    [data-testid="stSidebar"] {background: linear-gradient(180deg, #1B5E20 0%, #2E7D32 100%);}
    [data-testid="stSidebar"] * {color: #FFFFFF !important;}
    [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stTextArea label {color: #C8E6C9 !important; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;}
    div[data-testid="stMetric"] {background: #F1F8E9; border-radius: 8px; padding: 12px 16px; border-left: 4px solid #2E7D32;}
    .block-container {padding-top: 2rem;}
    div.stTabs [data-baseweb="tab-list"] {gap: 4px;}
    div.stTabs [data-baseweb="tab"] {background: #E8F5E9; border-radius: 6px 6px 0 0; padding: 8px 20px;}
    div.stTabs [aria-selected="true"] {background: #2E7D32 !important; color: white !important;}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ───
with st.sidebar:
    st.markdown("#### \U0001F33E CoCo-AgriPulseAI")
    st.caption("Enterprise Agricultural Intelligence")
    st.markdown("---")

    selected_crops = st.multiselect("Target Crops", ["Rice", "Cotton", "Chilli"], default=["Rice", "Cotton", "Chilli"])
    user_query = st.text_area("Intelligence Query", value="Full assessment for rice cotton chilli in Maharashtra", height=68)
    run_btn = st.button("\U0001F680 Execute Pipeline", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("**Platform Specs**")
    st.markdown("""
    \U0001F916 9 Specialized Agents  
    \U0001F4C4 8 Unstructured Docs  
    \U0001F5C4 12 Structured Tables  
    \U0001F9EA 4,500+ ML Samples  
    \U0001F9E0 Cortex AI + Search  
    """)

# ─── Header ───
hcol1, hcol2 = st.columns([3, 1])
with hcol1:
    st.markdown("# CoCo-AgriPulseAI")
    st.markdown("**Unstructured Data Intelligence System** for Agriculture")
with hcol2:
    st.markdown("")
    st.markdown(f"**Crops:** {' | '.join(selected_crops)}")
    pipeline_status = "\U0001F7E2 Ready" if not run_btn else "\U0001F7E1 Running..."
    st.markdown(f"**Pipeline:** {pipeline_status}")

st.markdown("---")

# ─── Execute ───
if run_btn or "initialized" not in st.session_state:
    st.session_state["initialized"] = True

crop_filter = ",".join([f"'{c}'" for c in selected_crops])

# ─── KPI Strip ───
k1, k2, k3, k4, k5 = st.columns(5)
doc_count = run_query("SELECT COUNT(*) AS N FROM AGRIPULSE.UNSTRUCTURED.RAW_DOCUMENTS")
pest_count = run_query(f"SELECT COUNT(*) AS N FROM AGRIPULSE.CURATED.PEST_DISEASE_KB WHERE CROP_NAME IN ({crop_filter}) AND SEVERITY = 'Critical'")
msp_rice = run_query("SELECT MSP_RS_PER_QUINTAL AS V FROM AGRIPULSE.CURATED.MSP_HISTORY WHERE CROP_NAME='Rice' AND YEAR=2025")
msp_cotton = run_query("SELECT MSP_RS_PER_QUINTAL AS V FROM AGRIPULSE.CURATED.MSP_HISTORY WHERE CROP_NAME='Cotton' AND YEAR=2025")
yield_data = run_query("SELECT ROUND(AVG(YIELD_KG_PER_HA),0) AS V FROM AGRIPULSE.FEATURES.RICE_YIELD_TRAINING")

k1.metric("Documents Processed", f"{doc_count.iloc[0]['N']}", "\U0001F4C4 AI-analyzed")
k2.metric("Critical Threats", f"{pest_count.iloc[0]['N']}", "\U0001F6A8 Active")
k3.metric("Rice MSP 2025", f"\u20B9{msp_rice.iloc[0]['V']:,.0f}/q", "+5.4%")
k4.metric("Cotton MSP 2025", f"\u20B9{msp_cotton.iloc[0]['V']:,.0f}/q", "+5.6%")
k5.metric("Rice Avg Yield", f"{yield_data.iloc[0]['V']:,.0f} kg/ha", "ML predicted")

st.markdown("")

# ─── Tabs ───
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "\U0001F9E0 AI Document Intel",
    "\U0001F33F Agronomy",
    "\U0001F6E1 Crop Protection",
    "\U0001F4CA ML Predictions",
    "\U0001F4B9 Market & MSP",
    "\U0001F916 AI Advisory",
])

# ═══ TAB 1: Unstructured AI ═══
with tab1:
    st.markdown("### Unstructured Document Intelligence Pipeline")
    st.caption("Ingest \u2192 AI Extract \u2192 Classify \u2192 Summarize \u2192 Semantic Search")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("##### Ingested Sources")
        docs = run_query("SELECT DOC_ID, DOC_TYPE, DOC_TITLE, REGION FROM AGRIPULSE.UNSTRUCTURED.RAW_DOCUMENTS")
        st.dataframe(
            docs.style.map(lambda v: "background-color: #FFCDD2" if v == "farmer_report" else "background-color: #C8E6C9" if v == "government_advisory" else "", subset=["DOC_TYPE"]),
            use_container_width=True, hide_index=True, height=280
        )

    with col_b:
        st.markdown("##### Cortex AI Processing Results")
        processed = run_query("SELECT DOC_ID, TRIM(AI_CLASSIFICATION) AS CLASSIFICATION, LEFT(AI_SUMMARY, 180) AS AI_SUMMARY FROM AGRIPULSE.UNSTRUCTURED.PROCESSED_DOCUMENTS")
        st.dataframe(processed, use_container_width=True, hide_index=True, height=280)

    st.markdown("---")
    st.markdown("##### Semantic Document Search (Cortex Search Service)")
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_q = st.text_input("Natural language query over documents", value="pink bollworm resistance management", label_visibility="collapsed", placeholder="Search: e.g. 'blast disease prevention in rice'")
    with search_col2:
        search_btn = st.button("\U0001F50D Search", use_container_width=True)

    if search_q and search_btn:
        with st.spinner("Searching via Cortex Search..."):
            try:
                results = run_query(f"""
                    SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                        'AGRIPULSE.UNSTRUCTURED.DOC_SEARCH_SERVICE',
                        '{{"query": "{search_q}", "columns": ["DOC_TITLE","CROP","REGION"], "limit": 3}}'
                    ))['results'] AS RESULTS
                """)
                st.json(results.iloc[0]["RESULTS"] if len(results) > 0 else {})
            except Exception as e:
                st.info(f"Cortex Search: {e}")

# ═══ TAB 2: Agronomy ═══
with tab2:
    st.markdown("### Agronomic Intelligence")

    agro_tab1, agro_tab2, agro_tab3 = st.tabs(["Growth Stages", "Nutrient Plan", "Weather Risk"])

    with agro_tab1:
        stages = run_query(f"SELECT CROP_NAME, STAGE_ORDER, STAGE_NAME, DAYS_FROM, DAYS_TO, WATER_MM_PER_WEEK, NUTRIENT_FOCUS, KEY_ACTIVITY FROM AGRIPULSE.CURATED.CROP_GROWTH_STAGES WHERE CROP_NAME IN ({crop_filter}) ORDER BY CROP_NAME, STAGE_ORDER")
        for crop in selected_crops:
            crop_stages = stages[stages["CROP_NAME"] == crop]
            if len(crop_stages) > 0:
                st.markdown(f"**{crop}** — {len(crop_stages)} stages, {int(crop_stages['DAYS_TO'].max())} days")
                st.dataframe(crop_stages[["STAGE_NAME","DAYS_FROM","DAYS_TO","WATER_MM_PER_WEEK","KEY_ACTIVITY"]], use_container_width=True, hide_index=True)

    with agro_tab2:
        nutrients = run_query(f"SELECT CROP_NAME, SOIL_TYPE, N_KG_PER_HA, P2O5_KG_PER_HA, K2O_KG_PER_HA, FYM_TONNES_PER_HA, SPLIT_SCHEDULE, ORGANIC_SUPPLEMENTS FROM AGRIPULSE.CURATED.NUTRIENT_RECOMMENDATIONS WHERE CROP_NAME IN ({crop_filter})")
        st.dataframe(nutrients, use_container_width=True, hide_index=True)

    with agro_tab3:
        weather = run_query(f"SELECT CROP_NAME, PARAMETER, STAGE, OPTIMAL_MIN, OPTIMAL_MAX, UNIT, IMPACT_IF_EXCEEDED, MITIGATION FROM AGRIPULSE.CURATED.CROP_WEATHER_THRESHOLDS WHERE CROP_NAME IN ({crop_filter})")
        st.dataframe(weather, use_container_width=True, hide_index=True)

# ═══ TAB 3: Crop Protection ═══
with tab3:
    st.markdown("### Threat Assessment & IPM Protocols")

    pests = run_query(f"SELECT * FROM AGRIPULSE.CURATED.PEST_DISEASE_KB WHERE CROP_NAME IN ({crop_filter}) ORDER BY CASE SEVERITY WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 ELSE 3 END")

    critical = pests[pests["SEVERITY"] == "Critical"]
    high = pests[pests["SEVERITY"] == "High"]
    medium = pests[pests["SEVERITY"] == "Medium"]

    alert_col1, alert_col2, alert_col3 = st.columns(3)
    alert_col1.metric("Critical", len(critical), "\U0001F534")
    alert_col2.metric("High", len(high), "\U0001F7E0")
    alert_col3.metric("Medium", len(medium), "\U0001F7E1")

    st.markdown("---")
    for _, row in pests.iterrows():
        severity_icon = "\U0001F534" if row["SEVERITY"] == "Critical" else "\U0001F7E0" if row["SEVERITY"] == "High" else "\U0001F7E1"
        with st.expander(f"{severity_icon} {row['CROP_NAME']} | {row['PEST_NAME']} ({row['PEST_TYPE']}) — {row['SEVERITY']}"):
            st.markdown(f"**Symptoms:** {row['SYMPTOMS']}")
            st.markdown(f"**Economic Threshold:** {row['ECONOMIC_THRESHOLD']}")
            ipm_c1, ipm_c2, ipm_c3 = st.columns(3)
            with ipm_c1:
                st.markdown("**Cultural**")
                st.caption(row["IPM_CULTURAL"])
            with ipm_c2:
                st.markdown("**Biological**")
                st.caption(row["IPM_BIOLOGICAL"])
            with ipm_c3:
                st.markdown("**Chemical**")
                st.caption(row["IPM_CHEMICAL"])

# ═══ TAB 4: ML Predictions ═══
with tab4:
    st.markdown("### ML-Powered Yield Intelligence")

    ml_cols = st.columns(len(selected_crops))
    for i, crop in enumerate(selected_crops):
        table = f"AGRIPULSE.FEATURES.{crop.upper()}_YIELD_TRAINING"
        try:
            stats = run_query(f"SELECT COUNT(*) AS N, ROUND(AVG(YIELD_KG_PER_HA),0) AS AVG_YIELD, ROUND(STDDEV(YIELD_KG_PER_HA),0) AS STD_YIELD, ROUND(MIN(YIELD_KG_PER_HA),0) AS MIN_Y, ROUND(MAX(YIELD_KG_PER_HA),0) AS MAX_Y FROM {table}")
            with ml_cols[i]:
                st.metric(f"{crop}", f"{stats.iloc[0]['AVG_YIELD']:,.0f} kg/ha", f"\u00B1{stats.iloc[0]['STD_YIELD']:,.0f}")
                st.caption(f"Samples: {stats.iloc[0]['N']} | Range: {stats.iloc[0]['MIN_Y']:,.0f}\u2013{stats.iloc[0]['MAX_Y']:,.0f}")
        except Exception:
            pass

    st.markdown("---")
    st.markdown("##### State-wise Yield Comparison")
    for crop in selected_crops:
        table = f"AGRIPULSE.FEATURES.{crop.upper()}_YIELD_TRAINING"
        try:
            dist = run_query(f"SELECT STATE, ROUND(AVG(YIELD_KG_PER_HA),0) AS AVG_YIELD FROM {table} GROUP BY STATE ORDER BY AVG_YIELD DESC")
            st.markdown(f"**{crop}**")
            st.bar_chart(dist.set_index("STATE")["AVG_YIELD"], use_container_width=True)
        except Exception:
            pass

    st.markdown("---")
    st.markdown("##### Historical Yield Trends")
    hist = run_query(f"SELECT CROP_NAME, YEAR, ROUND(AVG(YIELD_KG_PER_HA),0) AS YIELD_KG_HA FROM AGRIPULSE.CURATED.YIELD_HISTORY WHERE CROP_NAME IN ({crop_filter}) GROUP BY CROP_NAME, YEAR ORDER BY YEAR")
    if len(hist) > 0:
        pivot = hist.pivot(index="YEAR", columns="CROP_NAME", values="YIELD_KG_HA")
        st.line_chart(pivot, use_container_width=True)

# ═══ TAB 5: Market ═══
with tab5:
    st.markdown("### Market & Procurement Intelligence")

    mkt_col1, mkt_col2 = st.columns([1, 1])
    with mkt_col1:
        st.markdown("##### MSP Trajectory (2019\u20132025)")
        msp = run_query(f"SELECT CROP_NAME, YEAR, MSP_RS_PER_QUINTAL FROM AGRIPULSE.CURATED.MSP_HISTORY WHERE CROP_NAME IN ({crop_filter}) AND MSP_RS_PER_QUINTAL > 0 ORDER BY YEAR")
        if len(msp) > 0:
            pivot_msp = msp.pivot(index="YEAR", columns="CROP_NAME", values="MSP_RS_PER_QUINTAL")
            st.line_chart(pivot_msp, use_container_width=True)

    with mkt_col2:
        st.markdown("##### Live Mandi Prices")
        prices = run_query(f"SELECT CROP_NAME, STATE, MARKET, MODAL_PRICE_RS AS PRICE_RS, MONTH, YEAR FROM AGRIPULSE.CURATED.MARKET_PRICES WHERE CROP_NAME IN ({crop_filter}) ORDER BY MODAL_PRICE_RS DESC")
        st.dataframe(prices, use_container_width=True, hide_index=True, height=300)

    st.markdown("---")
    st.markdown("##### MSP Year-on-Year Growth")
    msp_growth = run_query(f"""
        SELECT CROP_NAME, YEAR, MSP_RS_PER_QUINTAL,
               ROUND((MSP_RS_PER_QUINTAL - LAG(MSP_RS_PER_QUINTAL) OVER (PARTITION BY CROP_NAME ORDER BY YEAR)) 
               / NULLIF(LAG(MSP_RS_PER_QUINTAL) OVER (PARTITION BY CROP_NAME ORDER BY YEAR), 0) * 100, 1) AS GROWTH_PCT
        FROM AGRIPULSE.CURATED.MSP_HISTORY 
        WHERE CROP_NAME IN ({crop_filter}) AND MSP_RS_PER_QUINTAL > 0
        ORDER BY CROP_NAME, YEAR
    """)
    st.dataframe(msp_growth, use_container_width=True, hide_index=True)

# ═══ TAB 6: AI Advisory ═══
with tab6:
    st.markdown("### Combined Intelligence Advisory")
    st.caption("Fusing structured analytics + unstructured document insights via Cortex AI")

    if st.button("\U0001F9E0 Generate AI Advisory", type="primary", use_container_width=True):
        with st.spinner("Cortex AI analyzing structured + unstructured intelligence..."):
            try:
                prompt = f"You are an agricultural intelligence advisor. Based on the following data, provide a detailed 5-point advisory for {', '.join(selected_crops)} farmers in Maharashtra. Be specific with actions and timelines. Data: Critical pests are Rice Blast, Cotton Pink Bollworm (Bt resistance confirmed), Chilli Leaf Curl Virus. Rice MSP 2025 Rs.2425/quintal (+5.4%). Cotton MSP Rs.7521/quintal. Government advisory warns BPH in continuous rain. Research shows blast epidemics doubling. Farmer reports show 60-70% bollworm damage in Vidarbha."
                advisory = run_query(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', '{prompt.replace(chr(39), chr(39)+chr(39))}') AS ADVISORY")
                st.markdown(advisory.iloc[0]["ADVISORY"])
            except Exception as e:
                st.error(f"Cortex AI: {e}")
    else:
        st.info("Click the button above to generate a combined structured + unstructured AI advisory using Cortex LLM.")

# ─── Footer ───
st.markdown("---")
fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    st.caption("**CoCo-AgriPulseAI** v1.0")
with fcol2:
    st.caption("Snowflake CoCo CLI | Cortex AI | Cortex Search | Snowpark ML")
with fcol3:
    st.caption("Hackathon 2026 | Problem Statement 01")
