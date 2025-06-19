with tabs[3]:
    st.subheader("🌍 Geographic Customer Distribution")
    geo_mode = st.radio("Map Mode", ["Global", "USA States"], horizontal=True)

    if geo_mode == "Global":
        geo_data = df_usage.groupby("country").agg(customers=("customer_id", "count")).reset_index()
        fig4 = go.Figure(data=go.Scattergeo(
            locations=geo_data['country'],
            locationmode="country names",
            text=geo_data['customers'],
            marker=dict(
                size=geo_data['customers'] / 10,
                color='rgba(44, 102, 180, 0.6)',
                line=dict(color='black', width=0.5)
            )
        ))
        fig4.update_layout(title_text="Customer Distribution by Country", geo=dict(
            showland=True, landcolor='lightgray', showlakes=True, lakecolor='white'
        ))
        st.plotly_chart(fig4, use_container_width=True)

    else:
        geo_data = df_usage[df_usage["state"].notna()]
        geo_data = geo_data.groupby("state").agg(customers=("customer_id", "count")).reset_index()
        geo_data = geo_data[geo_data["state"].str.len() == 2]  # ensure two-letter codes

        fig4 = go.Figure(data=go.Scattergeo(
            locations=geo_data['state'],
            locationmode="USA-states",
            scope="usa",
            text=geo_data['customers'],
            marker=dict(
                size=geo_data['customers'] / 10,
                color='rgba(44, 102, 180, 0.6)',
                line=dict(color='black', width=0.5)
            )
        ))
        fig4.update_layout(title_text="Customer Distribution by U.S. State", geo=dict(
            showland=True, landcolor='lightgray', showlakes=True, lakecolor='white'
        ))
        st.plotly_chart(fig4, use_container_width=True)
