import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ কনফিগারেশন ---
st.set_page_config(page_title="Performance Analytics Pro", layout="wide")

# আধুনিক ক্লিন CSS
st.markdown("""
    <style>
    .metric-card { padding: 15px; border-radius: 12px; text-align: center; color: #1e293b; background: #ffffff; border-top: 5px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
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
    creds_info = json.loads(st.secrets["JSON_KEY"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_all_sheets():
    client = get_gspread_client()
    
    # শিট আইডি সমূহ
    master_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    internal_id = "1mOph7_YK6seLfXpKrO00S9tMaNvbBCS5iQP7FjiNBaE"
    external_id = "1yrCM3xMpQ2IdLO4wBIzyeMJ5lAC4KRTUmA-h5dG0iEM"
    efficiency_id = "1hFboFpRmst54yVUfESFAZE_UgNdBsaBAmHYA-9z5eJE"

    # প্রতিটি শিট এবং ট্যাব আলাদাভাবে লোড করা (আপনার স্ক্রিনশট অনুযায়ী)
    df_master = pd.DataFrame(client.open_by_key(master_id).worksheet("DATA").get_all_records())
    df_int = pd.DataFrame(client.open_by_key(internal_id).worksheet("99+ Rework Data Entry").get_all_records())
    df_ext = pd.DataFrame(client.open_by_key(external_id).worksheet("Rework Data Entry").get_all_records())
    df_yearly = pd.DataFrame(client.open_by_key(efficiency_id).worksheet("FINAL SUMMARY").get_all_records())

    # কলাম ক্লিন করা
    for d in [df_master, df_int, df_ext, df_yearly]:
        d.columns = [c.strip() for c in d.columns]
    
    # ডাটা ফরম্যাটিং
    df_master['date'] = pd.to_datetime(df_master['date'], errors='coerce').dt.date
    df_master['Time'] = pd.to_numeric(df_master['Time'], errors='coerce').fillna(0)
    
    return df_master, df_int, df_ext, df_yearly

try:
    df, df_int, df_ext, df_yearly = load_all_sheets()

    # --- ৩. ন্যাভিগেশন ---
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Select View", ["Live Dashboard", "Yearly Profile", "Tracking System"])
    
    st.sidebar.markdown("---")
    st.sidebar.title("🔍 Filters")
    start_date = st.sidebar.date_input("Start Date", df['date'].min())
    end_date = st.sidebar.date_input("End Date", df['date'].max())
    
    # গ্লোবাল ফিল্টার অনুযায়ী ডাটা ফিল্টারিং
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    filtered_df = df[mask].copy()

    # এভারেজ ক্যালকুলেশন লজিক
    def get_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(len(subset) / man_days, 2)

    # --- ৪. পেজ ১: লাইভ ড্যাশবোর্ড ---
    if page == "Live Dashboard":
        st.title("📊 Performance Dashboard 2025")
        
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{get_avg(filtered_df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{get_avg(filtered_df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{get_avg(filtered_df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{get_avg(filtered_df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{get_avg(filtered_df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree<br><h2>{get_avg(filtered_df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2>{len(filtered_df)}</h2></div>', unsafe_allow_html=True)

        tab_team, tab_artist = st.tabs(["👥 Team Summary", "🎨 Artist Summary"])
        
        with tab_team:
            team_summary = filtered_df.groupby(['Team', 'Shift']).agg(Artists=('Name', 'nunique'), Orders=('Ticket ID', 'count'), Time=('Time', 'sum')).reset_index()
            st.dataframe(team_summary, use_container_width=True, hide_index=True)

        with tab_artist:
            artist_summary = filtered_df.groupby(['Name', 'Team', 'Shift']).agg(Order=('Ticket ID', 'count'), Time=('Time', 'sum'), days=('date', 'nunique')).reset_index()
            st.dataframe(artist_summary.sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True)

    # --- ৫. পেজ ২: Yearly Profile ---
    elif page == "Yearly Profile":
        st.title("👤 Artist Yearly Performance")
        
        # Yearly শিট থেকে আর্টিস্টদের লিস্ট নেওয়া
        all_artists = sorted(df_yearly['USER NAME ALL'].unique().tolist())
        artist_sel = st.selectbox("Search Artist", all_artists)
        
        # ডাটা ফিল্টারিং
        y_data = df_yearly[df_yearly['USER NAME ALL'] == artist_sel]
        i_rew = df_int[df_int['Mistake BY'] == artist_sel]
        e_rew = df_ext[df_ext['Mistake BY'] == artist_sel]
        
        if not y_data.empty:
            d = y_data.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total FP", d['FLOOR PLAN'])
            c2.metric("Total MRP", d['MEASUREMENT'])
            c3.metric("Yearly Avg Time", f"{d['AVG TIME']}m")
            c4.metric("Days Worked", d['WORKING DAY'])
            
            st.markdown("---")
            col_l, col_r = st.columns(2)
            
            with col_l:
                st.subheader("Rejection Stats")
                r1, r2 = st.columns(2)
                r1.markdown(f'<div class="metric-card rework-card">Internal Rejects<br><h2>{len(i_rew)}</h2></div>', unsafe_allow_html=True)
                r2.markdown(f'<div class="metric-card rework-card">External Rejects<br><h2>{len(e_rew)}</h2></div>', unsafe_allow_html=True)
                
                # কন্ট্রিবিউশন চার্ট
                chart_df = pd.DataFrame({
                    'Spec': ['FP', 'MRP', 'CAD', 'UA', 'VanBree'],
                    'Count': [d['FLOOR PLAN'], d['MEASUREMENT'], d['AUTO CAD'], d['URBAN ANGLES'], d['VanBree Media']]
                })
                st.plotly_chart(px.bar(chart_df, x='Spec', y='Count', color='Spec', text='Count'), use_container_width=True)

            with col_r:
                st.subheader("Internal Error Log (Recent)")
                # 'Rework Data Entry' বা '99+' শিটে Mistake BY কলাম ধরে তথ্য দেখানো
                if not i_rew.empty:
                    st.dataframe(i_rew[['Received', 'Order Number', 'QC', 'Comment']].tail(10), hide_index=True)
                else:
                    st.info("No internal rejections found.")
        else:
            st.warning("Yearly data not found for this artist.")

    # --- ৬. ট্র্যাকিং সিস্টেম ---
    elif page == "Tracking System":
        st.title("🎯 Tracking System")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.info("টিপস: নিশ্চিত করুন সব কটি শিটে আপনার সার্ভিস একাউন্ট ইমেইলটিকে 'Editor' হিসেবে শেয়ার করেছেন।")
