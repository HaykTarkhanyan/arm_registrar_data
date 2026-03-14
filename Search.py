"""
Armenian Voter Registry - Search Application
Main search interface with person detail cards and per-name analytics.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

from data import load_data
from filters import filter_data
from utils import (
    is_valid_armenian,
    get_zodiac_sign,
    get_generation,
    calculate_days_until_birthday,
    calculate_rarity_percentile,
)

st.set_page_config(
    page_title="Search - Armenian Voter Registry",
    page_icon="\U0001f50d",
    layout="wide",
)


def _get_app_password() -> str | None:
    """Get app password from Streamlit secrets, .env, or environment."""
    try:
        return st.secrets["APP_PASSWORD"]
    except Exception:
        pass
    pw = os.environ.get("APP_PASSWORD")
    if not pw:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("APP_PASSWORD="):
                    pw = line.split("=", 1)[1].strip()
                    break
    return pw


def check_authenticated() -> bool:
    """Check if user has entered the correct password."""
    return st.session_state.get("authenticated", False)


# === Data Loading ===
@st.cache_data
def load_cached_data():
    return load_data()


@st.cache_data
def get_unique_regions(_df):
    return sorted(_df['region'].dropna().unique())


@st.cache_data
def compute_global_stats(_df):
    birth_years = pd.to_numeric(_df['birth_date'].str[-4:], errors='coerce')
    return {
        'name_counts': _df['name'].value_counts(),
        'surname_counts': _df['surname'].value_counts(),
        'total_count': len(_df),
        'region_counts': _df['region'].value_counts(),
        'birth_year_counts': birth_years.dropna().astype(int).value_counts().sort_index(),
    }


# === Per-Name Analytics (cached by name string) ===
@st.cache_data
def compute_name_analytics(name_value):
    """Distribution stats for a specific first name."""
    df = load_cached_data()
    subset = df[df['name'] == name_value]
    if len(subset) == 0:
        return None
    region_dist = subset['region'].value_counts().head(10)
    birth_years = pd.to_numeric(subset['birth_date'].str[-4:], errors='coerce')
    year_dist = birth_years.dropna().astype(int).value_counts().sort_index()
    return {
        'count': len(subset),
        'region_dist': region_dist,
        'year_dist': year_dist,
        'avg_age': float(subset['age'].mean()),
    }


@st.cache_data
def compute_surname_analytics(surname_value):
    """Distribution stats for a specific surname."""
    df = load_cached_data()
    subset = df[df['surname'] == surname_value]
    if len(subset) == 0:
        return None
    region_dist = subset['region'].value_counts().head(10)
    birth_years = pd.to_numeric(subset['birth_date'].str[-4:], errors='coerce')
    year_dist = birth_years.dropna().astype(int).value_counts().sort_index()
    top_names = subset['name'].value_counts().head(10)
    top_patronymics = subset['patronymic'].value_counts().head(5)
    return {
        'count': len(subset),
        'region_dist': region_dist,
        'year_dist': year_dist,
        'top_names': top_names,
        'top_patronymics': top_patronymics,
    }


# === Relationship Finders ===
def find_household_members(df, person):
    return df[
        (df['address'] == person['address'])
        & (df['region'] == person['region'])
        & (df['community'] == person['community'])
        & (df.index != person.name)
    ]


def find_possible_siblings(df, person):
    """Find possible siblings: same surname + patronymic, within 15 years."""
    return df[
        (df['surname'] == person['surname'])
        & (df['patronymic'] == person['patronymic'])
        & (df.index != person.name)
        & (abs(df['age'] - person['age']) <= 15)
    ].sort_values('age')


# === Display Components ===
def display_person_card(person, df, global_stats, expanded=False, card_idx=0):
    pid = f"{card_idx}_{person.name}"
    authenticated = check_authenticated()

    with st.expander(
        f"**{person['name']} {person['surname']}** \u2014 "
        f"{person['age']} years, {person['region']}",
        expanded=expanded,
    ):
        card_tab1, card_tab2 = st.tabs([
            "\U0001f4cb Overview",
            "\U0001f4ca Name & Surname Analytics",
        ])

        # ── Tab 1: Overview ──────────────────────────────────────
        with card_tab1:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("##### \U0001f464 Personal Info")
                st.write(f"**Name:** {person['name']}")
                st.write(f"**Surname:** {person['surname']}")
                if authenticated:
                    st.write(f"**Patronymic:** {person['patronymic']}")
                    st.write(f"**Birth Date:** {person['birth_date']}")
                st.write(f"**Age:** {person['age']}")

                sign, symbol = get_zodiac_sign(person['birth_date'])
                st.write(f"**Zodiac:** {symbol} {sign}")

                try:
                    birth_year = int(person['birth_date'][-4:])
                    st.write(f"**Generation:** {get_generation(birth_year)}")
                except (ValueError, IndexError):
                    pass

            with col2:
                st.markdown("##### \U0001f4cd Location")
                st.write(f"**Region:** {person['region']}")
                if authenticated:
                    st.write(f"**Community:** {person['community']}")
                    st.write(f"**Residence:** {person['residence']}")
                    st.write(f"**Address:** {person['address']}")
                    st.write(f"**Precinct:** {person['precinct']}")
                    st.write(f"**Polling Station:** {person['polling_station']}")
                else:
                    st.caption("Detailed location requires password")

            with col3:
                st.markdown("##### \U0001f4ca Statistics")

                days, is_today = calculate_days_until_birthday(person['birth_date'])
                if is_today:
                    st.success("\U0001f382 **Birthday is TODAY!**")
                elif days > 0:
                    st.info(f"\U0001f382 **{days}** days until birthday")

                name_rarity = calculate_rarity_percentile(
                    person['name'], global_stats['name_counts']
                )
                surname_rarity = calculate_rarity_percentile(
                    person['surname'], global_stats['surname_counts']
                )
                st.write(f"**Name rarity:** Top {name_rarity:.1f}%")
                st.write(f"**Surname rarity:** Top {surname_rarity:.1f}%")

                name_count = global_stats['name_counts'].get(person['name'], 0)
                surname_count = global_stats['surname_counts'].get(person['surname'], 0)
                st.write(f"**People with same name:** {name_count:,}")
                st.write(f"**People with same surname:** {surname_count:,}")

            # Sensitive sections — only shown when authenticated
            if authenticated:
                # Household members
                st.markdown("---")
                household = find_household_members(df, person)

                if len(household) > 0:
                    st.markdown(f"##### \U0001f3e0 Household Members ({len(household)})")
                    hh_display = household[
                        ['name', 'surname', 'patronymic', 'age', 'birth_date']
                    ].sort_values('age', ascending=False)
                    st.dataframe(hh_display, use_container_width=True, hide_index=True)

                    ages = [person['age']] + household['age'].tolist()
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Household Size", len(ages))
                    col_b.metric("Age Range", f"{min(ages)} - {max(ages)}")
                    col_c.metric("Average Age", f"{np.mean(ages):.0f}")
                else:
                    st.info("\U0001f3e0 No other household members found at this address")

                # Possible siblings
                siblings = find_possible_siblings(df, person)
                if len(siblings) > 0:
                    st.markdown(
                        f"##### \U0001f468\u200d\U0001f469\u200d\U0001f467\u200d\U0001f466 "
                        f"Possible Siblings ({len(siblings)})"
                    )
                    st.dataframe(
                        siblings[['name', 'surname', 'patronymic', 'age', 'birth_date', 'region', 'address']],
                        use_container_width=True, hide_index=True,
                    )

        # ── Tab 2: Name & Surname Analytics ──────────────────────
        with card_tab2:
            col_n, col_s = st.columns(2)

            with col_n:
                st.markdown(f"##### Name: {person['name']}")
                ns = compute_name_analytics(person['name'])
                if ns:
                    st.write(f"**{ns['count']:,}** people share this name")
                    st.write(f"**Average age:** {ns['avg_age']:.1f}")

                    if len(ns['region_dist']) > 0:
                        fig = px.bar(
                            x=ns['region_dist'].values,
                            y=ns['region_dist'].index,
                            orientation='h',
                            title="Distribution by Region",
                            labels={'x': 'Count', 'y': ''},
                            height=250,
                        )
                        fig.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            margin=dict(l=0, r=10, t=30, b=0),
                        )
                        st.plotly_chart(fig, use_container_width=True, key=f"name_region_{pid}")

                    if len(ns['year_dist']) > 1:
                        fig = px.line(
                            x=ns['year_dist'].index,
                            y=ns['year_dist'].values,
                            title="Births per Year with This Name",
                            labels={'x': 'Birth Year', 'y': 'Count'},
                            height=220,
                        )
                        fig.update_layout(margin=dict(l=0, r=10, t=30, b=0))
                        st.plotly_chart(fig, use_container_width=True, key=f"name_year_{pid}")

            with col_s:
                st.markdown(f"##### Surname: {person['surname']}")
                ss = compute_surname_analytics(person['surname'])
                if ss:
                    st.write(f"**{ss['count']:,}** people share this surname")

                    if len(ss['region_dist']) > 0:
                        fig = px.bar(
                            x=ss['region_dist'].values,
                            y=ss['region_dist'].index,
                            orientation='h',
                            title="Distribution by Region",
                            labels={'x': 'Count', 'y': ''},
                            height=250,
                            color_discrete_sequence=['#ff7f0e'],
                        )
                        fig.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            margin=dict(l=0, r=10, t=30, b=0),
                        )
                        st.plotly_chart(fig, use_container_width=True, key=f"surname_region_{pid}")

                    if len(ss['year_dist']) > 1:
                        fig = px.line(
                            x=ss['year_dist'].index,
                            y=ss['year_dist'].values,
                            title="Births per Year with This Surname",
                            labels={'x': 'Birth Year', 'y': 'Count'},
                            height=220,
                        )
                        fig.update_layout(margin=dict(l=0, r=10, t=30, b=0))
                        st.plotly_chart(fig, use_container_width=True, key=f"surname_year_{pid}")

                    if len(ss['top_names']) > 0:
                        st.markdown("**Most common first names:**")
                        for nm, cnt in ss['top_names'].head(5).items():
                            st.write(f"- {nm}: {cnt:,}")

                    if len(ss['top_patronymics']) > 0:
                        st.markdown("**Most common patronymics:**")
                        for pat, cnt in ss['top_patronymics'].head(5).items():
                            st.write(f"- {pat}: {cnt:,}")


def display_results_overview(results, global_stats):
    if len(results) < 2:
        return

    st.markdown("### \U0001f4c8 Results Overview")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            results, x='age', nbins=30,
            title="Age Distribution",
            color_discrete_sequence=['#1f77b4'],
        )
        fig.update_layout(
            xaxis_title="Age", yaxis_title="Count", showlegend=False, height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        region_counts = results['region'].value_counts().head(10)
        fig = px.bar(
            x=region_counts.values, y=region_counts.index,
            orientation='h', title="Top Regions",
            color_discrete_sequence=['#2ca02c'],
        )
        fig.update_layout(
            xaxis_title="Count", yaxis_title="", showlegend=False, height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

    if len(results) > 5:
        results_with_year = results.copy()
        results_with_year['birth_year'] = pd.to_numeric(
            results_with_year['birth_date'].str[-4:], errors='coerce'
        )
        year_counts = (
            results_with_year['birth_year']
            .dropna().astype(int).value_counts().sort_index()
        )
        if len(year_counts) > 1:
            fig = px.line(
                x=year_counts.index, y=year_counts.values,
                title="Birth Year Trend", markers=True,
            )
            fig.update_layout(
                xaxis_title="Birth Year", yaxis_title="Count", height=250,
            )
            st.plotly_chart(fig, use_container_width=True)


# === Main Application ===
def main():
    st.title("\U0001f50d Search")
    st.caption("Search the Armenian voter registry database")

    try:
        df = load_cached_data()
        regions = get_unique_regions(df)
        global_stats = compute_global_stats(df)
    except FileNotFoundError:
        st.error("Data file not found. Run `python preprocess.py` first.")
        return

    # Sidebar
    with st.sidebar:
        st.markdown("### \U0001f512 Access")
        if not check_authenticated():
            entered_pw = st.text_input(
                "Password (for detailed info)",
                type="password",
                placeholder="Enter password",
            )
            if entered_pw:
                correct_pw = _get_app_password()
                if entered_pw == correct_pw:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
            st.caption("Without password: name, surname, age, region only")
        else:
            st.success("Full access enabled")
            if st.button("Lock", use_container_width=True):
                st.session_state["authenticated"] = False
                st.rerun()

        st.markdown("---")
        st.markdown("### \U0001f4ca Database Stats")
        st.metric("Total Records", f"{len(df):,}")
        st.metric("Unique Names", f"{df['name'].nunique():,}")
        st.metric("Unique Surnames", f"{df['surname'].nunique():,}")
        st.metric("Regions", f"{df['region'].nunique()}")
        st.metric("Age Range", f"{df['age'].min()} - {df['age'].max()}")

        st.markdown("---")
        st.markdown("### \u2699\ufe0f Search Settings")
        match_mode = st.radio(
            "Match mode",
            options=["exact", "partial"],
            format_func=lambda x: "Exact match"
            if x == "exact"
            else "Partial match (contains)",
            help="Exact: name must match exactly. Partial: substring search.",
        )

        st.markdown("---")
        st.markdown("### \U0001f4a1 Search Tips")
        st.markdown(
            """
        - Names must be in **Armenian** script
        - Leave fields empty to skip them
        - Use **partial** mode for flexible search
        - Use age range for approximate ages
        """
        )

    # Search form
    st.markdown("### Search Filters")

    with st.form("search_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            name = st.text_input("Name", placeholder="Armenian name")
            surname = st.text_input("Surname", placeholder="Armenian surname")
            patronymic = st.text_input("Patronymic", placeholder="Father's name")

        with col2:
            region = st.selectbox("Region (Marz)", options=[""] + regions)
            community = st.text_input("Community", placeholder="Community name")

        with col3:
            age_col1, age_col2 = st.columns(2)
            with age_col1:
                age_min = st.number_input(
                    "Min Age", min_value=0, max_value=120, value=0, step=1,
                )
            with age_col2:
                age_max = st.number_input(
                    "Max Age", min_value=0, max_value=120, value=120, step=1,
                )

        submitted = st.form_submit_button(
            "\U0001f50d Search", use_container_width=True, type="primary",
        )

    if submitted:
        # Validation
        errors = []
        if name and not is_valid_armenian(name):
            errors.append("Name must contain only Armenian characters")
        if surname and not is_valid_armenian(surname):
            errors.append("Surname must contain only Armenian characters")
        if patronymic and not is_valid_armenian(patronymic):
            errors.append("Patronymic must contain only Armenian characters")

        if errors:
            for e in errors:
                st.error(f"\u26a0\ufe0f {e}")
            return

        f_name = name.strip() if name else None
        f_surname = surname.strip() if surname else None
        f_patronymic = patronymic.strip() if patronymic else None
        f_region = region if region else None
        f_community = community.strip() if community else None
        f_age_min = age_min if age_min > 0 else None
        f_age_max = age_max if age_max < 120 else None

        if not any([f_name, f_surname, f_patronymic, f_region, f_community, f_age_min, f_age_max]):
            st.warning("Please specify at least one search criterion")
            return

        results = filter_data(
            df,
            name=f_name, surname=f_surname, patronymic=f_patronymic,
            region=f_region, community=f_community,
            age_min=f_age_min, age_max=f_age_max,
            match_mode=match_mode,
        )

        st.markdown("---")
        st.markdown(f"### \U0001f4cb Results: **{len(results):,}** matches")

        if len(results) == 0:
            st.info("No results found. Try adjusting your search criteria.")
        elif len(results) > 1000:
            st.warning(
                f"Too many results ({len(results):,}). Please narrow your search."
            )
            display_results_overview(
                results.sample(min(1000, len(results))), global_stats,
            )
            st.markdown("#### Random Sample (10 records)")
            for i, (_, person) in enumerate(results.sample(10).iterrows()):
                display_person_card(person, df, global_stats, card_idx=i)
        else:
            if len(results) > 5:
                display_results_overview(results, global_stats)
            st.markdown("---")
            for i, (_, person) in enumerate(results.iterrows()):
                display_person_card(
                    person, df, global_stats,
                    expanded=(i == 0 and len(results) <= 5),
                    card_idx=i,
                )


if __name__ == "__main__":
    main()
