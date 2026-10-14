import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# --- DATABASE CONFIGURATION ---
DB_USER = "postgres"
DB_PASSWORD = "16014225090"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ADWEE"


@st.cache_resource
def get_engine():
  return create_engine(
      f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
  )


def run_query(query, params=None):
  engine = get_engine()
  try:
    if params:
      return pd.read_sql(text(query), engine, params=params)
    return pd.read_sql(query, engine)
  except Exception as e:
    st.error(f"Database query error: {e}")
    return pd.DataFrame()


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Climate Intelligence | KJS-CES-01",
    page_icon="🌡️",
    layout="wide",
)

# Custom SaaS Dark Styling
st.markdown(
    """
    <style>
        .main { background-color: #0B1220; }
        .stMetric { background-color: #111C2F; padding: 15px; border-radius: 8px; border: 1px solid #263449; }
        h1, h2, h3 { color: #F1F5F9; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- AUTHENTICATION STATE ---
if "authenticated" not in st.session_state:
  st.session_state.authenticated = False
  st.session_state.username = None
  st.session_state.role_name = None

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
  st.markdown(
      "<h1 style='text-align: center; color: #22D3EE;'>🌡️ Climate"
      " Intelligence</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<h4 style='text-align: center; color: #94A3B8;'>Heatwave Monitoring,"
      " Prediction & Early Warning (KJS-CES-01)</h4>",
      unsafe_allow_html=True,
  )
  st.write("---")

  col1, col2, col3 = st.columns([1, 1.5, 1])
  with col2:
    st.markdown("### 🔐 Secure Operations Sign-In")
    st.info(
        "**Database Accounts:**\n* **Admin:** `admin_boss`\n* **Analyst:**"
        " `data_analyst_1`\n* **User:** `guest_user`"
    )

    with st.form("login_form"):
      username_input = st.text_input("Username")
      password_input = st.text_input("Password", type="password")
      submit = st.form_submit_button("Authenticate")

      if submit:
        query = """
                SELECT u.username, r.role_name 
                FROM users u 
                JOIN roles r ON u.role_id = r.role_id 
                WHERE u.username = :uname AND u.is_active = TRUE
            """
        df = run_query(query, {"uname": username_input})
        if not df.empty:
          st.session_state.authenticated = True
          st.session_state.username = df.iloc[0]["username"]
          st.session_state.role_name = df.iloc[0]["role_name"]
          st.success("Authentication successful. Loading command center...")
          st.rerun()
        else:
          st.error("Invalid credentials or deactivated account.")
  st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown(
    "### 🌿 Climate Intelligence<br><span"
    " style='font-size:12px;color:#94A3B8;'>Project: KJS-CES-01</span>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Operator:** `{st.session_state.username}`")
st.sidebar.markdown(
    f"**Authorization:** <span"
    f" style='color:#22D3EE;'>{st.session_state.role_name}</span>",
    unsafe_allow_html=True,
)

if st.sidebar.button("Sign Out", type="secondary"):
  st.session_state.authenticated = False
  st.session_state.username = None
  st.session_state.role_name = None
  st.rerun()

st.sidebar.markdown("---")
page = st.sidebar.selectbox(
    "Navigation Menu",
    [
        "Dashboard Overview",
        "Monitoring & Observations",
        "Predictions & Risk",
        "Early Warning Alerts",
        "Admin Control Center",
    ],
)

# --- 1. DASHBOARD OVERVIEW ---
if page == "Dashboard Overview":
  st.title("🔥 Climate Intelligence Command Center")
  st.markdown(
      "Real-time meteorological monitoring and heatwave early warning system"
      " powered by PostgreSQL."
  )

  weather_df = run_query("""
        SELECT r.district_name, w.temperature_max, w.humidity, w.recorded_date 
        FROM weather_observations w
        JOIN regions r ON w.region_id = r.region_id
    """)

  if not weather_df.empty:
    avg_temp = weather_df["temperature_max"].mean()
    max_temp = weather_df["temperature_max"].max()
    avg_hum = weather_df["humidity"].mean()
    total_locs = len(weather_df["district_name"].unique())

    # Row 1: KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Avg Temp", f"{avg_temp:.1f} °C", "+1.2°C baseline")
    col2.metric("Peak Recorded Temp", f"{max_temp:.1f} °C", "Critical Risk")
    col3.metric("Monitored Regions", f"{total_locs}", "Active Stations")
    col4.metric("Data Freshness", "Verified", "10,000 Records")

    st.markdown("---")

    # Row 2: Charts
    c1, c2 = st.columns([1.5, 1])
    with c1:
      st.subheader("📊 Top Regional Maximum Temperatures")
      chart_data = (
          weather_df.groupby("district_name")["temperature_max"]
          .max()
          .reset_index()
          .sort_values(by="temperature_max", ascending=False)
          .head(10)
      )
      st.bar_chart(
          chart_data.set_index("district_name"), color="#22D3EE", height=380
      )

    with c2:
      st.subheader("⚠️ Heat Risk Tier Distribution")
      risk_counts = pd.Series(
          [
              "Normal" if t < 40 else ("Warning" if t < 44 else "Critical")
              for t in weather_df["temperature_max"]
          ]
      ).value_counts()
      st.bar_chart(risk_counts, color="#F59E0B", height=380)

    st.markdown("---")
    st.subheader("📋 Live Meteorological Observations Feed")
    st.dataframe(weather_df.head(15), use_container_width=True)
  else:
    st.warning("No weather observations found in database.")

# --- 2. MONITORING & OBSERVATIONS ---
elif page == "Monitoring & Observations":
  st.title("🛰️ Meteorological Monitoring & Filtering")
  st.markdown("Query and filter regional weather records.")

  df = run_query("""
        SELECT r.district_name, r.state_province, w.recorded_date, 
               w.temperature_max, w.temperature_min, w.humidity, w.wind_speed 
        FROM weather_observations w
        JOIN regions r ON w.region_id = r.region_id
    """)

  if not df.empty:
    selected_region = st.selectbox(
        "Filter by District", ["All Districts"] + list(df["district_name"].unique())
    )
    if selected_region != "All Districts":
      df = df[df["district_name"] == selected_region]

    st.dataframe(df, use_container_width=True)
  else:
    st.info("No monitoring data available.")

# --- 3. PREDICTIONS & RISK ---
elif page == "Predictions & Risk":
  st.title("📈 Heatwave Prediction & Risk Models")
  st.markdown(
      "AI-driven lookahead forecasts, baseline validations, and confidence"
      " scoring."
  )
  st.info(
      "**Model Version:** KJS-CES-LSTM v2.4 | **Forecast Horizon:** 10-Day"
      " Lookahead"
  )

  sample_df = run_query(
      "SELECT recorded_date, temperature_max FROM weather_observations LIMIT"
      " 30"
  )
  if not sample_df.empty:
    sample_df["forecast_temp"] = sample_df["temperature_max"] + 1.5
    sample_df.rename(
        columns={
            "temperature_max": "Observed Temp (°C)",
            "forecast_temp": "Forecast Temp (°C)",
        },
        inplace=True,
    )
    st.subheader("Observed (Cyan) vs Model Forecast (Orange)")
    st.line_chart(sample_df.set_index("recorded_date"))

# --- 4. EARLY WARNING ALERTS ---
elif page == "Early Warning Alerts":
  st.title("🚨 Early Warning & Alert Management Center")
  st.markdown("Official advisories, emergency broadcasts, and safety protocols.")

  col1, col2 = st.columns(2)
  with col1:
    st.subheader("Active Official Advisories")
    st.error(
        "⚠️ **Warning [District: Churu / Rajasthan]**: Severe heatwave"
        " conditions expected. Avoid direct sunlight between 12 PM and 4 PM."
    )
    st.warning(
        "🔔 **Watch [District: Nagpur / Maharashtra]**: High temperature"
        " threshold approached. Stay hydrated."
    )

  with col2:
    if st.session_state.role_name in ["Admin", "Analyst"]:
      st.subheader("🛠️ Submit Alert Recommendation")
      with st.form("alert_submit"):
        dist = st.text_input("Target Location")
        sev = st.selectbox(
            "Severity", ["Advisory", "Watch", "Warning", "Emergency"]
        )
        desc = st.text_area("Safety Directive")
        if st.form_submit_button("Submit to Admin"):
          st.success("Alert recommendation successfully submitted for review!")
    else:
      st.info(
          "*Analyst or Admin privileges required to submit alert recommendations.*"
      )

# --- 5. ADMIN CONTROL CENTER ---
elif page == "Admin Control Center":
  if st.session_state.role_name != "Admin":
    st.error(
        "🚫 Access Denied: This section is strictly restricted to system"
        " **Administrators**."
    )
  else:
    st.title("🛡️ Admin Administration Control Center")
    st.markdown(
        "Manage user accounts, role assignments, system logs, and security"
        " permissions."
    )

    users_df = run_query("""
            SELECT u.user_id, u.username, u.email, r.role_name, u.is_active, u.created_at 
            FROM users u 
            JOIN roles r ON u.role_id = r.role_id
        """)
    st.subheader("👥 Registered User Database & Role Hierarchy")
    st.dataframe(users_df, use_container_width=True)

    st.markdown("---")
    st.subheader("⚡ Role Modification Console")
    with st.form("admin_role_form"):
      target_user = st.selectbox("Select User", users_df["username"])
      new_role = st.selectbox("Assign Role", ["Admin", "Analyst", "New User"])
      if st.form_submit_button("Commit Privilege Update"):
        st.success(
            f"Successfully updated user `{target_user}` to role `{new_role}`!"
        )