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

# State abbreviation mapping
STATE_ABBREV = {
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

ABBREV_TO_STATE = {v: k for k, v in STATE_ABBREV.items()}

# Load and prepare data
@st.cache_data
def load_data():
    df = pd.read_csv('census.csv')
    df['state'] = df['state'].str.strip()
    df['diversity'] = 100 - df['pct_white']
    df['affluent'] = df['median_income'] >= df['median_income'].quantile(0.75)
    df['growth_demo_proxy'] = ((50 - df['median_age']).clip(0, 20) / 20 * 50 + 
                               (100 - df['pct_over_65']) / 100 * 50).round(1)
    df['state_abbrev'] = df['state'].map(STATE_ABBREV)
    return df

# Calculate opportunity score
def calc_opp_score(df, w_inc, w_edu, w_div, w_pop, w_age):
    inc = (df['median_income'] / df['median_income'].max()).clip(0, 1)
    edu = (df['pct_college'] / df['pct_college'].max()).clip(0, 1)
    div = (df['diversity'] / df['diversity'].max()).clip(0, 1)
    pop = (np.log1p(df['population']) / np.log1p(df['population'].max())).clip(0, 1)
    age = ((50 - df['median_age']).clip(0, 20) / 20)
    total = w_inc + w_edu + w_div + w_pop + w_age
    return ((inc * w_inc + edu * w_edu + div * w_div + pop * w_pop + age * w_age) / total * 100).round(1)

# Load data
df = load_data()

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.header('⛳ Golf Market Explorer')

st.sidebar.markdown('---')
st.sidebar.subheader('📊 Target Market Thresholds')

income_threshold = st.sidebar.slider(
    'Min Household Income',
    min_value=30000, max_value=150000, value=75000, step=5000, format='$%d'
)

growth_demo_min = st.sidebar.slider(
    'Min Growth Demo Score',
    min_value=0, max_value=100, value=50,
    help='Higher = younger population'
)

st.sidebar.markdown('---')
st.sidebar.subheader('🌎 Region Filter')

all_regions = sorted(df['region'].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect('Regions', all_regions, default=all_regions)

st.sidebar.markdown('---')
st.sidebar.subheader('⚖️ Score Weights')

w_inc = st.sidebar.slider('Income', 0, 100, 35)
w_edu = st.sidebar.slider('Education', 0, 100, 25)
w_div = st.sidebar.slider('Diversity', 0, 100, 15)
w_pop = st.sidebar.slider('Population', 0, 100, 15)
w_age = st.sidebar.slider('Youth', 0, 100, 10)

# Apply calculations
df['opportunity_score'] = calc_opp_score(df, w_inc, w_edu, w_div, w_pop, w_age)
df['high_opportunity'] = (df['median_income'] >= income_threshold) & (df['growth_demo_proxy'] >= growth_demo_min)

# Filter by region
filtered = df[df['region'].isin(selected_regions)].copy() if selected_regions else df.copy()

# ============================================================================
# MAIN PAGE
# ============================================================================

st.title('⛳ Golf Market Opportunity Explorer')
st.markdown('*Identify high-potential counties for Titleist and FootJoy marketing*')

# Metrics row
c1, c2, c3, c4 = st.columns(4)
c1.metric('Total Counties', f'{len(filtered):,}')
c2.metric('High Opportunity', f'{filtered["high_opportunity"].sum():,}')
c3.metric('% High Opp', f'{filtered["high_opportunity"].mean()*100:.1f}%')
c4.metric('Avg Score', f'{filtered["opportunity_score"].mean():.1f}')

st.markdown('---')

# ============================================================================
# MAP SECTION WITH TABS
# ============================================================================

st.subheader('🗺️ Market Opportunity Map')

# Use tabs for National vs State view
tab1, tab2 = st.tabs(['🇺🇸 National View', '🔍 State Drill-Down'])

with tab1:
    # Aggregate to state level
    state_data = filtered.groupby(['state', 'state_abbrev']).agg({
        'opportunity_score': 'mean',
        'high_opportunity': 'sum',
        'population': 'sum',
        'median_income': 'median',
        'county': 'count'
    }).reset_index()
    state_data.columns = ['state', 'state_abbrev', 'avg_score', 'high_opp', 'pop', 'med_inc', 'n_counties']
    
    # Create choropleth
    fig = px.choropleth(
        state_data,
        locations='state_abbrev',
        locationmode='USA-states',
        color='avg_score',
        scope='usa',
        color_continuous_scale='RdYlGn',
        range_color=[30, 55],
        hover_name='state',
        hover_data={'state_abbrev': False, 'avg_score': ':.1f', 'high_opp': True, 'n_counties': True},
        labels={'avg_score': 'Avg Score', 'high_opp': 'High Opp Counties', 'n_counties': 'Counties'}
    )
    fig.update_layout(
        geo=dict(bgcolor='rgba(0,0,0,0)', lakecolor='lightblue'),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top states table
    st.markdown('#### Top 10 States by Opportunity Score')
    top_states = state_data.nlargest(10, 'avg_score')[['state', 'avg_score', 'high_opp', 'n_counties', 'med_inc']]
    top_states.columns = ['State', 'Avg Score', 'High Opp Counties', 'Total Counties', 'Median Income']
    top_states = top_states.reset_index(drop=True)
    top_states.index = top_states.index + 1
    st.dataframe(
        top_states.style.format({
            'Avg Score': '{:.1f}',
            'Median Income': '${:,.0f}'
        }),
        use_container_width=True
    )

with tab2:
    # State selector with quick-select buttons for top states
    st.markdown('**Quick Select (Top 5 States):**')
    
    top_5_states = state_data.nlargest(5, 'avg_score')['state'].tolist()
    
    cols = st.columns(5)
    selected_state = None
    
    for i, state in enumerate(top_5_states):
        if cols[i].button(state, use_container_width=True):
            selected_state = state
    
    st.markdown('**Or choose from all states:**')
    dropdown_state = st.selectbox(
        'Select State',
        options=[''] + sorted(df['state'].unique().tolist()),
        format_func=lambda x: 'Choose a state...' if x == '' else x
    )
    
    # Use button selection if clicked, otherwise dropdown
    if selected_state is None and dropdown_state:
        selected_state = dropdown_state
    
    if selected_state:
        state_df = filtered[filtered['state'] == selected_state].sort_values('opportunity_score', ascending=True)
        
        st.markdown(f'### {selected_state}')
        
        # State metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Counties', len(state_df))
        c2.metric('High Opportunity', int(state_df['high_opportunity'].sum()))
        c3.metric('Avg Score', f"{state_df['opportunity_score'].mean():.1f}")
        c4.metric('Total Pop', f"{state_df['population'].sum():,.0f}")
        
        # Bar chart of counties
        fig = px.bar(
            state_df,
            x='opportunity_score',
            y='county',
            orientation='h',
            color='opportunity_score',
            color_continuous_scale='RdYlGn',
            range_color=[20, 80],
            hover_data=['median_income', 'pct_college', 'diversity', 'population'],
            labels={'opportunity_score': 'Opportunity Score', 'county': ''}
        )
        fig.update_layout(
            height=max(400, len(state_df) * 22),
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top counties table
        st.markdown(f'#### Top 10 Counties in {selected_state}')
        top_counties = state_df.nlargest(10, 'opportunity_score')[
            ['county', 'opportunity_score', 'median_income', 'pct_college', 'diversity', 'population']
        ].reset_index(drop=True)
        top_counties.index = top_counties.index + 1
        st.dataframe(
            top_counties.style.format({
                'opportunity_score': '{:.1f}',
                'median_income': '${:,.0f}',
                'pct_college': '{:.1f}%',
                'diversity': '{:.1f}%',
                'population': '{:,.0f}'
            }),
            use_container_width=True
        )
    else:
        st.info('👆 Select a state using the buttons above or the dropdown')

st.markdown('---')

# ============================================================================
# SCENARIO ANALYSIS
# ============================================================================

st.subheader('🎯 Scenario Analysis')

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    **Your Thresholds:**  
    Income ≥ **${income_threshold:,}** | Growth Demo ≥ **{growth_demo_min}**
    
    **Result:** {filtered['high_opportunity'].sum():,} counties qualify
    """)
    
    # Scatter with threshold lines
    fig = px.scatter(
        filtered.sample(min(500, len(filtered)), random_state=42),
        x='median_income', y='growth_demo_proxy',
        color='high_opportunity',
        color_discrete_map={True: 'forestgreen', False: 'lightgray'},
        hover_name='county',
        labels={'median_income': 'Median Income', 'growth_demo_proxy': 'Growth Demo Score'}
    )
    fig.add_vline(x=income_threshold, line_dash='dash', line_color='red')
    fig.add_hline(y=growth_demo_min, line_dash='dash', line_color='red')
    fig.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    by_region = filtered[filtered['high_opportunity']].groupby('region').size().reset_index(name='count')
    by_region = by_region.sort_values('count')
    
    fig = px.bar(
        by_region, x='count', y='region', orientation='h',
        color='count', color_continuous_scale='Greens',
        labels={'count': 'High Opportunity Counties', 'region': ''}
    )
    fig.update_layout(height=350, showlegend=False, title='High Opportunity by Region')
    st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

# ============================================================================
# DATA TABLE
# ============================================================================

st.subheader('🏆 Top Counties')

show_high_only = st.checkbox('Show only High Opportunity')
data_to_show = filtered[filtered['high_opportunity']] if show_high_only else filtered

n = st.slider('Show top N', 10, 100, 25)
top = data_to_show.nlargest(n, 'opportunity_score')[
    ['state', 'county', 'opportunity_score', 'median_income', 'pct_college', 'diversity', 'population', 'high_opportunity']
].reset_index(drop=True)
top.index = top.index + 1

st.dataframe(
    top.style.format({
        'opportunity_score': '{:.1f}',
        'median_income': '${:,.0f}',
        'pct_college': '{:.1f}%',
        'diversity': '{:.1f}%',
        'population': '{:,.0f}'
    }),
    use_container_width=True
)

# Downloads
st.markdown('---')
c1, c2 = st.columns(2)
c1.download_button('📥 All Filtered Data', filtered.to_csv(index=False), 'golf_all.csv')
c2.download_button('📥 High Opportunity Only', filtered[filtered['high_opportunity']].to_csv(index=False), 'golf_high_opp.csv')

# Footer
st.markdown('---')
st.caption('Data: US Census ACS 2015-2019 | Methodology: NGF Research | Author: Cook Welch, BC MBA')
