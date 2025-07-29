import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

# Allowed users and password
allowed_users = ['el dlo3a', 'Nour', 'zizi', 'danial', 'Abdo', 'destroyer of the galaxy', 'Ali' , 'Ahmed Hanafy' ]
password = '12345resva'
allowed_users_lower = [user.lower() for user in allowed_users]

st.set_page_config(page_title="ReadyMode Call Audit Tool", layout="wide")

# Google Analytics GA4 Measurement ID
GA4_MEASUREMENT_ID = "G-X73LCNERD6"

ga4_code = f"""
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA4_MEASUREMENT_ID}');
</script>
"""

st.markdown(ga4_code, unsafe_allow_html=True)

# Initialize session state variables if not present
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# Login form
if not st.session_state.authenticated:
    st.title("Login to RES-VA Call Audit Tool")

    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        if username_input.strip().lower() in allowed_users_lower and password_input == password:
            st.session_state.authenticated = True
            st.session_state.username = username_input.strip().lower()
            st.success("Login successful. Welcome!")
        else:
            st.error("Invalid username or password.")
    st.stop()

# Authenticated user interface
st.sidebar.title("Navigation")
st.sidebar.write(f"**Logged in as:** {st.session_state.username}")

if st.sidebar.button("Logout"):
    logout()

st.sidebar.markdown("---")
st.sidebar.title("Filters")

uploaded_file = st.sidebar.file_uploader("Upload your exported Call Log CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Clean column names and Disposition values
    df.columns = df.columns.str.strip()
    if 'Disposition' in df.columns:
        df['Disposition'] = df['Disposition'].astype(str).str.strip()

    # Fix Recording Length if misread as time
    if 'Recording Length (Seconds)' in df.columns and df['Recording Length (Seconds)'].dtype == 'object':
        try:
            df['Recording Length (Seconds)'] = pd.to_datetime(
                df['Recording Length (Seconds)'], format='%I:%M:%S %p', errors='coerce'
            )
            df['Recording Length (Seconds)'] = (
                df['Recording Length (Seconds)'].dt.hour * 3600 +
                df['Recording Length (Seconds)'].dt.minute * 60 +
                df['Recording Length (Seconds)'].dt.second
            )
        except:
            pass

    df['Recording Length (Seconds)'] = pd.to_numeric(df['Recording Length (Seconds)'], errors='coerce')

    def format_duration(seconds):
        if pd.isnull(seconds):
            return ""
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes}:{seconds:02d}"

    df['Recording Length (Formatted)'] = df['Recording Length (Seconds)'].apply(format_duration)

    # Flagging logic
    df['Flag - Voicemail Over 15 sec'] = df.apply(
        lambda row: 'Check' if row['Disposition'] == 'Voicemail' and row['Recording Length (Seconds)'] > 15 else '', axis=1)

    df['Flag - Dead Call Over 15 sec'] = df.apply(
        lambda row: 'Check' if row['Disposition'] == 'Dead Call' and row['Recording Length (Seconds)'] > 15 else '', axis=1)

    df['Flag - Decision Maker - NYI Under 10 sec'] = df.apply(
        lambda row: 'Check' if row['Disposition'] == 'Decision Maker - NYI' and row['Recording Length (Seconds)'] < 10 else '', axis=1)

    df['Flag - Wrong Number Under 10 sec'] = df.apply(
        lambda row: 'Check' if row['Disposition'] == 'Wrong Number' and row['Recording Length (Seconds)'] < 10 else '', axis=1)

    df['Flag - Unknown Under 5 sec'] = df.apply(
        lambda row: 'Check' if row['Disposition'] == 'Unknown' and row['Recording Length (Seconds)'] < 5 else '', axis=1)

    # Label durations
    def classify_duration(sec):
        if pd.isnull(sec):
            return ""
        if sec < 5:
            return "Very Short"
        elif sec < 15:
            return "Short"
        else:
            return "OK"

    df['Call Duration Label'] = df['Recording Length (Seconds)'].apply(classify_duration)

    # --- Filters in sidebar ---
    agent_options = ["All"] + sorted(df['Agent Name'].dropna().unique().tolist()) if 'Agent Name' in df.columns else ["All"]
    disposition_options = ["All"] + sorted(df['Disposition'].dropna().unique().tolist()) if 'Disposition' in df.columns else ["All"]

    agent_filter = st.sidebar.selectbox("Filter by Agent", options=agent_options)
    disposition_filter = st.sidebar.selectbox("Filter by Disposition", options=disposition_options)

    filtered_df = df.copy()
    if agent_filter != "All" and 'Agent Name' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Agent Name'] == agent_filter]
    if disposition_filter != "All" and 'Disposition' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Disposition'] == disposition_filter]

    # Agent summary
    if 'Agent Name' in df.columns:
        agent_summary = df.groupby('Agent Name').agg({
            'Flag - Voicemail Over 15 sec': lambda x: (x == 'Check').sum(),
            'Flag - Dead Call Over 15 sec': lambda x: (x == 'Check').sum(),
            'Flag - Decision Maker - NYI Under 10 sec': lambda x: (x == 'Check').sum(),
            'Flag - Wrong Number Under 10 sec': lambda x: (x == 'Check').sum(),
            'Flag - Unknown Under 5 sec': lambda x: (x == 'Check').sum(),
            'Disposition': lambda x: (x == 'Dead Call').sum(),  # Total Dead Calls
        }).reset_index()
        
        # Add Total Unknown Calls column
        agent_summary['Total Unknown Calls'] = df.groupby('Agent Name')['Disposition'].apply(
            lambda x: (x == 'Unknown').sum()
        ).reset_index(0, drop=True)
        
        # Rename the Disposition column to Total Dead Calls
        agent_summary = agent_summary.rename(columns={'Disposition': 'Total Dead Calls'})
    else:
        agent_summary = pd.DataFrame()

    # Overall Summary
    def get_flag_count(flag_col):
        if flag_col in df.columns:
            return df[flag_col].value_counts().get('Check', 0)
        return 0

    total_voicemail = get_flag_count('Flag - Voicemail Over 15 sec')
    total_deadcall = get_flag_count('Flag - Dead Call Over 15 sec')
    total_decision_maker_nyi = get_flag_count('Flag - Decision Maker - NYI Under 10 sec')
    total_wrong_number_under = get_flag_count('Flag - Wrong Number Under 10 sec')
    total_unknown_5sec = get_flag_count('Flag - Unknown Under 5 sec')

    total_flagged = df[[
        'Flag - Voicemail Over 15 sec',
        'Flag - Dead Call Over 15 sec',
        'Flag - Decision Maker - NYI Under 10 sec',
        'Flag - Wrong Number Under 10 sec',
        'Flag - Unknown Under 5 sec'
    ]].apply(lambda x: 'Check' in x.values, axis=1).sum() if not df.empty else 0

    st.write("### Overall Summary")
    
    st.info(f"""
    - **Voicemail Calls Over 15 sec:** {total_voicemail}
    - **Dead Calls Over 15 sec:** {total_deadcall}
    - **Decision Maker - NYI Under 10 sec:** {total_decision_maker_nyi}
    - **Wrong Number Calls Under 10 sec:** {total_wrong_number_under}
    - **Unknown Calls Under 5 sec:** {total_unknown_5sec}
    - **Total Flagged Calls:** {total_flagged}
    """)

    st.write("### Agent Summary - Issues Overview")
    if not agent_summary.empty:
        st.dataframe(agent_summary)
    else:
        st.write("No agent data to show.")

    flagged_calls = filtered_df[
        (filtered_df.get('Flag - Voicemail Over 15 sec', '') == 'Check') |
        (filtered_df.get('Flag - Dead Call Over 15 sec', '') == 'Check') |
        (filtered_df.get('Flag - Decision Maker - NYI Under 10 sec', '') == 'Check') |
        (filtered_df.get('Flag - Wrong Number Under 10 sec', '') == 'Check') |
        (filtered_df.get('Flag - Unknown Under 5 sec', '') == 'Check')
    ]

    st.write("### Flagged Calls")
    
    if not flagged_calls.empty:
        # Create columns for flagged calls data and pie chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(flagged_calls[[
                'Agent Name', 'Phone Number', 'Disposition', 'Recording Length (Formatted)',
                'Call Duration Label',
                'Flag - Voicemail Over 15 sec',
                'Flag - Dead Call Over 15 sec',
                'Flag - Decision Maker - NYI Under 10 sec',
                'Flag - Wrong Number Under 10 sec',
                'Flag - Unknown Under 5 sec'
            ]])
        
        with col2:
            # Create pie chart for total calls by disposition from the full filtered dataset
            disposition_counts = filtered_df['Disposition'].value_counts()
            
            # Filter to show only the specific dispositions we want
            key_dispositions = ['Dead Call', 'Decision Maker - NYI', 'Wrong Number', 'Unknown']
            filtered_counts = {disp: disposition_counts.get(disp, 0) for disp in key_dispositions}
            
            # Filter out zero values for cleaner chart
            filtered_counts = {k: v for k, v in filtered_counts.items() if v > 0}
            
            if filtered_counts:
                fig_pie = px.pie(
                    values=list(filtered_counts.values()),
                    names=list(filtered_counts.keys()),
                    title=f'Total Calls by Disposition ({len(filtered_df)} total)',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Aya's Idea component positioned under the chart
                st.markdown(
                    """
                    <div style="
                        text-align: center;
                        margin-top: 5px;
                        margin-left: 120px;
                        padding: 8px 12px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 20px;
                        color: white;
                        font-size: 14px;
                        font-weight: bold;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                        animation: bounce 2s infinite;
                        display: inline-block;
                    ">
                        💡 Aya's Idea ↑
                    </div>
                    
                    <style>
                    @keyframes bounce {
                        0%, 20%, 50%, 80%, 100% {
                            transform: translateY(0);
                        }
                        40% {
                            transform: translateY(-5px);
                        }
                        60% {
                            transform: translateY(-3px);
                        }
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("No calls to display in chart")
    else:
        st.write("No flagged calls found for the selected filters.")

    # Download buttons
    if not agent_summary.empty:
        st.download_button("Download Agent Summary", agent_summary.to_csv(index=False).encode('utf-8'), "agent_summary_flags.csv", "text/csv")
    if not flagged_calls.empty:
        st.download_button("Download Flagged Calls", flagged_calls.to_csv(index=False).encode('utf-8'), "call_log_with_flags.csv", "text/csv")
    if not filtered_df.empty:
        st.download_button("Download All Filtered Data", filtered_df.to_csv(index=False).encode('utf-8'), "filtered_call_log.csv", "text/csv")
else:
    st.info("Please upload your exported call log CSV file to start the audit.")


st.markdown(
    """
    <div style="
        position: fixed;
        bottom: 10px;
        width: 100%;
        text-align: center;
        font-size: 16px;
        color: white;
        background: linear-gradient(to right, #00c6ff, #0072ff);
        padding: 10px 0;
        border-radius: 8px;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.3);
        animation: fadeIn 2s ease-in-out;
    ">
        App developed by <strong>Mohamed Abdo NUMBER ONE</strong>
    </div>

    <style>
    @keyframes fadeIn {{
        0% {{ opacity: 0; transform: translateY(20px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
    a.dev-link:hover {{
        color: #ffeb3b !important;
        text-decoration: none !important;
        cursor: pointer;
    }}
    </style>
    """,
    unsafe_allow_html=True
)