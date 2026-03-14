"""
EDA Page - Reads pre-computed statistics from eda_cache.pkl.
Run `python precompute_eda.py` to regenerate the cache.
"""

import os
import streamlit as st
import pandas as pd
import pickle
from pathlib import Path
import plotly.express as px

CACHE_PATH = "eda_cache.pkl"
CACHE_PATH_ENC = "eda_cache.pkl.enc"

st.set_page_config(
    page_title="Data Analysis - Armenian Registrar",
    page_icon="\U0001f4ca",
    layout="wide",
)


def _get_key() -> str | None:
    """Get decryption key from Streamlit secrets, .env, or environment."""
    try:
        return st.secrets["DATA_KEY"]
    except Exception:
        pass
    key = os.environ.get("DATA_KEY")
    if not key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("DATA_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key


@st.cache_data
def load_stats():
    if Path(CACHE_PATH).exists():
        with open(CACHE_PATH, 'rb') as f:
            return pickle.load(f)
    elif Path(CACHE_PATH_ENC).exists():
        from cryptography.fernet import Fernet
        key = _get_key()
        if not key:
            raise RuntimeError(
                "Encrypted cache found but DATA_KEY is not set. "
                "Add it in .streamlit/secrets.toml, .env, or as an environment variable."
            )
        fernet = Fernet(key.encode())
        raw = fernet.decrypt(Path(CACHE_PATH_ENC).read_bytes())
        return pickle.loads(raw)
    else:
        raise FileNotFoundError(f"Neither {CACHE_PATH} nor {CACHE_PATH_ENC} found.")


def main():
    st.title("\U0001f4ca Armenian Registrar Data - Exploratory Data Analysis")
    st.markdown("Comprehensive analysis of voter registration data")

    try:
        s = load_stats()
    except FileNotFoundError:
        st.error(f"Cache file `{CACHE_PATH}` not found.")
        st.info("Run `python precompute_eda.py` to generate it.")
        return

    # Overview
    st.header("\U0001f4cb Dataset Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Population", f"{s['total_records']:,}")
    col2.metric("Unique Names", f"{s['unique_names']:,}")
    col3.metric("Unique Surnames", f"{s['unique_surnames']:,}")
    col4.metric("Communities", f"{s['unique_communities']:,}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Average Age", f"{s['avg_age']:.1f} years")
    col2.metric("Median Age", f"{s['median_age']:.0f} years")
    col3.metric("Youngest", f"{s['min_age']} years")
    col4.metric("Oldest", f"{s['max_age']} years")

    st.divider()

    tab1, tab2, tab3, tab4, tab_bday, tab5, tab6, tab_records, tab7 = st.tabs([
        "\U0001f465 Demographics",
        "\U0001f4db Names Analysis",
        "\U0001f5fa\ufe0f Geographic",
        "\U0001f4c5 Temporal Patterns",
        "\U0001f382 Birthdays",
        "\U0001f52e Fun Insights",
        "\U0001f3e0 Household Analysis",
        "\U0001f3c6 Records & Superlatives",
        "\U0001f50d Data Quality",
    ])

    # ── Tab 1: Demographics ──────────────────────────────────────────
    with tab1:
        st.header("Demographics Analysis")

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                x=s['age_distribution'].index.astype(str),
                y=s['age_distribution'].values,
                title="Population by Age Group",
                labels={'x': 'Age Group', 'y': 'Count'},
                color=s['age_distribution'].values,
                color_continuous_scale='Viridis',
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.pie(
                names=s['generation_counts'].index,
                values=s['generation_counts'].values,
                title="Population by Generation",
                hole=0.4,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("\U0001f4ca Key Demographic Insights")
        total = s['total_records']
        col1, col2, col3 = st.columns(3)
        col1.metric("Voting Age (18+)", f"{s['voting_age']:,}", f"{s['voting_age']/total*100:.1f}%")
        col2.metric("Youth (<30)", f"{s['youth']:,}", f"{s['youth']/total*100:.1f}%")
        col3.metric("Seniors (65+)", f"{s['seniors']:,}", f"{s['seniors']/total*100:.1f}%")

    # ── Tab 2: Names Analysis ────────────────────────────────────────
    with tab2:
        st.header("Names Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("\U0001f3c6 Top 20 Most Common Names")
            top_names = s['name_counts'].head(20)
            fig = px.bar(
                x=top_names.values, y=top_names.index, orientation='h',
                title="Most Common First Names",
                labels={'x': 'Count', 'y': 'Name'},
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("\U0001f3c6 Top 20 Most Common Surnames")
            top_surnames = s['surname_counts'].head(20)
            fig = px.bar(
                x=top_surnames.values, y=top_surnames.index, orientation='h',
                title="Most Common Surnames",
                labels={'x': 'Count', 'y': 'Surname'},
                color_discrete_sequence=['#ff7f0e'],
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        # Name trends over time
        st.subheader("\U0001f4c8 Name Popularity Over Time")
        st.markdown("Most popular names by birth decade")

        names_by_decade = s['names_by_decade']
        if len(names_by_decade) > 0:
            decades = sorted(set(
                idx[0] for idx in names_by_decade.index
                if pd.notna(idx[0]) and idx[0] >= 1940
            ))
            if decades:
                all_trending = set()
                decade_data = {}
                for decade in decades:
                    try:
                        top = names_by_decade.loc[decade]
                        decade_data[int(decade)] = top
                        all_trending.update(top.index.tolist())
                    except KeyError:
                        pass

                selected = st.multiselect(
                    "Select names to track across decades",
                    options=sorted(all_trending),
                    default=sorted(all_trending)[:5],
                )

                if selected:
                    trend_rows = []
                    for decade in decades:
                        if int(decade) in decade_data:
                            top = decade_data[int(decade)]
                            for name in selected:
                                trend_rows.append({
                                    'Decade': int(decade),
                                    'Name': name,
                                    'Count': top.get(name, 0),
                                })
                    fig = px.line(
                        pd.DataFrame(trend_rows),
                        x='Decade', y='Count', color='Name',
                        title="Name Popularity by Decade",
                        markers=True,
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

        # Name length by year
        st.subheader("\U0001f4cf Average & Median Name Length by Year")
        nl = s['name_length_by_year']
        sl = s['surname_length_by_year']

        col1, col2 = st.columns(2)

        with col1:
            if len(nl) > 0:
                nl_filtered = nl[nl.index >= 1920]
                fig = px.line(
                    x=nl_filtered.index,
                    y=[nl_filtered['mean'], nl_filtered['median']],
                    title="First Name Length Over Time",
                    labels={'x': 'Birth Year', 'value': 'Characters'},
                )
                fig.data[0].name = 'Average'
                fig.data[1].name = 'Median'
                fig.update_layout(height=350, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if len(sl) > 0:
                sl_filtered = sl[sl.index >= 1920]
                fig = px.line(
                    x=sl_filtered.index,
                    y=[sl_filtered['mean'], sl_filtered['median']],
                    title="Surname Length Over Time",
                    labels={'x': 'Birth Year', 'value': 'Characters'},
                    color_discrete_sequence=['#ff7f0e', '#d62728'],
                )
                fig.data[0].name = 'Average'
                fig.data[1].name = 'Median'
                fig.update_layout(height=350, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

        # Name ending patterns
        st.subheader("\U0001f524 Name Ending Patterns")
        st.markdown(
            "Armenian names often follow specific patterns. "
            "Analyzing endings reveals traditional vs. modern naming trends."
        )

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                x=s['name_endings'].head(15).index,
                y=s['name_endings'].head(15).values,
                title="Most Common Name Endings (last 2 letters)",
                labels={'x': 'Ending', 'y': 'Count'},
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                x=s['surname_endings'].head(15).index,
                y=s['surname_endings'].head(15).values,
                title="Most Common Surname Endings (last 3 letters)",
                labels={'x': 'Ending', 'y': 'Count'},
                color_discrete_sequence=['#2ca02c'],
            )
            st.plotly_chart(fig, use_container_width=True)

        # Concentration
        st.subheader("\U0001f4ca Name Concentration Statistics")
        top10n = s['name_counts'].head(10).sum() / s['total_records'] * 100
        top10s = s['surname_counts'].head(10).sum() / s['total_records'] * 100

        col1, col2, col3 = st.columns(3)
        col1.metric("Top 10 Names Cover", f"{top10n:.1f}% of population")
        col2.metric("Top 10 Surnames Cover", f"{top10s:.1f}% of population")
        col3.metric(
            "Most Common Name",
            f"{s['name_counts'].index[0]} ({s['name_counts'].iloc[0]:,})",
        )

        st.subheader("\U0001f464 Most Common Full Name Combinations")
        common_df = pd.DataFrame({
            'Full Name': s['common_full_names'].head(15).index,
            'Count': s['common_full_names'].head(15).values,
        })
        st.dataframe(common_df, hide_index=True, use_container_width=True)

    # ── Tab 3: Geographic ────────────────────────────────────────────
    with tab3:
        st.header("Geographic Distribution")

        # Map
        st.subheader("\U0001f5fa\ufe0f Regional Map")
        map_df = s['map_data']

        if len(map_df) > 0:
            fig = px.scatter_mapbox(
                map_df,
                lat='lat', lon='lon',
                size='population', color='avg_age',
                hover_name='region',
                hover_data={'population': ':,', 'avg_age': ':.1f', 'lat': False, 'lon': False},
                color_continuous_scale='RdYlBu_r',
                size_max=40, zoom=6.5,
                center={'lat': 40.15, 'lon': 44.50},
                mapbox_style='open-street-map',
                title="Population by Region (bubble = population, color = avg age)",
            )
            fig.update_layout(height=500, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Could not match region names to coordinates for the map.")

        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(
                names=s['region_counts'].index,
                values=s['region_counts'].values,
                title="Population by Region",
                hole=0.3,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                x=s['region_counts'].values, y=s['region_counts'].index,
                orientation='h',
                title="Population by Region (Bar Chart)",
                labels={'x': 'Population', 'y': 'Region'},
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("\U0001f4ca Average Age by Region")
        fig = px.bar(
            x=s['regional_avg_age'].index, y=s['regional_avg_age'].values,
            title="Average Age by Region",
            labels={'x': 'Region', 'y': 'Average Age'},
            color=s['regional_avg_age'].values,
            color_continuous_scale='RdYlBu_r',
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("\U0001f3a8 Name Diversity by Region")
        fig = px.bar(
            x=s['name_diversity_by_region'].index,
            y=s['name_diversity_by_region'].values,
            title="Unique Names per Region",
            labels={'x': 'Region', 'y': 'Number of Unique Names'},
            color=s['name_diversity_by_region'].values,
            color_continuous_scale='Greens',
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("\U0001f3d8\ufe0f Largest Communities")
        top_comm = s['community_counts'].head(20)
        fig = px.bar(
            x=top_comm.values, y=top_comm.index, orientation='h',
            title="Top 20 Communities by Population",
            labels={'x': 'Population', 'y': 'Community'},
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab 4: Temporal Patterns ─────────────────────────────────────
    with tab4:
        st.header("Temporal Patterns")

        exclude_jan1 = st.checkbox(
            "Exclude January 1st birthdays (likely registration artifacts)",
            value=False,
        )

        if exclude_jan1:
            birth_years = s['birth_year_counts_no_jan1']
            birth_months = s['birth_month_counts_no_jan1']
            birth_days = s['birth_day_counts_no_jan1']
            st.info(f"Excluding {s['jan1_excluded_count']:,} January 1st records")
        else:
            birth_years = s['birth_year_counts']
            birth_months = s['birth_month_counts']
            birth_days = s['birth_day_counts']

        birth_years = birth_years[birth_years.index >= 1920]

        st.subheader("\U0001f4c8 Birth Year Distribution")
        fig = px.line(
            x=birth_years.index, y=birth_years.values,
            title="Number of People by Birth Year",
            labels={'x': 'Birth Year', 'y': 'Count'},
        )
        fig.add_vline(x=1991, line_dash="dash", line_color="red",
                      annotation_text="Independence (1991)")
        fig.add_vline(x=1988, line_dash="dash", line_color="orange",
                      annotation_text="Earthquake (1988)")
        st.plotly_chart(fig, use_container_width=True)

        st.info(
            f"\U0001f4cc Peak birth year: **{int(s['peak_birth_year'])}** "
            f"with **{s['peak_birth_count']:,}** births"
        )

        col1, col2 = st.columns(2)
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        with col1:
            fig = px.bar(
                x=month_names,
                y=[birth_months.get(i, 0) for i in range(1, 13)],
                title="Births by Month",
                labels={'x': 'Month', 'y': 'Count'},
                color=[birth_months.get(i, 0) for i in range(1, 13)],
                color_continuous_scale='Blues',
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                x=birth_days.index, y=birth_days.values,
                title="Births by Day of Month",
                labels={'x': 'Day', 'y': 'Count'},
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("\U0001f4dc Historical Context")
        st.markdown("""
        Notable events that may have affected birth patterns:
        - **1988**: Devastating earthquake in Spitak region
        - **1991**: Armenian independence from USSR
        - **1992-1994**: Nagorno-Karabakh War
        - **2020**: Second Karabakh War
        """)

        st.subheader("\U0001f4ca Birth Trends by Decade")
        decades = {}
        for year, count in s['birth_year_counts'].items():
            if pd.notna(year) and year >= 1920:
                decade = int(year // 10 * 10)
                decades[decade] = decades.get(decade, 0) + count
        decades_s = pd.Series(decades).sort_index()
        fig = px.bar(
            x=decades_s.index.astype(str) + 's', y=decades_s.values,
            title="Total Births by Decade",
            labels={'x': 'Decade', 'y': 'Count'},
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab: Birthdays ─────────────────────────────────────────────
    with tab_bday:
        st.header("\U0001f382 Birthday Analysis")

        # Key metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Most Common Birthday", s['most_common_birthday'],
                     f"{s['most_common_birthday_count']:,} people")
        col2.metric("Least Common Birthday", s['least_common_birthday'],
                     f"{s['least_common_birthday_count']:,} people")
        col3.metric("Jan 1st Birthdays", f"{s['jan1_births']:,}",
                     f"{s['jan1_pct']:.1f}% of total")

        # Daily distribution across the year
        st.subheader("\U0001f4c5 Birthdays by Day of Year")
        doy = s['birthday_doy_counts']
        if len(doy) > 0:
            fig = px.bar(
                x=doy.index, y=doy.values,
                title="Number of People Born on Each Day of the Year",
                labels={'x': 'Day of Year (1 = Jan 1)', 'y': 'Count'},
            )
            fig.update_layout(height=350, bargap=0)
            st.plotly_chart(fig, use_container_width=True)

        # Heatmap: month x day
        st.subheader("\U0001f5d3\ufe0f Birthday Heatmap (Month x Day)")
        mmdd = s['birthday_mmdd_counts']
        if len(mmdd) > 0:
            import numpy as np
            heatmap_data = np.zeros((12, 31))
            for md, count in mmdd.items():
                try:
                    m, d = int(md[:2]), int(md[3:])
                    heatmap_data[m - 1][d - 1] = count
                except (ValueError, IndexError):
                    pass

            month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            import plotly.graph_objects as go
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=list(range(1, 32)),
                y=month_labels,
                colorscale='YlOrRd',
                hovertemplate='Month: %{y}<br>Day: %{x}<br>Count: %{z:,}<extra></extra>',
            ))
            fig.update_layout(
                title="Birthday Frequency by Month and Day",
                xaxis_title="Day of Month",
                yaxis_title="",
                height=400,
                yaxis=dict(autorange='reversed'),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Birth weekday distribution
        st.subheader("\U0001f4c6 Births by Day of Week")
        wd = s['birth_weekday_counts']
        if len(wd) > 0:
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                         'Friday', 'Saturday', 'Sunday']
            wd_sorted = wd.reindex(day_order).fillna(0).astype(int)
            fig = px.bar(
                x=wd_sorted.index, y=wd_sorted.values,
                title="Births by Day of Week (based on actual birth dates)",
                labels={'x': 'Day', 'y': 'Count'},
                color=wd_sorted.values,
                color_continuous_scale='Blues',
            )
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Conception month estimate 😉
        st.subheader("\U0001f609 Estimated Conception Month (birthday \u2212 9 months)")
        cm = s['conception_month_counts']
        if len(cm) > 0:
            month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            fig = px.bar(
                x=month_labels,
                y=[cm.get(i, 0) for i in range(1, 13)],
                title="When were people most likely conceived? \U0001f609",
                labels={'x': 'Estimated Conception Month', 'y': 'Count'},
                color=[cm.get(i, 0) for i in range(1, 13)],
                color_continuous_scale='RdPu',
            )
            fig.update_layout(height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            peak_month = cm.idxmax()
            st.info(
                f"\U0001f609 Peak conception month: **{month_labels[int(peak_month) - 1]}** "
                f"({cm[peak_month]:,} estimated conceptions)"
            )

        # Feb 29 special
        feb29 = mmdd.get('02-29', 0)
        if feb29 > 0:
            st.subheader("\U0001f4a0 Leap Day Babies")
            st.metric("Born on February 29th", f"{feb29:,}")
            st.caption("These people only get a 'real' birthday every 4 years!")

    # ── Tab 5: Fun Insights ──────────────────────────────────────────
    with tab5:
        st.header("\U0001f52e Fun Insights")

        st.subheader("\u2648 Zodiac Sign Distribution")
        fig = px.pie(
            names=s['zodiac_counts'].index, values=s['zodiac_counts'].values,
            title="Population by Zodiac Sign", hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.success(f"**Most common:** {s['zodiac_counts'].index[0]} ({s['zodiac_counts'].iloc[0]:,})")
        col2.info(f"**Least common:** {s['zodiac_counts'].index[-1]} ({s['zodiac_counts'].iloc[-1]:,})")

        st.subheader("\U0001f382 Interesting Birthday Facts")
        expected_pct = 100 / 365
        col1, col2, col3 = st.columns(3)
        col1.metric("January 1st Birthdays", f"{s['jan1_births']:,}",
                     f"{s['jan1_pct'] - expected_pct:+.2f}% vs expected")
        col2.metric("Most Common Birth Day", f"{int(s['birth_day_counts'].idxmax())}")
        col3.metric("Most Common Birth Month",
                     month_names[int(s['birth_month_counts'].idxmax()) - 1])

        st.subheader("\U0001f468 Patronymic Analysis (Father's Names)")
        top_pat = s['patronymic_counts'].head(15)
        fig = px.bar(
            x=top_pat.index, y=top_pat.values,
            title="Most Common Patronymics",
            labels={'x': 'Patronymic', 'y': 'Count'},
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab 6: Household Analysis ────────────────────────────────────
    with tab6:
        st.header("\U0001f3e0 Household Analysis")

        st.subheader("\U0001f4ca Estimated Household Sizes")
        col1, col2, col3 = st.columns(3)
        col1.metric("Average Household Size", f"{s['avg_household_size']:.2f}")
        col2.metric("Largest Household", f"{s['max_household_size']} people")
        single = s['household_size_dist'].get(1, 0)
        col3.metric("Single-Person Registrations", f"{single:,}")

        hh = s['household_size_dist'].head(15)
        fig = px.bar(
            x=hh.index, y=hh.values,
            title="Distribution of Household Sizes",
            labels={'x': 'People per Address', 'y': 'Number of Addresses'},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("\U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466 Family Structure Estimates")
        col1, col2 = st.columns(2)
        col1.metric("Estimated Nuclear Families", f"{s['unique_families']:,}",
                     help="Unique surname + patronymic combinations")
        col2.metric("Average Family Size", f"{s['avg_family_size']:.2f}")

        fig = px.bar(
            x=s['family_size_dist'].index, y=s['family_size_dist'].values,
            title="Family Sizes (same surname + patronymic)",
            labels={'x': 'People per Family', 'y': 'Number of Families'},
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab: Records & Superlatives ──────────────────────────────────
    with tab_records:
        st.header("\U0001f3c6 Records & Superlatives")

        # Oldest / Youngest
        st.subheader("\U0001f9d3 Age Records")
        col1, col2 = st.columns(2)
        oldest = s.get('oldest_person', {})
        youngest = s.get('youngest_person', {})

        with col1:
            st.markdown("#### Oldest Person")
            if oldest:
                st.metric("Age", f"{oldest['age']} years")
                st.markdown(
                    f"**{oldest['name']} {oldest['surname']}**  \n"
                    f"Patronymic: {oldest['patronymic']}  \n"
                    f"Born: {oldest['birth_date']}  \n"
                    f"Region: {oldest['region']}"
                )

        with col2:
            st.markdown("#### Youngest Person")
            if youngest:
                st.metric("Age", f"{youngest['age']} years")
                st.markdown(
                    f"**{youngest['name']} {youngest['surname']}**  \n"
                    f"Patronymic: {youngest['patronymic']}  \n"
                    f"Born: {youngest['birth_date']}  \n"
                    f"Region: {youngest['region']}"
                )

        st.divider()

        # Longest / Shortest Names
        st.subheader("\U0001f524 Name Length Records")
        col1, col2 = st.columns(2)

        with col1:
            ln = s.get('longest_name', {})
            if ln:
                st.markdown("#### Longest First Name")
                st.metric("Length", f"{ln['length']} characters")
                st.markdown(
                    f"**{ln['name']}** {ln['surname']}  \n"
                    f"Age: {ln['age']} | Region: {ln['region']}"
                )

            ls = s.get('longest_surname', {})
            if ls:
                st.markdown("#### Longest Surname")
                st.metric("Length", f"{ls['length']} characters")
                st.markdown(
                    f"{ls['name']} **{ls['surname']}**  \n"
                    f"Age: {ls['age']} | Region: {ls['region']}"
                )

        with col2:
            sn = s.get('shortest_name', {})
            if sn:
                st.markdown("#### Shortest First Name")
                st.metric("Length", f"{sn['length']} characters")
                st.markdown(
                    f"**{sn['name']}** {sn['surname']}  \n"
                    f"Age: {sn['age']} | Region: {sn['region']}"
                )

            ss = s.get('shortest_surname', {})
            if ss:
                st.markdown("#### Shortest Surname")
                st.metric("Length", f"{ss['length']} characters")
                st.markdown(
                    f"{ss['name']} **{ss['surname']}**  \n"
                    f"Age: {ss['age']} | Region: {ss['region']}"
                )

        lfn = s.get('longest_full_name', {})
        if lfn:
            st.markdown("#### Longest Full Name (First + Last)")
            st.metric("Total Length", f"{lfn['length']} characters")
            st.markdown(
                f"**{lfn['name']} {lfn['surname']}**  \n"
                f"Age: {lfn['age']} | Region: {lfn['region']}"
            )

        st.divider()

        # Most / Least Popular Names
        st.subheader("\U0001f4ca Popularity Records")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Most Popular")
            st.metric("Most Common Name",
                      s.get('most_popular_name', ''),
                      f"{s.get('most_popular_name_count', 0):,} people")
            st.metric("Most Common Surname",
                      s.get('most_popular_surname', ''),
                      f"{s.get('most_popular_surname_count', 0):,} people")
            st.metric("Most Common Full Name",
                      s.get('most_common_full_name_value', ''),
                      f"{s.get('most_common_full_name_count', 0):,} people")

        with col2:
            st.markdown("#### Rarest")
            st.metric("Names Appearing Only Once",
                      f"{s.get('unique_names_count', 0):,}")
            st.metric("Surnames Appearing Only Once",
                      f"{s.get('unique_surnames_count', 0):,}")

        st.divider()

        # Regions
        st.subheader("\U0001f5fa\ufe0f Regional Records")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Largest Region")
            st.metric(s.get('largest_region', ''),
                      f"{s.get('largest_region_count', 0):,} people")

        with col2:
            st.markdown("#### Smallest Region")
            st.metric(s.get('smallest_region', ''),
                      f"{s.get('smallest_region_count', 0):,} people")

        st.divider()

        # Largest Household
        st.subheader("\U0001f3e0 Largest Household")
        lh = s.get('largest_household', {})
        if lh:
            st.metric("Household Size", f"{lh['size']} people")
            st.markdown(
                f"**Address:** {lh['address']}  \n"
                f"**Community:** {lh['community']}  \n"
                f"**Region:** {lh['region']}"
            )
            st.markdown("**Members:**")
            members = lh.get('members')
            if members is not None and len(members) > 0:
                st.dataframe(members, hide_index=True, use_container_width=True)

        st.divider()

        # Largest Family
        st.subheader("\U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466 Largest Family")
        lf = s.get('largest_family', {})
        if lf:
            st.metric("Family Size", f"{lf['size']} people")
            st.markdown(
                f"**Surname:** {lf['surname']}  \n"
                f"**Patronymic:** {lf['patronymic']}"
            )

    # ── Tab 7: Data Quality ──────────────────────────────────────────
    with tab7:
        st.header("\U0001f50d Data Quality Report")

        missing_df = s['missing_data']
        full_cols = int((missing_df['Completeness %'] == 100).sum())

        col1, col2, col3 = st.columns(3)
        col1.metric("Fully Complete Columns", f"{full_cols} / {len(missing_df)}")
        col2.metric("Average Completeness", f"{missing_df['Completeness %'].mean():.2f}%")
        col3.metric("Total Missing Values", f"{int(missing_df['Total Missing'].sum()):,}")

        fig = px.bar(
            missing_df.sort_values('Completeness %'),
            x='Completeness %', y='Column', orientation='h',
            title="Data Completeness by Column",
            color='Completeness %', color_continuous_scale='RdYlGn',
            range_color=[0, 100],
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detailed Breakdown")
        st.dataframe(
            missing_df,
            use_container_width=True, hide_index=True,
        )

        st.subheader("\u26a0\ufe0f Potential Anomalies")
        expected = s['total_records'] / 365
        jan1_ratio = s['jan1_births'] / expected if expected > 0 else 0
        anomalies = []
        if jan1_ratio > 2:
            anomalies.append(
                f"**January 1st birthdays**: {s['jan1_births']:,} records "
                f"({jan1_ratio:.1f}x expected). Common when exact date was unknown."
            )
        if s['age_outliers'] > 0:
            anomalies.append(
                f"**Age outliers**: {s['age_outliers']:,} records with age < 0 or > 120."
            )
        if anomalies:
            for a in anomalies:
                st.warning(a)
        else:
            st.success("No major anomalies detected")

    # ── Summary ──────────────────────────────────────────────────────
    st.divider()
    st.header("\U0001f4dd Key Findings Summary")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        ### Demographics
        - **Total registered voters:** {s['total_records']:,}
        - **Average age:** {s['avg_age']:.1f} years
        - **Peak birth year:** {int(s['peak_birth_year'])}

        ### Geographic
        - **Largest region:** {s['region_counts'].index[0]} ({s['region_counts'].iloc[0]:,})
        - **Communities:** {s['unique_communities']:,}
        - **Region with oldest population:** {s['regional_avg_age'].index[0]}
        """)

    with col2:
        st.markdown(f"""
        ### Names
        - **Most common name:** {s['name_counts'].index[0]} ({s['name_counts'].iloc[0]:,})
        - **Most common surname:** {s['surname_counts'].index[0]} ({s['surname_counts'].iloc[0]:,})
        - **Unique names:** {s['unique_names']:,}
        - **Unique surnames:** {s['unique_surnames']:,}

        ### Fun Facts
        - **Most common zodiac:** {s['zodiac_counts'].index[0]}
        - **Average household size:** {s['avg_household_size']:.2f}
        - **January 1st birthdays:** {s['jan1_births']:,} ({s['jan1_pct']:.1f}%)
        """)


if __name__ == "__main__":
    main()
