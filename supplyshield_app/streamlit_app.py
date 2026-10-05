import json
import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()
st.set_page_config(page_title="SupplyShield AI", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=60)
def q(sql):
    return session.sql(sql).to_pandas()

def run_agent(question):
    safe = question.replace("'", "''")
    sql = """SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
      'SUPPLYSHIELD.CORE.SUPPLYSHIELD_AGENT',
      $$ {"messages":[{"role":"user","content":[{"type":"text","text":"%s"}]}],"stream":false} $$
    )) AS RESPONSE""" % safe
    raw = q(sql).iloc[0]["RESPONSE"]
    if isinstance(raw, str):
        raw = json.loads(raw)
    return "\n".join(x.get("text","") for x in raw.get("content",[]) if x.get("type")=="text") or str(raw)

st.markdown("""<style>
.block-container{padding-top:1.4rem}
.hero{padding:22px 26px;border-radius:14px;background:linear-gradient(135deg,#07131f,#12334a);color:white;margin-bottom:18px}
.hero h1{font-size:2.3rem;margin:0}.hero p{font-size:1rem;color:#c7d8e5}
.card{border:1px solid #d9e2ea;border-radius:12px;padding:16px;background:#fff}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="hero"><h1>🛡️ SupplyShield AI</h1>
<p>Governed supply-chain intelligence that helps teams prevent shortages before customers feel the impact.</p></div>""", unsafe_allow_html=True)

risk = q("SELECT * FROM SUPPLYSHIELD.CORE.V_STOCKOUT_RISK ORDER BY RISK_SCORE DESC")
sup = q("SELECT * FROM SUPPLYSHIELD.CORE.V_SUPPLIER_PERFORMANCE ORDER BY ON_TIME_DELIVERY_RATE")
impact = q("SELECT * FROM SUPPLYSHIELD.CORE.V_DOWNSTREAM_IMPACT ORDER BY RISK_SCORE DESC")

k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("High-risk part/site pairs", int((risk["RISK_LEVEL"]=="HIGH").sum()))
k2.metric("Delayed shipments", int(risk["DELAYED_SHIPMENTS"].sum()))
k3.metric("Orders exposed", int(risk["OPEN_ORDER_COUNT"].sum()))
k4.metric("Suppliers monitored", len(sup))
k5.metric("Compute model", "SQL-first")

st.markdown("### 🚨 Risk radar")
c1,c2 = st.columns([1.15,1])
with c1:
    st.dataframe(risk[["PLANT_NAME","PART_NAME","CRITICALITY","DAYS_OF_COVER","DELAYED_SHIPMENTS","RISK_SCORE","RISK_LEVEL"]], use_container_width=True, hide_index=True)
with c2:
    top = risk.iloc[0]
    html = """<div class="card"><h4>Top intervention</h4>
<p><b>{}</b> at <b>{}</b> is <b>{}</b>.</p>
<p>Inventory cover: <b>{:.1f} days</b><br>Delayed shipments: <b>{}</b><br>Risk score: <b>{}/100</b></p>
<p><b>Decision:</b> investigate the delayed supplier before the safety-stock boundary is breached.</p></div>""".format(
        top["PART_NAME"], top["PLANT_NAME"], top["RISK_LEVEL"], top["DAYS_OF_COVER"], int(top["DELAYED_SHIPMENTS"]), int(top["RISK_SCORE"]))
    st.markdown(html, unsafe_allow_html=True)

st.markdown("### 🔗 Supplier → Part → Plant → Shipment → Order → Customer")
st.dataframe(impact[["SUPPLIER_NAME","PART_NAME","PLANT_NAME","SHIPMENT_ID","STATUS","CUSTOMER_NAME","ORDER_ID","ORDER_QTY","REQUIRED_DATE","DELAY_DAYS"]], use_container_width=True, hide_index=True)

st.markdown("### 💬 Ask SupplyShield")
examples = [
    "Which suppliers are putting Plant P07 at risk, and which customer orders are affected?",
    "What is the on-time delivery rate by supplier?",
    "How many days of cover does Plant P07 have for critical parts?",
    "Which delayed shipment has the largest downstream customer impact?"
]
question = st.selectbox("Try a governed business question", examples)
if st.button("Run governed analysis", type="primary", use_container_width=True):
    with st.spinner("Coordinating semantic analytics in Snowflake..."):
        try:
            st.markdown("#### SupplyShield decision")
            st.write(run_agent(question))
        except Exception as e:
            st.error("Agent execution failed: " + str(e))

st.markdown("### 🧾 Evidence layer")
st.caption("Deterministic metrics stay in Snowflake. Cortex is used for natural-language orchestration and explanation.")
st.dataframe(sup[["SUPPLIER_NAME","RELIABILITY_SCORE","ON_TIME_DELIVERY_RATE","AVG_DELAY_DAYS","DELAYED_SHIPMENT_COUNT","RECENT_INCIDENTS","RISK_TIER"]], use_container_width=True, hide_index=True)
st.markdown("---")
st.caption("SupplyShield AI • Snowflake CoCo CLI Hackathon • Problem Statement 05 • Synthetic demonstration data")
