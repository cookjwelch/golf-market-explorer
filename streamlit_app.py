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
    
    return df

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

# Load data
df = load_data()

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.header('⛳ Golf Market Explorer')
st.sidebar.markdown('---')

# Region filter
st.sidebar.subheader('Filter by Region')
all_regions = df['region'].dropna().unique().tolist()
selected_regions = st.sidebar.multiselect(
    'Select Regions',
    options=all_regions,
    default=all_regions
)

# Score filter
st.sidebar.subheader('Filter by Opportunity Score')
min_score = st.sidebar.slider('Minimum Score', 0, 100, 0)

# Affluent filter
st.sidebar.subheader('Filter by Affluence')
affluent_filter = st.sidebar.radio(
    'Show Counties',
    options=['All', 'Affluent Only', 'Non-Affluent Only'],
    index=0
)

st.sidebar.markdown('---')

# Custom weights
st.sidebar.subheader('Adjust Opportunity Weights')
st.sidebar.markdown('*Customize what matters most*')

w_income = st.sidebar.slider('Income', 0, 100, 35)
w_education = st.sidebar.slider('Education', 0, 100, 25)
w_diversity = st.sidebar.slider('Diversity', 0, 100, 15)
w_size = st.sidebar.slider('Population Size', 0, 100, 15)
w_age = st.sidebar.slider('Younger Age', 0, 100, 10)

# Recalculate score with custom weights
df['opportunity_score'] = calculate_opportunity_score(df, w_income, w_education, w_diversity, w_size, w_age)

# ============================================================================
# APPLY FILTERS
# ============================================================================

filtered = df.copy()

# Region filter
if selected_regions:
    filtered = filtered[filtered['region'].isin(selected_regions)]

# Score filter
filtered = filtered[filtered['opportunity_score'] >= min_score]

# Affluent filter
if affluent_filter == 'Affluent Only':
    filtered = filtered[filtered['affluent'] == True]
elif affluent_filter == 'Non-Affluent Only':
    filtered = filtered[filtered['affluent'] == False]

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title('⛳ Golf Market Opportunity Explorer')
st.markdown('*Identify high-potential counties for Titleist and FootJoy marketing*')

# Key metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric('Counties Shown', f'{len(filtered):,}')
with col2:
    st.metric('Total Population', f'{filtered["population"].sum():,.0f}')
with col3:
    st.metric('Avg Opportunity Score', f'{filtered["opportunity_score"].mean():.1f}')
with col4:
    st.metric('Affluent Counties', f'{filtered["affluent"].sum():,}')

st.markdown('---')

# ============================================================================
# MAP
# ============================================================================

st.subheader('📍 Opportunity Score by State')

# Aggregate to state level
state_avg = filtered.groupby('state')['opportunity_score'].mean().reset_index()
state_avg['state_abbrev'] = state_avg['state'].map(state_abbrev)

fig_map = px.choropleth(
    state_avg,
    locations='state_abbrev',
    locationmode='USA-states',
    color='opportunity_score',
    scope='usa',
    color_continuous_scale='RdYlGn',
    range_color=[0, state_avg['opportunity_score'].max()],
    labels={'opportunity_score': 'Opportunity Score'}
)
fig_map.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    height=450
)
st.plotly_chart(fig_map, use_container_width=True)

# ============================================================================
# CHARTS ROW
# ============================================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader('📊 Score Distribution by Region')
    fig_box = px.box(
        filtered,
        x='region',
        y='opportunity_score',
        color='region',
        labels={'opportunity_score': 'Opportunity Score', 'region': 'Region'}
    )
    fig_box.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_box, use_container_width=True)

with col2:
    st.subheader('💰 Income vs Diversity Tradeoff')
    fig_scatter = px.scatter(
        filtered,
        x='median_income',
        y='diversity',
        color='affluent',
        hover_name='county',
        hover_data=['state', 'opportunity_score'],
        labels={
            'median_income': 'Median Income',
            'diversity': 'Diversity Index',
            'affluent': 'Affluent'
        },
        color_discrete_map={True: 'green', False: 'gray'}
    )
    fig_scatter.update_layout(height=400)
    st.plotly_chart(fig_scatter, use_container_width=True)

# ============================================================================
# TOP COUNTIES TABLE
# ============================================================================

st.markdown('---')
st.subheader('🏆 Top Counties by Opportunity Score')

top_n = st.slider('Number of counties to show', 10, 100, 25)

top_counties = filtered.nlargest(top_n, 'opportunity_score')[
    ['state', 'county', 'opportunity_score', 'median_income', 'pct_college', 'diversity', 'median_age', 'population', 'affluent']
].reset_index(drop=True)

top_counties.columns = ['State', 'County', 'Opportunity Score', 'Median Income', '% College', 'Diversity', 'Median Age', 'Population', 'Affluent']
top_counties.index = top_counties.index + 1

st.dataframe(
    top_counties.style.format({
        'Opportunity Score': '{:.1f}',
        'Median Income': '${:,.0f}',
        '% College': '{:.1f}%',
        'Diversity': '{:.1f}%',
        'Median Age': '{:.1f}',
        'Population': '{:,.0f}'
    }),
    use_container_width=True,
    height=400
)

# ============================================================================
# DOWNLOAD
# ============================================================================

st.markdown('---')
st.subheader('📥 Download Data')

csv = filtered.to_csv(index=False)
st.download_button(
    label='Download Filtered Data as CSV',
    data=csv,
    file_name='golf_market_filtered.csv',
    mime='text/csv'
)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown('---')
st.markdown('''
**Data Source:** U.S. Census Bureau American Community Survey (2015-2019)  
**Methodology:** Opportunity score based on National Golf Foundation golfer demographics research  
**Author:** Cook Welch, Boston College MBA
''')
