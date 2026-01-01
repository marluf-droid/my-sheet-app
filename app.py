with col_right:
            unique_artist_list = sorted(df['Name'].unique().tolist())
            if not artist_breakdown.empty:
                top_performer_name = artist_breakdown.iloc[0]['Name']
                default_idx = unique_artist_list.index(top_performer_name) if top_performer_name in unique_artist_list else 0
            else: default_idx = 0

            artist_selected = st.selectbox("Select Artist for Stats", unique_artist_list, index=default_idx)
            
            # আর্টিস্ট অনুযায়ী ডাটা ফিল্টার
            artist_df = df[df['Name'] == artist_selected]
            
            if not artist_df.empty:
                st.subheader(f"Stats: {artist_selected}")
                
                # ১. প্রজেক্ট সংখ্যা গণনা করা (প্রতিটি প্রোডাক্টে কয়টি কাজ করেছে)
                project_counts = artist_df.groupby('Product').size().reset_index(name='Total Projects')
                
                # ২. বার চার্ট (Pie Chart এর বদলে এটি ব্যবহার করুন)
                bar_fig = px.bar(
                    project_counts, 
                    x='Product', 
                    y='Total Projects',
                    text='Total Projects', # বারের উপরে সংখ্যা দেখাবে
                    color='Product',
                    height=400,
                    labels={'Total Projects': 'No. of Projects', 'Product': 'Product Type'}
                )
                
                bar_fig.update_traces(textposition='outside')
                bar_fig.update_layout(showlegend=False)
                
                # চার্টটি ডিসপ্লে করা
                st.plotly_chart(bar_fig, use_container_width=True)
                
                # ৩. আর্টিস্টের কাজের ডিটেইলস টেবিল
                st.subheader("Artist Performance Detail")
                detail_cols = ['date', 'Ticket ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time']
                detail_t = artist_df[[c for c in detail_cols if c in artist_df.columns]].copy()
                
                # তারিখ ফরম্যাট ঠিক করা
                if 'date' in detail_t.columns:
                    detail_t['date'] = detail_t['date'].astype(str)
                
                st.dataframe(detail_t, use_container_width=True, hide_index=True)
