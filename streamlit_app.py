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

# Try to import plotly_events for click handling
try:
    from streamlit_plotly_events import plotly_events
    CLICK_ENABLED = True
except ImportError:
    CLICK_ENABLED = False

# Page config
st.set_page_config(
    page_title="Golf Market Opportunity Explorer",
    page_icon="⛳",
    layout="wide"
)

# Initialize session state for selected state
if 'selected_state' not in st.session_state:
    st.session_state.selected_state = 'National (All States)'

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

# Load and prepare data
@st.cache_data
def load_data():
    df = pd.read_csv('census.csv')
    
    # Clean state names (strip whitespace)
    df['state'] = df['state'].str.strip()
    
    # Create calculated columns
    df['diversity'] = 100 - df['pct_white']
    df['affluent'] = df['median_income'] >= df['median_income'].quantile(0.75)
    df['growth_demo_proxy'] = ((50 - df['median_age']).clip(0, 20) / 20 * 50 + 
                               (100 - df['pct_over_65']) / 100 * 50).round(1)
    
    # Add state abbreviations
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
# MAP SECTION
# ============================================================================

st.subheader('🗺️ Market Opportunity Map')

# State selector (also updated by clicks)
col1, col2 = st.columns([3, 1])

with col1:
    selected_state = st.selectbox(
        'View',
        options=['National (All States)'] + sorted(df['state'].unique().tolist()),
        index=0 if st.session_state.selected_state == 'National (All States)' 
              else sorted(df['state'].unique().tolist()).index(st.session_state.selected_state) + 1
              if st.session_state.selected_state in df['state'].unique() else 0,
        key='state_selector'
    )
    st.session_state.selected_state = selected_state

with col2:
    if selected_state != 'National (All States)':
        if st.button('← Back to National'):
            st.session_state.selected_state = 'National (All States)'
            st.rerun()

if selected_state == 'National (All States)':
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
    
    # Try click events, fall back to regular chart
    if CLICK_ENABLED:
        st.caption('👆 **Click any state to drill down** or use the dropdown above')
        clicked = plotly_events(fig, click_event=True, override_height=500)
        
        if clicked and len(clicked) > 0:
            # Get the clicked state
            click_idx = clicked[0].get('pointIndex', None)
            if click_idx is not None and click_idx < len(state_data):
                clicked_state = state_data.iloc[click_idx]['state']
                st.session_state.selected_state = clicked_state
                st.rerun()
    else:
        st.plotly_chart(fig, use_container_width=True)
        st.info('👆 Select a state from the dropdown to drill down. *Tip: Install `streamlit-plotly-events` for click-to-drill-down.*')

else:
    # State drill-down: show counties as horizontal bar chart
    state_df = filtered[filtered['state'] == selected_state].sort_values('opportunity_score', ascending=True)
    
    if len(state_df) == 0:
        st.warning(f'No data for {selected_state}')
    else:
        # State metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Counties', len(state_df))
        c2.metric('High Opportunity', int(state_df['high_opportunity'].sum()))
        c3.metric('Avg Score', f"{state_df['opportunity_score'].mean():.1f}")
        c4.metric('Total Pop', f"{state_df['population'].sum():,.0f}")
        
        # Bar chart
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
        filtered.sample(min(500, len(filtered))),  # Sample for performance
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
    # High opportunity by region
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
