"""
Golf Market Opportunity Explorer
Streamlit App for Acushnet/Titleist Marketing Analysis

Author: Cook Welch
Boston College MBA
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

# Page config
st.set_page_config(
    page_title="Golf Market Opportunity Explorer",
    page_icon="⛳",
    layout="wide"
)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('census.csv')
    
    # Create diversity column
    df['diversity'] = 100 - df['pct_white']
    
    # Create affluent flag (top quartile of income)
    income_threshold = df['median_income'].quantile(0.75)
    df['affluent'] = df['median_income'] >= income_threshold
    
    # Estimate growth demographic (% aged 25-40)
    df['growth_demo_proxy'] = ((50 - df['median_age']).clip(0, 20) / 20 * 50 + 
                               (100 - df['pct_over_65']) / 100 * 50).round(1)
    
    # Ensure FIPS is 5 digits with leading zeros
    df['fips'] = df['fips'].astype(str).str.zfill(5)
    
    return df

# Load county GeoJSON
@st.cache_data
def load_counties_geojson():
    # Use plotly's built-in county data via URL
    from urllib.request import urlopen
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)
    return counties

# Calculate opportunity score with custom weights
def calculate_opportunity_score(df, w_income, w_education, w_diversity, w_size, w_age):
    income_score = (df['median_income'] / df['median_income'].max()).clip(0, 1)
    education_score = (df['pct_college'] / df['pct_college'].max()).clip(0, 1)
    diversity_score = (df['diversity'] / df['diversity'].max()).clip(0, 1)
    size_score = (np.log1p(df['population']) / np.log1p(df['population'].max())).clip(0, 1)
    age_score = ((50 - df['median_age']).clip(0, 20) / 20)
    
    total_weight = w_income + w_education + w_diversity + w_size + w_age
    
    score = (
        income_score * w_income +
        education_score * w_education +
        diversity_score * w_diversity +
        size_score * w_size +
        age_score * w_age
    ) / total_weight * 100
    
    return score.round(1)

# State abbreviation mapping
state_abbrev = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
    'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
    'District of Columbia': 'DC'
}

# State center coordinates for zooming
state_centers = {
    'Alabama': {'lat': 32.7, 'lon': -86.7, 'zoom': 5.5},
    'Alaska': {'lat': 64.0, 'lon': -153.0, 'zoom': 3},
    'Arizona': {'lat': 34.2, 'lon': -111.6, 'zoom': 5.5},
    'Arkansas': {'lat': 34.8, 'lon': -92.4, 'zoom': 6},
    'California': {'lat': 37.2, 'lon': -119.4, 'zoom': 4.5},
    'Colorado': {'lat': 39.0, 'lon': -105.5, 'zoom': 5.5},
    'Connecticut': {'lat': 41.6, 'lon': -72.7, 'zoom': 7.5},
    'Delaware': {'lat': 39.0, 'lon': -75.5, 'zoom': 7.5},
    'Florida': {'lat': 28.6, 'lon': -82.4, 'zoom': 5},
    'Georgia': {'lat': 32.6, 'lon': -83.4, 'zoom': 5.5},
    'Hawaii': {'lat': 20.8, 'lon': -156.3, 'zoom': 5.5},
    'Idaho': {'lat': 44.4, 'lon': -114.6, 'zoom': 5},
    'Illinois': {'lat': 40.0, 'lon': -89.2, 'zoom': 5.5},
    'Indiana': {'lat': 39.9, 'lon': -86.3, 'zoom': 5.5},
    'Iowa': {'lat': 42.0, 'lon': -93.5, 'zoom': 5.5},
    'Kansas': {'lat': 38.5, 'lon': -98.4, 'zoom': 5.5},
    'Kentucky': {'lat': 37.5, 'lon': -85.3, 'zoom': 6},
    'Louisiana': {'lat': 31.0, 'lon': -92.0, 'zoom': 5.5},
    'Maine': {'lat': 45.4, 'lon': -69.2, 'zoom': 5.5},
    'Maryland': {'lat': 39.0, 'lon': -76.7, 'zoom': 6.5},
    'Massachusetts': {'lat': 42.2, 'lon': -71.5, 'zoom': 7},
    'Michigan': {'lat': 44.3, 'lon': -85.4, 'zoom': 5},
    'Minnesota': {'lat': 46.3, 'lon': -94.3, 'zoom': 5},
    'Mississippi': {'lat': 32.7, 'lon': -89.7, 'zoom': 5.5},
    'Missouri': {'lat': 38.3, 'lon': -92.4, 'zoom': 5.5},
    'Montana': {'lat': 47.0, 'lon': -110.0, 'zoom': 5},
    'Nebraska': {'lat': 41.5, 'lon': -99.8, 'zoom': 5.5},
    'Nevada': {'lat': 39.3, 'lon': -116.6, 'zoom': 5},
    'New Hampshire': {'lat': 43.7, 'lon': -71.6, 'zoom': 6.5},
    'New Jersey': {'lat': 40.2, 'lon': -74.7, 'zoom': 6.5},
    'New Mexico': {'lat': 34.4, 'lon': -106.1, 'zoom': 5.5},
    'New York': {'lat': 42.9, 'lon': -75.5, 'zoom': 5.5},
    'North Carolina': {'lat': 35.5, 'lon': -79.4, 'zoom': 5.5},
    'North Dakota': {'lat': 47.4, 'lon': -100.3, 'zoom': 5.5},
    'Ohio': {'lat': 40.4, 'lon': -82.8, 'zoom': 6},
    'Oklahoma': {'lat': 35.6, 'lon': -97.5, 'zoom': 5.5},
    'Oregon': {'lat': 44.0, 'lon': -120.5, 'zoom': 5.5},
    'Pennsylvania': {'lat': 40.9, 'lon': -77.8, 'zoom': 6},
    'Rhode Island': {'lat': 41.7, 'lon': -71.5, 'zoom': 8.5},
    'South Carolina': {'lat': 33.9, 'lon': -80.9, 'zoom': 6},
    'South Dakota': {'lat': 44.4, 'lon': -100.2, 'zoom': 5.5},
    'Tennessee': {'lat': 35.8, 'lon': -86.3, 'zoom': 5.5},
    'Texas': {'lat': 31.5, 'lon': -99.4, 'zoom': 4.5},
    'Utah': {'lat': 39.3, 'lon': -111.7, 'zoom': 5.5},
    'Vermont': {'lat': 44.0, 'lon': -72.7, 'zoom': 6.5},
    'Virginia': {'lat': 37.5, 'lon': -78.8, 'zoom': 5.5},
    'Washington': {'lat': 47.4, 'lon': -120.5, 'zoom': 5.5},
    'West Virginia': {'lat': 38.9, 'lon': -80.5, 'zoom': 6},
    'Wisconsin': {'lat': 44.6, 'lon': -89.7, 'zoom': 5.5},
    'Wyoming': {'lat': 43.0, 'lon': -107.5, 'zoom': 5.5},
    'District of Columbia': {'lat': 38.9, 'lon': -77.0, 'zoom': 10}
}

# Load data
df = load_data()

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.header('⛳ Golf Market Explorer')

# Scenario Definition Section
st.sidebar.markdown('---')
st.sidebar.subheader('📊 Define Your Target Market')
st.sidebar.markdown('*Set thresholds for "High Opportunity"*')

# Income threshold slider
income_threshold = st.sidebar.slider(
    'Minimum Household Income',
    min_value=30000,
    max_value=150000,
    value=75000,
    step=5000,
    format='$%d'
)

# Growth demographic slider
growth_demo_min = st.sidebar.slider(
    'Growth Demographic Score',
    min_value=0,
    max_value=100,
    value=50,
    help='Higher = younger population (ages 25-40 proxy)'
)

# Mark high opportunity based on scenario
df['high_opportunity'] = (df['median_income'] >= income_threshold) & (df['growth_demo_proxy'] >= growth_demo_min)

st.sidebar.markdown('---')

# Region filter
st.sidebar.subheader('🌎 Filter by Region')
all_regions = df['region'].dropna().unique().tolist()
selected_regions = st.sidebar.multiselect(
    'Select Regions',
    options=all_regions,
    default=all_regions
)

st.sidebar.markdown('---')

# Custom weights for opportunity score
st.sidebar.subheader('⚖️ Opportunity Score Weights')

w_income = st.sidebar.slider('Income', 0, 100, 35)
w_education = st.sidebar.slider('Education', 0, 100, 25)
w_diversity = st.sidebar.slider('Diversity', 0, 100, 15)
w_size = st.sidebar.slider('Population', 0, 100, 15)
w_age = st.sidebar.slider('Youth', 0, 100, 10)

# Recalculate score
df['opportunity_score'] = calculate_opportunity_score(df, w_income, w_education, w_diversity, w_size, w_age)

# ============================================================================
# APPLY FILTERS
# ============================================================================

filtered = df.copy()
if selected_regions:
    filtered = filtered[filtered['region'].isin(selected_regions)]

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title('⛳ Golf Market Opportunity Explorer')
st.markdown('*Identify high-potential counties for Titleist and FootJoy marketing*')

# Key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric('Total Counties', f'{len(filtered):,}')
with col2:
    high_opp_count = filtered['high_opportunity'].sum()
    st.metric('High Opportunity', f'{high_opp_count:,}')
with col3:
    high_opp_pct = high_opp_count / len(filtered) * 100 if len(filtered) > 0 else 0
    st.metric('% High Opportunity', f'{high_opp_pct:.1f}%')
with col4:
    st.metric('Avg Score', f'{filtered["opportunity_score"].mean():.1f}')

st.markdown('---')

# ============================================================================
# INTERACTIVE MAP
# ============================================================================

st.subheader('🗺️ Interactive County Heatmap')
st.markdown('*Select a state to zoom in, or view the national picture*')

# State selector
col_select, col_reset = st.columns([3, 1])
with col_select:
    selected_state = st.selectbox(
        'Select State to Drill Down',
        options=['All States (National View)'] + sorted(df['state'].unique().tolist())
    )
with col_reset:
    st.markdown('')  # spacer

# Load GeoJSON for county boundaries
try:
    counties_geojson = load_counties_geojson()
    geojson_loaded = True
except:
    geojson_loaded = False
    st.warning('County boundaries unavailable. Showing state-level map.')

if selected_state == 'All States (National View)':
    # NATIONAL VIEW - County choropleth
    if geojson_loaded:
        fig_map = px.choropleth(
            filtered,
            geojson=counties_geojson,
            locations='fips',
            color='opportunity_score',
            color_continuous_scale='RdYlGn',
            range_color=[20, 80],
            scope='usa',
            hover_name='county',
            hover_data={
                'fips': False,
                'state': True,
                'opportunity_score': ':.1f',
                'median_income': ':$,.0f',
                'pct_college': ':.1f',
                'high_opportunity': True
            },
            labels={
                'opportunity_score': 'Opportunity Score',
                'median_income': 'Median Income',
                'pct_college': '% College',
                'high_opportunity': 'High Opportunity'
            }
        )
        fig_map.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            height=550,
            coloraxis_colorbar=dict(title="Score")
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
    else:
        # Fallback to state-level
        state_avg = filtered.groupby('state')['opportunity_score'].mean().reset_index()
        state_avg['state_abbrev'] = state_avg['state'].map(state_abbrev)
        fig_map = px.choropleth(
            state_avg,
            locations='state_abbrev',
            locationmode='USA-states',
            color='opportunity_score',
            scope='usa',
            color_continuous_scale='RdYlGn',
            range_color=[20, 60]
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
    
    st.plotly_chart(fig_map, use_container_width=True)

else:
    # STATE DRILL-DOWN VIEW
    state_data = filtered[filtered['state'] == selected_state].copy()
    
    if len(state_data) == 0:
        st.warning(f'No data available for {selected_state}')
    else:
        # Get state center for zoom
        center = state_centers.get(selected_state, {'lat': 39.8, 'lon': -98.5, 'zoom': 4})
        
        if geojson_loaded:
            fig_state = px.choropleth(
                state_data,
                geojson=counties_geojson,
                locations='fips',
                color='opportunity_score',
                color_continuous_scale='RdYlGn',
                range_color=[20, 80],
                hover_name='county',
                hover_data={
                    'fips': False,
                    'opportunity_score': ':.1f',
                    'median_income': ':$,.0f',
                    'pct_college': ':.1f',
                    'diversity': ':.1f',
                    'population': ':,.0f',
                    'high_opportunity': True
                },
                labels={
                    'opportunity_score': 'Score',
                    'median_income': 'Income',
                    'pct_college': '% College',
                    'diversity': 'Diversity',
                    'population': 'Population',
                    'high_opportunity': 'High Opp'
                }
            )
            fig_state.update_geos(
                center=dict(lat=center['lat'], lon=center['lon']),
                projection_scale=center['zoom'],
                visible=False
            )
            fig_state.update_layout(
                margin={"r":0,"t":30,"l":0,"b":0},
                height=500,
                title=f'{selected_state} Counties by Opportunity Score'
            )
            st.plotly_chart(fig_state, use_container_width=True)
        
        # State summary
        st.markdown(f'### {selected_state} Summary')
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric('Counties', len(state_data))
        with col2:
            st.metric('High Opportunity', int(state_data['high_opportunity'].sum()))
        with col3:
            st.metric('Avg Score', f"{state_data['opportunity_score'].mean():.1f}")
        with col4:
            st.metric('Total Pop', f"{state_data['population'].sum():,.0f}")
        
        # Top counties in state
        st.markdown(f'#### Top Counties in {selected_state}')
        top_in_state = state_data.nlargest(10, 'opportunity_score')[
            ['county', 'opportunity_score', 'median_income', 'pct_college', 'diversity', 'population', 'high_opportunity']
        ].reset_index(drop=True)
        top_in_state.index = top_in_state.index + 1
        st.dataframe(
            top_in_state.style.format({
                'opportunity_score': '{:.1f}',
                'median_income': '${:,.0f}',
                'pct_college': '{:.1f}%',
                'diversity': '{:.1f}%',
                'population': '{:,.0f}'
            }),
            use_container_width=True
        )

st.markdown('---')

# ============================================================================
# SCENARIO ANALYSIS
# ============================================================================

st.subheader('🎯 Scenario Analysis')

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    **Your Target Market Definition:**
    - Income ≥ **${income_threshold:,}**
    - Growth Demo ≥ **{growth_demo_min}**
    
    **Result:** **{filtered['high_opportunity'].sum():,}** counties qualify 
    ({filtered['high_opportunity'].sum() / len(filtered) * 100:.1f}%)
    """)
    
    fig_scatter = px.scatter(
        filtered,
        x='median_income',
        y='growth_demo_proxy',
        color='high_opportunity',
        hover_name='county',
        hover_data=['state', 'opportunity_score'],
        color_discrete_map={True: 'forestgreen', False: 'lightgray'},
        labels={'median_income': 'Median Income', 'growth_demo_proxy': 'Growth Demo Score'}
    )
    fig_scatter.add_vline(x=income_threshold, line_dash="dash", line_color="red")
    fig_scatter.add_hline(y=growth_demo_min, line_dash="dash", line_color="red")
    fig_scatter.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:
    high_opp_by_region = filtered[filtered['high_opportunity']].groupby('region').size().reset_index(name='count')
    high_opp_by_region = high_opp_by_region.sort_values('count', ascending=True)
    
    fig_region = px.bar(
        high_opp_by_region,
        x='count',
        y='region',
        orientation='h',
        color='count',
        color_continuous_scale='Greens',
        labels={'count': 'High Opportunity Counties', 'region': 'Region'}
    )
    fig_region.update_layout(height=350, title='High Opportunity by Region', showlegend=False)
    st.plotly_chart(fig_region, use_container_width=True)

st.markdown('---')

# ============================================================================
# TOP COUNTIES TABLE
# ============================================================================

st.subheader('🏆 Top Counties')

show_high_only = st.checkbox('Show only High Opportunity counties', value=False)
table_data = filtered[filtered['high_opportunity']] if show_high_only else filtered

top_n = st.slider('Number to show', 10, 100, 25)

top_counties = table_data.nlargest(top_n, 'opportunity_score')[
    ['state', 'county', 'opportunity_score', 'median_income', 'pct_college', 
     'diversity', 'median_age', 'population', 'high_opportunity']
].reset_index(drop=True)
top_counties.index = top_counties.index + 1

st.dataframe(
    top_counties.style.format({
        'opportunity_score': '{:.1f}',
        'median_income': '${:,.0f}',
        'pct_college': '{:.1f}%',
        'diversity': '{:.1f}%',
        'median_age': '{:.1f}',
        'population': '{:,.0f}'
    }),
    use_container_width=True,
    height=400
)

# ============================================================================
# DOWNLOAD
# ============================================================================

st.markdown('---')
col1, col2 = st.columns(2)
with col1:
    st.download_button('📥 Download All Data', filtered.to_csv(index=False), 'golf_market_all.csv', 'text/csv')
with col2:
    st.download_button('📥 Download High Opportunity', filtered[filtered['high_opportunity']].to_csv(index=False), 'golf_market_high_opp.csv', 'text/csv')

# Footer
st.markdown('---')
st.markdown('''
**Data:** U.S. Census ACS (2015-2019) | **Methodology:** NGF golfer demographics | **Author:** Cook Welch, BC MBA
''')
