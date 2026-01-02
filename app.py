import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ---
st.set_page_config(page_title="Performance Analytics", layout="wide")

# ডিজাইন স্টাইল (সব আইকন রিমুভ করা হয়েছে)
st.markdown("""
    <style>
    .metric-card { 
        padding: 15px; border-radius: 12px; text-align: center; color: #1e293b; 
        background: #ffffff; border-top: 5px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .rework-border { border-top-color: #ef4444; background-color: #fff1f0; }
    .fp-border { border-top-color: #3b82f6; background-color: #e6f7ff; }
    .mrp-border { border-top-color: #10b981; background-color: #f6ffed; }
    .cad-border { border-top-color: #f59e0b; background-color: #fffbe6; }
    .ua-border { border-top-color: #8b5cf6; background-color: #f9f0ff; }
    .vanbree-border { border-top-color: #06b6d4; background-color: #e6fffb; }
    .total-border { border-top-color: #64748b; background-color: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

# --- ২. ডাটা কানেকশন ---
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["JSON_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_all_data():
    client = get_gspread_client()
    master_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    efficiency_id = "1hFboFpRmst54yVUfESFAZE_UgNdBsaBAmHYA-9z5eJE"

    # ডাটা পড়া
    df_m = pd.DataFrame(client.open_by_key(master_id).worksheet("DATA").get_all_records())
    df_y = pd.DataFrame(client.open_by_key(efficiency_id).worksheet("FINAL SUMMARY").get_all_records())

    # কলামের নাম ক্লিন করা (অদৃশ্য স্পেস মোছা)
    df_m.columns = [c.strip() for c in df_m.columns]
    df_y.columns = [c.strip() for c in df_y.columns]
    
    # ডাটা ফরম্যাটিং
    df_m['date'] = pd.to_datetime(df_m['date'], errors='coerce').dt.date
    df_m['Time'] = pd.to_numeric(df_m['Time'], errors='coerce').fillna(0)
    df_m['SQM'] = pd.to_numeric(df_m['SQM'], errors='coerce').fillna(0)
    
    # টেক্সট কলাম ক্লিন করা
    text_cols = ['Product', 'Job Type', 'Employee Type', 'Team', 'Name', 'Shift']
    for col in text_cols:
        if col in df_m.columns: df_m[col] = df_m[col].astype(str).str.strip()
    
    return df_m, df_y

try:
    df_master, df_yearly = load_all_data()

    # --- ৩. ন্যাভিগেশন (আইকন ছাড়া) ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Yearly Artist Profile", "Tracking System"])
    st.sidebar.markdown("---")
    
    st.sidebar.title("Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_master['date'].min())
    end_date = st.sidebar.date_input("End Date", df_master['date'].max())
    
    team_list = ["All"] + sorted(df_master['Team'].unique().tolist())
    team_selected = st.sidebar.selectbox("Team Name", team_list)
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_master['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])

    # ডাটা ফিল্টারিং
    mask = (df_master['date'] >= start_date) & (df_master['date'] <= end_date)
    if team_selected != "All": mask &= (df_master['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_master['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_master['Employee Type'] == emp_type_selected)
    df = df_master[mask].copy()

    # ম্যান-ডে এভারেজ ক্যালকুলেশন
    def get_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(len(subset) / man_days, 2)

    # --- ৪. ড্যাশবোর্ড পেজ ---
    if page == "Dashboard":
        st.markdown("<h2 style='text-align: center;'>Performance Analytics 2025</h2>", unsafe_allow_html=True)
        
        # কার্ড মেট্রিক্স
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{get_man_day_avg(df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{get_man_day_avg(df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{get_man_day_avg(df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{get_man_day_avg(df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{get_man_day_avg(df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree AVG<br><h2>{get_man_day_avg(df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tab_team, tab_artist = st.tabs(["Team Summary Breakdown", "Individual Analysis"])

        with tab_team:
            # --- টিম সামারি (আপনার সব রিকোয়ার্ড কলাম সহ) ---
            st.subheader("Detailed Team Performance")
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Present=('Name', 'nunique'),
                Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                MRP=('Product', lambda x: (x == 'Measurement Queue').sum()),
                CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum()),
                VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()),
                Orders=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                SQM=('SQM', 'sum')
            ).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)

            st.markdown("---")
            # --- আর্টিস্ট সামারি (Unique Artist Aggregation) ---
            st.subheader("Performance Breakdown Section (Artist Summary)")
            artist_brk = df.groupby(['Name', 'Team', 'Shift']).agg(
                Order=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                MRP=('Product', lambda x: (x == 'Measurement Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum()),
                CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()),
                SQM=('SQM', 'sum'),
                days=('date', 'nunique')
            ).reset_index()
            
            artist_brk['Idle'] = (artist_brk['days'] * 400) - artist_brk['Time']
            artist_brk['Idle'] = artist_brk['Idle'].apply(lambda x: max(0, x))
            
            final_cols = ['Name', 'Team', 'Shift', 'Order', 'Time', 'Idle', 'Rework', 'FP', 'MRP', 'UA', 'CAD', 'VanBree', 'SQM']
            st.dataframe(artist_brk[final_cols].sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True, height=600)

        with tab_artist:
            # আর্টিস্ট সিলেকশন ও বার চার্ট
            u_names = sorted(df['Name'].unique().tolist())
            a_sel = st.selectbox("Select Artist for Details", u_names)
            a_df = df[df['Name'] == a_sel]
            
            st.subheader(f"Artist Insights: {a_sel}")
            col_chart, col_log = st.columns([1, 1.5])
            with col_chart:
                p_data = a_df['Product'].value_counts().reset_index()
                p_data.columns = ['Product', 'Orders']
                st.plotly_chart(px.bar(p_data, x='Product', y='Orders', text='Orders', color='Product'), use_container_width=True)
            with col_log:
                st.write("Full Activity Log (Click Ticket ID to open RT)")
                log_df = a_df.copy()
                log_df['RT Link'] = log_df['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
                st.dataframe(log_df[['date', 'Ticket ID', 'RT Link', 'Product', 'SQM', 'Time']], column_config={"RT Link": st.column_config.LinkColumn("View")}, use_container_width=True, hide_index=True)

    # --- ৫. Yearly Profile পেজ (এরর ফিক্স করা হয়েছে) ---
    elif page == "Yearly Artist Profile":
        st.markdown("<h2 style='text-align: center;'>Artist Yearly Performance Summary</h2>", unsafe_allow_html=True)
        
        all_artists = sorted(df_yearly['USER NAME ALL'].unique().tolist())
        artist_sel = st.selectbox("Select Artist Name", all_artists)
        
        y_data = df_yearly[df_yearly['USER NAME ALL'] == artist_sel]
        
        if not y_data.empty:
            d = y_data.iloc[0]
            # কলামের নামগুলো স্পেস রিমুভ করে এক্সেস করা হচ্ছে
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Yearly Total FP", d.get('FLOOR PLAN', 0))
            c2.metric("Yearly Total MRP", d.get('MEASUREMENT', 0))
            c3.metric("Yearly Avg Time", f"{d.get('AVG TIME', 0)}m")
            c4.metric("Days Worked", d.get('WORKING DAY', 0))
            
            st.markdown("---")
            # চার্ট সেকশন
            st.subheader("Annual Production Breakdown")
            chart_df = pd.DataFrame({
                'Spec': ['FP', 'MRP', 'CAD', 'UA', 'VanBree'],
                'Count': [d.get('FLOOR PLAN', 0), d.get('MEASUREMENT', 0), d.get('AUTO CAD', 0), d.get('URBAN ANGLES', 0), d.get('VanBree Media', 0)]
            })
            st.plotly_chart(px.bar(chart_df, x='Spec', y='Count', color='Spec', text='Count'), use_container_width=True)
        else:
            st.warning("Yearly data not found for this artist.")

    # --- ৬. ট্র্যাকিং সিস্টেম ---
    elif page == "Tracking System":
        st.title("Performance Tracking")
        # Ticket ID এর সাথে সরাসরি লিঙ্ক যুক্ত করা হয়েছে
        tdf = df.copy()
        tdf['RT Link'] = tdf['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
        st.dataframe(tdf, column_config={"RT Link": st.column_config.LinkColumn("RT", display_text="Open")}, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
