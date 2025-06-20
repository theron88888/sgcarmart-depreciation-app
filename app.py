import pandas as pd
import streamlit as st
import plotly.express as px

# Load your master dataset
df = pd.read_csv("data/used_cars_master.csv")

# Basic cleanup
df['Mileage (km)'] = df['Mileage'].str.replace('km', '').str.replace(
    ',', '').str.extract(r'(\d+)').astype(float)
df['Depreciation ($)'] = df['Depreciation'].str.replace(
    '$', '').str.replace(',', '').str.extract(r'(\d+)').astype(float)
df['Reg Year'] = df['Reg Date'].str.extract(r'(\d{4})')
df = df.dropna(subset=['Reg Year'])
df['Reg Year'] = df['Reg Year'].astype(int)

# Handle reset logic
if 'reset' not in st.session_state:
    st.session_state['reset'] = False

# Sidebar filters
st.sidebar.header("Filter Options")
make_model_input = st.sidebar.text_input(
    "Enter Make & Model (e.g., Honda Vezel)", "")

# Filter dataset by make/model early to dynamically update other filters
filtered_base = df[df['Title'].str.contains(
    make_model_input, case=False, na=False)] if make_model_input else df

owner_options = sorted(filtered_base['Owners'].dropna().unique())
year_options = sorted(filtered_base['Reg Year'].dropna().unique())

# Only set default filters if not reset
if st.session_state['reset']:
    selected_owners = st.sidebar.multiselect(
        "Select Number of Owners", owner_options, default=[])
    selected_years = st.sidebar.multiselect(
        "Select Registration Year(s)", year_options, default=[])
else:
    selected_owners = st.sidebar.multiselect(
        "Select Number of Owners", owner_options)
    selected_years = st.sidebar.multiselect(
        "Select Registration Year(s)", year_options)

min_mileage, max_mileage = st.sidebar.slider(
    "Select Mileage Range (in km)", 0, int(df['Mileage (km)'].max()), (0, 150000))

if st.sidebar.button("Reset Filters"):
    st.session_state['reset'] = True
    st.rerun()
else:
    st.session_state['reset'] = False

# Main App
st.title("\U0001F697 Sgcarmart Used Car Depreciation Explorer")

# Filter based on selections
filtered_df = filtered_base.copy()

if selected_owners:
    filtered_df = filtered_df[filtered_df['Owners'].isin(selected_owners)]
if selected_years:
    filtered_df = filtered_df[filtered_df['Reg Year'].isin(selected_years)]

filtered_df = filtered_df[
    (filtered_df['Mileage (km)'] >= min_mileage) &
    (filtered_df['Mileage (km)'] <= max_mileage)
]

# Display active filters
owner_display = ', '.join(selected_owners) if selected_owners else 'All'
year_display = ', '.join(map(str, selected_years)) if selected_years else 'All'
st.markdown(
    f"Showing results for: **{make_model_input or 'All Models'}**, "
    f"Owners: {owner_display}, Years: {year_display}"
)

if filtered_df.empty:
    st.warning("No results found for your criteria.")
else:
    st.write(f"### Results for '{make_model_input or 'All Models'}'")

    # Summary
    summary = filtered_df.groupby(['Owners', 'Reg Year'])['Depreciation ($)'].agg(
        Average='mean',
        Lowest='min',
        Highest='max'
    ).reset_index().sort_values(by=['Owners', 'Reg Year'])

    st.write(
        "### \U0001F4CA Depreciation Summary by Number of Owners and Registration Year")
    summary[['Average', 'Lowest', 'Highest']] = summary[[
        'Average', 'Lowest', 'Highest']].round(2)
    st.dataframe(summary)

    # Matching Listings Table
    st.write("**Matching Listings**")
    st.dataframe(
        filtered_df[['Title', 'Price', 'Reg Date',
                     'Depreciation', 'Mileage', 'Owners']]
    )

    # Clustered Bar Chart
    st.write("#### \U0001F4CA Clustered Bar Chart: Depreciation Summary")
    owner_options_chart = summary['Owners'].unique().tolist()
    if owner_options_chart:
        selected_owner = st.selectbox(
            "Choose Number of Owners", sorted(owner_options_chart))

        owner_filtered = summary[summary['Owners'] == selected_owner]
        melted = owner_filtered.melt(
            id_vars='Reg Year',
            value_vars=['Average', 'Lowest', 'Highest'],
            var_name='Metric',
            value_name='Depreciation ($)'
        )

        fig = px.bar(
            melted,
            x='Reg Year',
            y='Depreciation ($)',
            color='Metric',
            barmode='group',
            title=f"Depreciation Summary for Owner Count: {selected_owner}",
            labels={'Reg Year': 'Registration Year'},
            height=500
        )
        fig.update_layout(xaxis_tickangle=-45, bargap=0.15, bargroupgap=0.05)
        st.plotly_chart(fig, use_container_width=True)

    # Line Chart
    st.write("#### \U0001F4C8 Depreciation Trends per Owner Count")
    line_chart = px.line(
        summary,
        x='Reg Year',
        y='Average',
        color='Owners',
        markers=True,
        title='Average Depreciation Trend by Owners Over Registration Year',
        labels={'Average': 'Avg Depreciation ($)'}
    )
    st.plotly_chart(line_chart, use_container_width=True)


# use this to run in terminal
# streamlit run app.py
