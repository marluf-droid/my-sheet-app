import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ কনফিগারেশন ও ডিজাইন ---
st.set_page_config(page_title="Performance Analytics Pro", layout="wide")

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
def load_data():
    client = get_gspread_client()
    
    # শিট আইডি সমূহ
    master_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    efficiency_id = "1hFboFpRmst54yVUfESFAZE_UgNdBsaBAmHYA-9z5eJE"

    # ডাটা পড়া (DATA এবং FINAL SUMMARY ট্যাব থেকে)
    df_master = pd.DataFrame(client.open_by_key(master_id).worksheet("DATA").get_all_records())
    df_yearly = pd.DataFrame(client.open_by_key(efficiency_id).worksheet("FINAL SUMMARY").get_all_records())

    # কলাম ক্লিন করা
    for d in [df_master, df_yearly]:
        d.columns = [c.strip() for c in d.columns]
    
    df_master['date'] = pd.to_datetime(df_master['date'], errors='coerce').dt.date
    df_master['Time'] = pd.to_numeric(df_master['Time'], errors='coerce').fillna(0)
    df_master['SQM'] = pd.to_numeric(df_master['SQM'], errors='coerce').fillna(0)
    
    return df_master, df_yearly

try:
    df, df_yearly = load_data()

    # --- ৩. সাইডবার ন্যাভিগেশন ---
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Yearly Artist Profile", "Tracking System"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Global Filters")
    start_date = st.sidebar.date_input("Start Date", df['date'].min())
    end_date = st.sidebar.date_input("End Date", df['date'].max())
    
    team_list = ["All"] + sorted(df['Team'].unique().tolist())
    team_selected = st.sidebar.selectbox("Team Name", team_list)
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])

    # ডাটা ফিল্টারিং
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    if team_selected != "All": mask &= (df['Team'] == team_selected)
    if shift_selected != "All": mask &= (df['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df['Employee Type'] == emp_type_selected)
    filtered_df = df[mask].copy()

    # এভারেজ ক্যালকুলেশন ফাংশন (Man-Day logic)
    def get_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(len(subset) / man_days, 2)

    # --- ৪. পেজ ১: ড্যাশবোর্ড ---
    if page == "Dashboard":
        st.markdown("<h2 style='text-align: center;'>Performance Analytics 2025</h2>", unsafe_allow_html=True)
        
        # ৭টি প্রফেশনাল কার্ড
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{get_man_day_avg(filtered_df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{get_man_day_avg(filtered_df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{get_man_day_avg(filtered_df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{get_man_day_avg(filtered_df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{get_man_day_avg(filtered_df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree<br><h2>{get_man_day_avg(filtered_df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2>{len(filtered_df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tab_team, tab_artist = st.tabs(["👥 Team Summary", "🎨 Artist Summary"])
        
        with tab_team:
            team_sum = filtered_df.groupby(['Team', 'Shift']).agg(Present=('Name', 'nunique'), Orders=('Ticket ID', 'count'), Time=('Time', 'sum'), FP=('Product', lambda x: (x == 'Floorplan Queue').sum())).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)

        with tab_artist:
            # ইউনিক আর্টিস্ট সামারি
            artist_sum = filtered_df.groupby(['Name', 'Team', 'Shift']).agg(Order=('Ticket ID', 'count'), Time=('Time', 'sum'), days=('date', 'nunique')).reset_index()
            artist_sum['Idle'] = (artist_sum['days'] * 400) - artist_sum['Time']
            artist_sum['Idle'] = artist_sum['Idle'].apply(lambda x: max(0, x))
            st.dataframe(artist_sum.sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True, height=600)

    # --- ৫. পেজ ২: Yearly Artist Profile ---
    elif page == "Yearly Artist Profile":
        st.title("👤 Artist Yearly Performance Summary")
        
        all_artists = sorted(df_yearly['USER NAME ALL'].unique().tolist())
        artist_sel = st.selectbox("Select Artist Name", all_artists)
        
        y_data = df_yearly[df_yearly['USER NAME ALL'] == artist_sel]
        
        if not y_data.empty:
            d = y_data.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Yearly Total FP", d['FLOOR PLAN'])
            col2.metric("Yearly Total MRP", d['MEASUREMENT'])
            col3.metric("Yearly Avg Time", f"{d['AVG TIME']}m")
            col4.metric("Days Worked", d['WORKING DAY'])
            
            st.markdown("---")
            col_l, col_r = st.columns([1.5, 1])
            with col_l:
                chart_df = pd.DataFrame({
                    'Spec': ['FP', 'MRP', 'CAD', 'UA', 'VanBree'],
                    'Count': [d['FLOOR PLAN'], d['MEASUREMENT'], d['AUTO CAD'], d['URBAN ANGLES'], d['VanBree Media']]
                })
                st.plotly_chart(px.bar(chart_df, x='Spec', y='Count', color='Spec', text='Count', title=f"Annual Contribution: {artist_sel}"), use_container_width=True)
            with col_r:
                st.info(f"Artist Team: {d['Team']}")
                st.write(f"Role: {d['ARTIST/ QC']}")
                # স্ক্যাটার চার্ট (এফিসিয়েন্সি)
                a_df = df[df['Name'] == artist_sel]
                if not a_df.empty:
                    fig_scat = px.scatter(a_df, x="SQM", y="Time", size="Time", color="Product", hover_data=['Ticket ID'], title="Efficiency (Time vs SQM)")
                    st.plotly_chart(fig_scat, use_container_width=True)
        else:
            st.info("No yearly data found for this artist in 'FINAL SUMMARY' tab.")

    # --- ৬. ট্র্যাকিং সিস্টেম ---
    elif page == "Tracking System":
        st.title("🎯 Performance Tracking")
        criteria = st.selectbox("Criteria", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        tdf = filtered_df.copy()
        
        # জটিল লজিক মাস্কিং
        s_ip = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] < 2)) | ((tdf['Employee Type'] == 'Artist') & (((tdf['Product'] == 'Floorplan Queue') & (tdf['Time'] <= 15)) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] < 5)) | (~tdf['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf['Time'] <= 10)))))
        s_mt = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] > 20)) | ((tdf['Employee Type'] == 'Artist') & ((tdf['Time'] >= 150) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] > 40)))))
        h_ts = (tdf['Time'] > (tdf['SQM'] + 15)) & ~s_mt

        if criteria == "Short IP": tdf = tdf[s_ip]
        elif criteria == "Spending More Time": tdf = tdf[s_mt]
        elif criteria == "High Time vs SQM": tdf = tdf[h_ts]

        st.metric("Total Found", len(tdf))
        
        # Ticket ID ক্লিকেবল লিঙ্ক
        tdf['RT Link'] = tdf['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
        st.dataframe(
            tdf,
            column_config={"RT Link": st.column_config.LinkColumn("Open RT", display_text="Open")},
            use_container_width=True, hide_index=True
        )

except Exception as e:
    st.error(f"Error: {e}")
