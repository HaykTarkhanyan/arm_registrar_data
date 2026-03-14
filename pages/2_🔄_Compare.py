"""
Comparison Tool - Compare regions or names side by side.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from data import load_data

st.set_page_config(
    page_title="Compare - Armenian Registrar",
    page_icon="\U0001f504",
    layout="wide",
)


@st.cache_data
def load_cached_data():
    return load_data()


def compare_regions(df):
    regions = sorted(df['region'].dropna().unique())

    col1, col2 = st.columns(2)
    with col1:
        region1 = st.selectbox("Region 1", regions, key="r1")
    with col2:
        default_idx = min(1, len(regions) - 1)
        region2 = st.selectbox("Region 2", regions, index=default_idx, key="r2")

    if region1 == region2:
        st.warning("Please select two different regions to compare")
        return

    df1 = df[df['region'] == region1]
    df2 = df[df['region'] == region2]

    # Overview metrics
    st.markdown("### Overview")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### {region1}")
        st.metric("Population", f"{len(df1):,}")
        st.metric("Average Age", f"{df1['age'].mean():.1f}")
        st.metric("Unique Names", f"{df1['name'].nunique():,}")
        st.metric("Communities", f"{df1['community'].nunique()}")

    with col2:
        st.markdown(f"#### {region2}")
        st.metric("Population", f"{len(df2):,}")
        st.metric("Average Age", f"{df2['age'].mean():.1f}")
        st.metric("Unique Names", f"{df2['name'].nunique():,}")
        st.metric("Communities", f"{df2['community'].nunique()}")

    # Age distribution comparison
    st.markdown("### Age Distribution")
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=df1['age'], name=str(region1), opacity=0.7, nbinsx=30))
    fig.add_trace(go.Histogram(x=df2['age'], name=str(region2), opacity=0.7, nbinsx=30))
    fig.update_layout(
        barmode='overlay',
        xaxis_title="Age",
        yaxis_title="Count",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Top names comparison
    st.markdown("### Top 10 Names")
    col1, col2 = st.columns(2)

    with col1:
        top1 = df1['name'].value_counts().head(10)
        fig = px.bar(
            x=top1.values, y=top1.index, orientation='h',
            title=str(region1),
            labels={'x': 'Count', 'y': 'Name'},
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top2 = df2['name'].value_counts().head(10)
        fig = px.bar(
            x=top2.values, y=top2.index, orientation='h',
            title=str(region2),
            labels={'x': 'Count', 'y': 'Name'},
            color_discrete_sequence=['#ff7f0e'],
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    # Top surnames comparison
    st.markdown("### Top 10 Surnames")
    col1, col2 = st.columns(2)

    with col1:
        top_s1 = df1['surname'].value_counts().head(10)
        fig = px.bar(
            x=top_s1.values, y=top_s1.index, orientation='h',
            title=str(region1),
            labels={'x': 'Count', 'y': 'Surname'},
            color_discrete_sequence=['#2ca02c'],
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top_s2 = df2['surname'].value_counts().head(10)
        fig = px.bar(
            x=top_s2.values, y=top_s2.index, orientation='h',
            title=str(region2),
            labels={'x': 'Count', 'y': 'Surname'},
            color_discrete_sequence=['#d62728'],
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    # Birth year trend comparison
    st.markdown("### Birth Year Trend")
    by1 = pd.to_numeric(df1['birth_date'].str[-4:], errors='coerce').dropna().astype(int)
    by2 = pd.to_numeric(df2['birth_date'].str[-4:], errors='coerce').dropna().astype(int)
    yc1 = by1.value_counts().sort_index()
    yc2 = by2.value_counts().sort_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=yc1.index, y=yc1.values, name=str(region1), mode='lines'))
    fig.add_trace(go.Scatter(x=yc2.index, y=yc2.values, name=str(region2), mode='lines'))
    fig.update_layout(xaxis_title="Birth Year", yaxis_title="Count", height=350)
    st.plotly_chart(fig, use_container_width=True)


def compare_names(df):
    st.markdown("Enter two names to compare their distribution across the population")

    col1, col2 = st.columns(2)
    with col1:
        name1 = st.text_input("Name 1", key="n1")
    with col2:
        name2 = st.text_input("Name 2", key="n2")

    if not name1 or not name2:
        st.info("Enter two names to compare")
        return

    df1 = df[df['name'].str.lower() == name1.strip().lower()]
    df2 = df[df['name'].str.lower() == name2.strip().lower()]

    if len(df1) == 0 and len(df2) == 0:
        st.warning("Neither name found in the database")
        return

    display_name1 = df1['name'].iloc[0] if len(df1) > 0 else name1
    display_name2 = df2['name'].iloc[0] if len(df2) > 0 else name2

    # Overview
    st.markdown("### Overview")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### {display_name1}")
        st.metric("Count", f"{len(df1):,}")
        if len(df1) > 0:
            st.metric("Average Age", f"{df1['age'].mean():.1f}")
            st.metric("Regions", f"{df1['region'].nunique()}")

    with col2:
        st.markdown(f"#### {display_name2}")
        st.metric("Count", f"{len(df2):,}")
        if len(df2) > 0:
            st.metric("Average Age", f"{df2['age'].mean():.1f}")
            st.metric("Regions", f"{df2['region'].nunique()}")

    # Age distribution
    if len(df1) > 0 or len(df2) > 0:
        st.markdown("### Age Distribution")
        fig = go.Figure()
        if len(df1) > 0:
            fig.add_trace(go.Histogram(
                x=df1['age'], name=str(display_name1), opacity=0.7, nbinsx=30
            ))
        if len(df2) > 0:
            fig.add_trace(go.Histogram(
                x=df2['age'], name=str(display_name2), opacity=0.7, nbinsx=30
            ))
        fig.update_layout(
            barmode='overlay', xaxis_title="Age", yaxis_title="Count", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # Geographic distribution
    if len(df1) > 0 or len(df2) > 0:
        st.markdown("### Geographic Distribution")
        col1, col2 = st.columns(2)

        with col1:
            if len(df1) > 0:
                r1 = df1['region'].value_counts()
                fig = px.bar(
                    x=r1.values, y=r1.index, orientation='h',
                    title=str(display_name1),
                    labels={'x': 'Count', 'y': 'Region'},
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No records found for {name1}")

        with col2:
            if len(df2) > 0:
                r2 = df2['region'].value_counts()
                fig = px.bar(
                    x=r2.values, y=r2.index, orientation='h',
                    title=str(display_name2),
                    labels={'x': 'Count', 'y': 'Region'},
                    color_discrete_sequence=['#ff7f0e'],
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No records found for {name2}")

    # Birth year trend
    if len(df1) > 0 or len(df2) > 0:
        st.markdown("### Birth Year Trend")
        fig = go.Figure()
        if len(df1) > 0:
            by1 = pd.to_numeric(df1['birth_date'].str[-4:], errors='coerce').dropna().astype(int)
            yc1 = by1.value_counts().sort_index()
            fig.add_trace(go.Scatter(
                x=yc1.index, y=yc1.values, name=str(display_name1), mode='lines+markers'
            ))
        if len(df2) > 0:
            by2 = pd.to_numeric(df2['birth_date'].str[-4:], errors='coerce').dropna().astype(int)
            yc2 = by2.value_counts().sort_index()
            fig.add_trace(go.Scatter(
                x=yc2.index, y=yc2.values, name=str(display_name2), mode='lines+markers'
            ))
        fig.update_layout(xaxis_title="Birth Year", yaxis_title="Count", height=350)
        st.plotly_chart(fig, use_container_width=True)


def main():
    st.title("\U0001f504 Comparison Tool")
    st.markdown("Compare regions or names side by side")

    df = load_cached_data()

    comparison_type = st.radio("Compare by", ["Regions", "Names"], horizontal=True)

    st.markdown("---")

    if comparison_type == "Regions":
        compare_regions(df)
    else:
        compare_names(df)


if __name__ == "__main__":
    main()
