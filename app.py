import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# --- ১. পেজ সেটআপ ---
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

st.markdown("""
    <style>
    .metric-card { 
        padding: 15px; 
        border-radius: 8px; 
        text-align: center; 
        color: #333; 
        font-weight: bold; 
        margin-bottom: 10px; 
        border-bottom: 4px solid #ddd;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .rework-card { background-color: #FFEBEE; border-color: #F44336; }
    .fp-card { background-color: #E3F2FD; border-color: #2196F3; }
    .mrp-card { background-color: #E8F5E9; border-color: #4CAF50; }
    .cad-card { background-color: #FFFDE7; border-color: #FBC02D; }
    .ua-card { background-color: #F3E5F5; border-color: #9C27B0; }
    .vanbree-card { background-color: #E0F2F1; border-color: #009688; }
    .total-card { background-color: #ECEFF1; border-color: #607D8B; }
    
    /* Improve dataframe appearance */
    .dataframe {
        font-size: 14px;
    }
    
    /* Custom header styling */
    .main-header {
        background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ২. ডাটা কানেকশন ---
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/drive",
             "https://www.googleapis.com/auth/spreadsheets"]
    creds_info = json.loads(st.secrets["JSON_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def get_data():
    try:
        client = get_gspread_client()
        sheet_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
        spreadsheet = client.open_by_key(sheet_id)
        df = pd.DataFrame(spreadsheet.worksheet("DATA").get_all_records())
        
        # কলাম ক্লিন করা
        df.columns = [str(c).strip() for c in df.columns]
        
        # ডাটা টাইপ ও টেক্সট ক্লিন করা
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
        df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
        
        # সকল টেক্সট কলাম থেকে বাড়তি স্পেস মুছে ফেলা
        text_cols = ['Product', 'Job Type', 'Employee Type', 'Team', 'Name', 'Shift']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.title()
                
        # Ensure necessary columns exist
        required_cols = ['Ticket ID', 'date', 'Product', 'Job Type', 'Name', 'Team', 'Shift', 'Employee Type', 'Time', 'SQM']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
                
        return df
    
    except Exception as e:
        st.error(f"Data loading error: {e}")
        return pd.DataFrame()

# --- ৩. ম্যান-ডে এভারেজ ক্যালকুলেশন ---
def calculate_man_day_avg(target_df, product_name, job_type="Live Job"):
    """Calculate man-day average based on sheet formula logic"""
    if target_df.empty:
        return 0.0
    
    subset = target_df[
        (target_df['Product'] == product_name) & 
        (target_df['Job Type'] == job_type)
    ]
    
    if subset.empty:
        return 0.0
    
    total_tasks = len(subset)  # ROWS(fp_data)
    
    # UNIQUE(Artist + Date) - কতজন মানুষ কত দিন কাজ করেছে
    if 'Name' in subset.columns and 'date' in subset.columns:
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
    else:
        man_days = subset.shape[0]
    
    return round(total_tasks / man_days, 2) if man_days > 0 else 0.0

# --- মেইন অ্যাপ্লিকেশন ---
def main():
    try:
        df_raw = get_data()
        
        if df_raw.empty:
            st.warning("No data loaded. Please check your connection and credentials.")
            return
        
        # --- ৪. সাইডবার ন্যাভিগেশন ও গ্লোবাল ফিল্টারস ---
        st.sidebar.markdown("# 🧭 Navigation")
        page = st.sidebar.radio("Select Dashboard", 
                               ["📊 Main Dashboard", 
                                "🎯 Performance Tracking", 
                                "📈 Detailed Analytics"])
        st.sidebar.markdown("---")
        
        st.sidebar.markdown("# 🔍 Global Filters")
        
        # Date filters
        if not df_raw.empty and 'date' in df_raw.columns:
            start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
            end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
        else:
            start_date = st.sidebar.date_input("Start Date", datetime.today())
            end_date = st.sidebar.date_input("End Date", datetime.today())
        
        # Team filter
        if 'Team' in df_raw.columns:
            teams = ["All"] + sorted([t for t in df_raw['Team'].unique().tolist() if pd.notna(t)])
            team_selected = st.sidebar.selectbox("Team Name", teams)
        else:
            team_selected = "All"
        
        # Shift filter
        if 'Shift' in df_raw.columns:
            shifts = ["All"] + sorted([s for s in df_raw['Shift'].unique().tolist() if pd.notna(s)])
            shift_selected = st.sidebar.selectbox("Shift", shifts)
        else:
            shift_selected = "All"
        
        # Employee Type filter
        if 'Employee Type' in df_raw.columns:
            emp_types = ["All"] + sorted([e for e in df_raw['Employee Type'].unique().tolist() if pd.notna(e)])
            emp_type_selected = st.sidebar.selectbox("Employee Type", emp_types)
        else:
            emp_type_selected = "All"
        
        # Product filter
        if 'Product' in df_raw.columns:
            products = ["All"] + sorted([p for p in df_raw['Product'].unique().tolist() if pd.notna(p)])
            product_selected_global = st.sidebar.selectbox("Product Type Filter", products)
        else:
            product_selected_global = "All"

        # ডাটা ফিল্টারিং (Global)
        mask = pd.Series(True, index=df_raw.index)
        
        if 'date' in df_raw.columns:
            mask &= (df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)
        
        if team_selected != "All" and 'Team' in df_raw.columns:
            mask &= (df_raw['Team'] == team_selected)
        
        if shift_selected != "All" and 'Shift' in df_raw.columns:
            mask &= (df_raw['Shift'] == shift_selected)
        
        if emp_type_selected != "All" and 'Employee Type' in df_raw.columns:
            mask &= (df_raw['Employee Type'] == emp_type_selected)
        
        if product_selected_global != "All" and 'Product' in df_raw.columns:
            mask &= (df_raw['Product'] == product_selected_global)
        
        df = df_raw[mask].copy()

        # --- ৫. মেইন ড্যাশবোর্ড ---
        if page == "📊 Main Dashboard":
            st.markdown('<div class="main-header"><h1>📊 PERFORMANCE ANALYTICS 2025</h1></div>', unsafe_allow_html=True)
            
            # কার্ড মেট্রিক্স ক্যালকুলেশন
            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
            
            with col1:
                avg_rework = calculate_man_day_avg(df, "Floorplan Queue", "Rework")
                st.markdown(f'<div class="metric-card rework-card">Rework AVG<br><h2>{avg_rework}</h2></div>', unsafe_allow_html=True)
            
            with col2:
                avg_fp = calculate_man_day_avg(df, "Floorplan Queue", "Live Job")
                st.markdown(f'<div class="metric-card fp-card">FP AVG<br><h2>{avg_fp}</h2></div>', unsafe_allow_html=True)
            
            with col3:
                avg_mrp = calculate_man_day_avg(df, "Measurement Queue", "Live Job")
                st.markdown(f'<div class="metric-card mrp-card">MRP AVG<br><h2>{avg_mrp}</h2></div>', unsafe_allow_html=True)
            
            with col4:
                avg_cad = calculate_man_day_avg(df, "Autocad Queue", "Live Job")
                st.markdown(f'<div class="metric-card cad-card">CAD AVG<br><h2>{avg_cad}</h2></div>', unsafe_allow_html=True)
            
            with col5:
                avg_ua = calculate_man_day_avg(df, "Urban Angles", "Live Job")
                st.markdown(f'<div class="metric-card ua-card">UA AVG<br><h2>{avg_ua}</h2></div>', unsafe_allow_html=True)
            
            with col6:
                avg_vanbree = calculate_man_day_avg(df, "Van Bree Media", "Live Job")
                st.markdown(f'<div class="metric-card vanbree-card">Van Bree<br><h2>{avg_vanbree}</h2></div>', unsafe_allow_html=True)
            
            with col7:
                total_orders = len(df) if not df.empty else 0
                st.markdown(f'<div class="metric-card total-card">Total Order<br><h2>{total_orders}</h2></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- First Row: Charts ---
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Product Distribution Bar Chart
                if not df.empty and 'Product' in df.columns:
                    product_counts = df['Product'].value_counts().reset_index()
                    product_counts.columns = ['Product', 'Order Count']
                    
                    fig1 = px.bar(
                        product_counts.head(10),  # Show top 10 products
                        x='Product',
                        y='Order Count',
                        title='📦 Product Distribution (Top 10)',
                        color='Order Count',
                        color_continuous_scale='Blues',
                        text='Order Count'
                    )
                    fig1.update_traces(
                        textposition='outside',
                        marker_line_color='black',
                        marker_line_width=0.5
                    )
                    fig1.update_layout(
                        xaxis_title='Product Type',
                        yaxis_title='Number of Orders',
                        xaxis_tickangle=-45,
                        showlegend=False
                    )
                    st.plotly_chart(fig1, use_container_width=True)
            
            with chart_col2:
                # Monthly Performance Bar Chart
                if not df.empty and 'date' in df.columns:
                    df_monthly = df.copy()
                    df_monthly['Month'] = pd.to_datetime(df_monthly['date']).dt.strftime('%b %Y')
                    monthly_data = df_monthly.groupby('Month').agg(
                        Total_Orders=('Ticket ID', 'count'),
                        Avg_Time=('Time', 'mean')
                    ).reset_index()
                    
                    fig2 = px.bar(
                        monthly_data,
                        x='Month',
                        y='Total_Orders',
                        title='📅 Monthly Performance',
                        color='Avg_Time',
                        color_continuous_scale='Viridis',
                        text='Total_Orders'
                    )
                    fig2.update_traces(
                        textposition='outside',
                        marker_line_color='black',
                        marker_line_width=0.5
                    )
                    fig2.update_layout(
                        xaxis_title='Month',
                        yaxis_title='Total Orders',
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig2, use_container_width=True)

            # --- Second Row: Data Tables ---
            col_left, col_right = st.columns([1.8, 1])

            with col_left:
                # Team Summary
                st.subheader("👥 Team Summary")
                if not df.empty:
                    team_sum = df.groupby(['Team', 'Shift']).agg(
                        Present=('Name', 'nunique'),
                        Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                        FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                        MRP=('Product', lambda x: (x == 'Measurement Queue').sum()),
                        CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                        UA=('Product', lambda x: (x == 'Urban Angles').sum()),
                        Total_Orders=('Ticket ID', 'count'),
                        Total_Time=('Time', 'sum')
                    ).reset_index().round(2)
                    
                    # Format for display
                    team_sum['Total_Time'] = team_sum['Total_Time'].apply(lambda x: f"{x:,.0f}")
                    team_sum['Total_Orders'] = team_sum['Total_Orders'].apply(lambda x: f"{x:,.0f}")
                    
                    st.dataframe(team_sum, use_container_width=True, hide_index=True)
                else:
                    st.info("No team data available for selected filters.")
                
                # Artist Breakdown (Group By Artist)
                st.subheader("🎨 Performance Breakdown (Artist Summary)")
                if not df.empty and 'Name' in df.columns:
                    artist_breakdown = df.groupby(['Name', 'Team', 'Shift']).agg(
                        Order=('Ticket ID', 'count'),
                        Time=('Time', 'sum'),
                        Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                        FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                        MRP=('Product', lambda x: (x == 'Measurement Queue').sum()),
                        UA=('Product', lambda x: (x == 'Urban Angles').sum()),
                        CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                        SQM=('SQM', 'sum'),
                        worked_days=('date', 'nunique')
                    ).reset_index().round(2)
                    
                    # Idle Time calculation
                    artist_breakdown['Idle'] = (artist_breakdown['worked_days'] * 400) - artist_breakdown['Time']
                    artist_breakdown['Idle'] = artist_breakdown['Idle'].apply(lambda x: max(0, round(x, 2)))
                    artist_breakdown = artist_breakdown.sort_values(by=['Order', 'Time'], ascending=False)
                    
                    # Format columns for display
                    cols_order = ['Name', 'Team', 'Shift', 'Order', 'Time', 'Idle', 'Rework', 'FP', 'MRP', 'UA', 'CAD', 'SQM']
                    display_df = artist_breakdown[cols_order].copy()
                    
                    # Format numeric columns
                    numeric_cols = ['Order', 'Time', 'Idle', 'Rework', 'FP', 'MRP', 'UA', 'CAD', 'SQM']
                    for col in numeric_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No artist data available for selected filters.")

            with col_right:
                # Artist Statistics Section
                st.subheader("👤 Artist Statistics")
                
                if not df.empty and 'Name' in df.columns:
                    unique_names = sorted([n for n in df['Name'].unique().tolist() if pd.notna(n)])
                    
                    if unique_names:
                        # Get top performer
                        if 'artist_breakdown' in locals() and not artist_breakdown.empty:
                            top_name = artist_breakdown['Name'].iloc[0] if not artist_breakdown.empty else unique_names[0]
                        else:
                            top_name = unique_names[0]
                        
                        artist_selected = st.selectbox(
                            "Select Artist for Stats", 
                            unique_names, 
                            index=unique_names.index(top_name) if top_name in unique_names else 0
                        )
                        
                        artist_df = df[df['Name'] == artist_selected]
                        
                        if not artist_df.empty:
                            # Artist Performance Bar Chart
                            st.subheader(f"📊 Performance: {artist_selected}")
                            
                            # Product-wise performance
                            artist_product_data = artist_df['Product'].value_counts().reset_index()
                            artist_product_data.columns = ['Product', 'Order Count']
                            
                            fig3 = px.bar(
                                artist_product_data,
                                x='Product',
                                y='Order Count',
                                color='Order Count',
                                color_continuous_scale='Teal',
                                text='Order Count',
                                title=f'Product Distribution for {artist_selected}'
                            )
                            fig3.update_traces(
                                textposition='outside',
                                marker_line_color='black',
                                marker_line_width=0.5
                            )
                            fig3.update_layout(
                                xaxis_title='Product Type',
                                yaxis_title='Number of Orders',
                                xaxis_tickangle=-45,
                                showlegend=False
                            )
                            st.plotly_chart(fig3, use_container_width=True)
                            
                            # Artist Detail Table
                            st.subheader("📋 Performance Details")
                            detail_df = artist_df.copy()
                            detail_df['date'] = detail_df['date'].apply(lambda x: x.strftime('%m/%d/%Y') if pd.notna(x) else 'N/A')
                            
                            # Select and rename columns for display
                            detail_cols = ['date', 'Ticket ID', 'Product', 'SQM', 'Time', 'Job Type']
                            available_cols = [col for col in detail_cols if col in detail_df.columns]
                            
                            if available_cols:
                                detail_display = detail_df[available_cols].copy()
                                rename_dict = {
                                    'date': 'Date',
                                    'Ticket ID': 'Order ID',
                                    'Product': 'Product',
                                    'SQM': 'SQM',
                                    'Time': 'Time (min)',
                                    'Job Type': 'Job Type'
                                }
                                detail_display = detail_display.rename(columns=rename_dict)
                                
                                # Format numeric columns
                                if 'SQM' in detail_display.columns:
                                    detail_display['SQM'] = detail_display['SQM'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
                                if 'Time (min)' in detail_display.columns:
                                    detail_display['Time (min)'] = detail_display['Time (min)'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
                                
                                st.dataframe(detail_display, use_container_width=True, hide_index=True)
                    else:
                        st.info("No artist names available in the filtered data.")
                else:
                    st.info("No artist data available for selected filters.")

        # --- ৬. পারফরম্যান্স ট্র্যাকিং পেজ ---
        elif page == "🎯 Performance Tracking":
            st.markdown('<div class="main-header"><h1>🎯 PERFORMANCE TRACKING</h1></div>', unsafe_allow_html=True)
            
            criteria = st.selectbox(
                "Select Criteria for Analysis",
                ["All", "Short IP", "Spending More Time", "High Time vs SQM", "Top Performers", "Need Improvement"]
            )
            
            tdf = df.copy()
            
            if criteria == "Short IP":
                # Short IP criteria
                if 'Employee Type' in tdf.columns and 'Time' in tdf.columns and 'Product' in tdf.columns:
                    short_ip_mask = (
                        ((tdf['Employee Type'] == 'QC') & (tdf['Time'] < 2)) | 
                        ((tdf['Employee Type'] == 'Artist') & (
                            ((tdf['Product'] == 'Floorplan Queue') & (tdf['Time'] <= 15)) |
                            ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] < 5)) |
                            (~tdf['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf['Time'] <= 10))
                        ))
                    )
                    tdf = tdf[short_ip_mask]
                    
            elif criteria == "Spending More Time":
                # Spending more time criteria
                if 'Employee Type' in tdf.columns and 'Time' in tdf.columns and 'Product' in tdf.columns:
                    spending_more_mask = (
                        ((tdf['Employee Type'] == 'QC') & (tdf['Time'] > 20)) | 
                        ((tdf['Employee Type'] == 'Artist') & (
                            (tdf['Time'] >= 150) | 
                            ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] > 40))
                        ))
                    )
                    tdf = tdf[spending_more_mask]
                    
            elif criteria == "High Time vs SQM":
                # High time vs SQM criteria
                if 'Time' in tdf.columns and 'SQM' in tdf.columns:
                    if 'spending_more_mask' in locals():
                        high_time_sqm_mask = (tdf['Time'] > (tdf['SQM'] + 15)) & ~spending_more_mask
                    else:
                        high_time_sqm_mask = (tdf['Time'] > (tdf['SQM'] + 15))
                    tdf = tdf[high_time_sqm_mask]
            
            elif criteria == "Top Performers":
                # Show top 10 performers
                if not df.empty and 'Name' in df.columns:
                    top_performers = df.groupby('Name').agg(
                        Total_Orders=('Ticket ID', 'count'),
                        Total_Time=('Time', 'sum'),
                        Avg_Time_Per_Order=('Time', 'mean')
                    ).reset_index().round(2)
                    
                    top_performers = top_performers.nlargest(10, 'Total_Orders')
                    
                    # Create bar chart for top performers
                    fig4 = px.bar(
                        top_performers,
                        x='Name',
                        y='Total_Orders',
                        color='Avg_Time_Per_Order',
                        color_continuous_scale='Greens',
                        text='Total_Orders',
                        title='🏆 Top 10 Performers by Order Count'
                    )
                    fig4.update_traces(
                        textposition='outside',
                        marker_line_color='black',
                        marker_line_width=0.5
                    )
                    fig4.update_layout(
                        xaxis_title='Artist Name',
                        yaxis_title='Total Orders',
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig4, use_container_width=True)
                    
                    tdf = df[df['Name'].isin(top_performers['Name'])]
            
            elif criteria == "Need Improvement":
                # Show bottom 10 performers
                if not df.empty and 'Name' in df.columns:
                    bottom_performers = df.groupby('Name').agg(
                        Total_Orders=('Ticket ID', 'count'),
                        Total_Time=('Time', 'sum'),
                        Avg_Time_Per_Order=('Time', 'mean')
                    ).reset_index().round(2)
                    
                    bottom_performers = bottom_performers.nsmallest(10, 'Total_Orders')
                    
                    # Create bar chart for bottom performers
                    fig5 = px.bar(
                        bottom_performers,
                        x='Name',
                        y='Total_Orders',
                        color='Avg_Time_Per_Order',
                        color_continuous_scale='Reds',
                        text='Total_Orders',
                        title='📉 Bottom 10 Performers Needing Improvement'
                    )
                    fig5.update_traces(
                        textposition='outside',
                        marker_line_color='black',
                        marker_line_width=0.5
                    )
                    fig5.update_layout(
                        xaxis_title='Artist Name',
                        yaxis_title='Total Orders',
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig5, use_container_width=True)
                    
                    tdf = df[df['Name'].isin(bottom_performers['Name'])]

            # Display results
            st.metric("Total Jobs Found", len(tdf))
            
            if not tdf.empty:
                # Create summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_time = tdf['Time'].mean() if 'Time' in tdf.columns else 0
                    st.metric("Average Time", f"{avg_time:.1f} min")
                
                with col2:
                    total_sqm = tdf['SQM'].sum() if 'SQM' in tdf.columns else 0
                    st.metric("Total SQM", f"{total_sqm:,.0f}")
                
                with col3:
                    unique_artists = tdf['Name'].nunique() if 'Name' in tdf.columns else 0
                    st.metric("Unique Artists", unique_artists)
                
                # Display the dataframe
                display_cols = ['date', 'Name', 'Team', 'Product', 'Job Type', 'Time', 'SQM', 'Ticket ID']
                available_display_cols = [col for col in display_cols if col in tdf.columns]
                
                if available_display_cols:
                    display_df = tdf[available_display_cols].copy()
                    
                    # Format date
                    if 'date' in display_df.columns:
                        display_df['date'] = display_df['date'].apply(
                            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else 'N/A'
                        )
                    
                    # Format numeric columns
                    if 'Time' in display_df.columns:
                        display_df['Time'] = display_df['Time'].apply(
                            lambda x: f"{x:,.0f}" if pd.notna(x) else "0"
                        )
                    
                    if 'SQM' in display_df.columns:
                        display_df['SQM'] = display_df['SQM'].apply(
                            lambda x: f"{x:,.0f}" if pd.notna(x) else "0"
                        )
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No data found for criteria: {criteria}")

        # --- ৭. ডিটেইলড অ্যানালিটিক্স পেজ ---
        elif page == "📈 Detailed Analytics":
            st.markdown('<div class="main-header"><h1>📈 DETAILED ANALYTICS</h1></div>', unsafe_allow_html=True)
            
            if not df.empty:
                # Summary Statistics
                st.subheader("📊 Summary Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_orders = len(df)
                    st.metric("Total Orders", f"{total_orders:,}")
                
                with col2:
                    total_time = df['Time'].sum() if 'Time' in df.columns else 0
                    st.metric("Total Time", f"{total_time:,.0f} min")
                
                with col3:
                    avg_time = df['Time'].mean() if 'Time' in df.columns else 0
                    st.metric("Avg Time/Order", f"{avg_time:.1f} min")
                
                with col4:
                    total_sqm = df['SQM'].sum() if 'SQM' in df.columns else 0
                    st.metric("Total SQM", f"{total_sqm:,.0f}")
                
                # Time Distribution Analysis
                st.subheader("⏱️ Time Distribution Analysis")
                
                if 'Time' in df.columns:
                    time_bins = pd.cut(df['Time'], bins=[0, 15, 30, 60, 120, 240, df['Time'].max()], 
                                      labels=['0-15', '16-30', '31-60', '61-120', '121-240', '240+'])
                    time_distribution = time_bins.value_counts().sort_index().reset_index()
                    time_distribution.columns = ['Time Range (min)', 'Count']
                    
                    fig6 = px.bar(
                        time_distribution,
                        x='Time Range (min)',
                        y='Count',
                        color='Count',
                        color_continuous_scale='Purples',
                        text='Count',
                        title='Order Count by Time Range'
                    )
                    fig6.update_traces(
                        textposition='outside',
                        marker_line_color='black',
                        marker_line_width=0.5
                    )
                    fig6.update_layout(
                        xaxis_title='Time Range (minutes)',
                        yaxis_title='Number of Orders',
                        showlegend=False
                    )
                    st.plotly_chart(fig6, use_container_width=True)
                
                # Productivity Trends
                st.subheader("📈 Productivity Trends")
                
                if 'date' in df.columns:
                    df_daily = df.copy()
                    df_daily['date'] = pd.to_datetime(df_daily['date'])
                    daily_trends = df_daily.groupby(df_daily['date'].dt.date).agg(
                        Daily_Orders=('Ticket ID', 'count'),
                        Daily_Time=('Time', 'sum'),
                        Daily_Avg_Time=('Time', 'mean')
                    ).reset_index()
                    
                    fig7 = px.bar(
                        daily_trends,
                        x='date',
                        y='Daily_Orders',
                        color='Daily_Avg_Time',
                        color_continuous_scale='Oranges',
                        title='Daily Order Count Trend'
                    )
                    fig7.update_layout(
                        xaxis_title='Date',
                        yaxis_title='Daily Orders',
                        xaxis_tickformat='%b %d'
                    )
                    st.plotly_chart(fig7, use_container_width=True)
                
                # Team Comparison
                st.subheader("🏆 Team Comparison")
                
                if 'Team' in df.columns:
                    team_comparison = df.groupby('Team').agg(
                        Total_Orders=('Ticket ID', 'count'),
                        Total_Time=('Time', 'sum'),
                        Avg_Time=('Time', 'mean'),
                        Total_Artists=('Name', 'nunique')
                    ).reset_index().round(2)
                    
                    fig8 = px.bar(
                        team_comparison,
                        x='Team',
                        y='Total_Orders',
                        color='Avg_Time',
                        color_continuous_scale='Blues',
                        text='Total_Orders',
                        title='Team Performance Comparison'
                    )
                    fig8.update_traces(
                        textposition='outside',
                        marker_line_color='black',
                        marker_line_width=0.5
                    )
                    fig8.update_layout(
                        xaxis_title='Team',
                        yaxis_title='Total Orders',
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig8, use_container_width=True)
                    
                    # Display team comparison table
                    team_comparison_display = team_comparison.copy()
                    team_comparison_display['Total_Time'] = team_comparison_display['Total_Time'].apply(lambda x: f"{x:,.0f}")
                    team_comparison_display['Total_Orders'] = team_comparison_display['Total_Orders'].apply(lambda x: f"{x:,.0f}")
                    team_comparison_display['Avg_Time'] = team_comparison_display['Avg_Time'].apply(lambda x: f"{x:.1f}")
                    
                    st.dataframe(team_comparison_display, use_container_width=True, hide_index=True)
            else:
                st.info("No data available for detailed analytics with current filters.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please check your data connection and filters.")

if __name__ == "__main__":
    main()
