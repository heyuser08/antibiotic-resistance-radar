from __future__ import annotations

import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
	page_title="Antibiotic Resistance Radar",
	page_icon="🧫",
	layout="wide",
)

st.markdown(
	"""
	<style>
	@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
	html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
	h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0; }
	.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1440px; }
	.eyebrow { color: #237a68; font-size: .75rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
	.subtitle { color: #5c6b67; font-size: 1rem; margin-top: -.45rem; }
	div[data-testid="stMetric"] { background: #f1f6f3; border-left: 3px solid #237a68; padding: 1rem 1.1rem; }
	div[data-testid="stMetricLabel"] { color: #52635d; }
	.stTabs [data-baseweb="tab-list"] { gap: 1.4rem; }
	</style>
	""",
	unsafe_allow_html=True,
)


DEMO_DATA = pd.DataFrame(
	[
		("E. coli", "Ciprofloxacin", "Resistant"),
		("E. coli", "Ceftriaxone", "Susceptible"),
		("E. coli", "Gentamicin", "Resistant"),
		("E. coli", "Meropenem", "Susceptible"),
		("K. pneumoniae", "Ciprofloxacin", "Resistant"),
		("K. pneumoniae", "Ceftriaxone", "Resistant"),
		("K. pneumoniae", "Gentamicin", "Susceptible"),
		("K. pneumoniae", "Meropenem", "Susceptible"),
		("S. aureus", "Ciprofloxacin", "Susceptible"),
		("S. aureus", "Ceftriaxone", "Susceptible"),
		("S. aureus", "Gentamicin", "Resistant"),
		("S. aureus", "Meropenem", "Resistant"),
	],
	columns=["Organism", "Antibiotic", "Result"],
)

RESISTANT_TERMS = {"r", "resistant", "resistance", "non susceptible", "nonsusceptible"}
SUSCEPTIBLE_TERMS = {"s", "susceptible", "sensitive"}
INTERMEDIATE_TERMS = {"i", "intermediate", "indeterminate", "unknown", "na", "n/a", ""}


def normalized(value: object) -> str:
	return re.sub(r"[_-]+", " ", str(value).strip().lower())


def suggested_column(columns: list[str], terms: tuple[str, ...]) -> str:
	for column in columns:
		name = normalized(column)
		if any(term in name for term in terms):
			return column
	return columns[0]


def classify_result(value: object, numeric_threshold: float) -> bool | None:
	if pd.isna(value):
		return None
	text = normalized(value)
	if text in RESISTANT_TERMS:
		return True
	if text in SUSCEPTIBLE_TERMS:
		return False
	if text in INTERMEDIATE_TERMS:
		return None
	try:
		number = float(text.rstrip("%"))
	except ValueError:
		return None
	if number in (0, 1):
		return bool(number)
	return number >= numeric_threshold


def make_long_data(
	data: pd.DataFrame,
	layout: str,
	organism_column: str,
	antibiotic_column: str | None,
	result_column: str | None,
	antibiotics: list[str],
	numeric_threshold: float,
) -> pd.DataFrame:
	if layout == "Long format":
		tidy = data[[organism_column, antibiotic_column, result_column]].copy()
		tidy.columns = ["Organism", "Antibiotic", "Result"]
	else:
		tidy = data.melt(
			id_vars=[organism_column],
			value_vars=antibiotics,
			var_name="Antibiotic",
			value_name="Result",
		).rename(columns={organism_column: "Organism"})
	tidy["Resistant"] = tidy["Result"].map(
		lambda value: classify_result(value, numeric_threshold)
	)
	tidy = tidy.dropna(subset=["Organism", "Antibiotic", "Resistant"])
	tidy["Organism"] = tidy["Organism"].astype(str)
	tidy["Antibiotic"] = tidy["Antibiotic"].astype(str)
	tidy["Resistant"] = tidy["Resistant"].astype(bool)
	return tidy


def draw_radar(summary: pd.DataFrame, organisms: list[str]) -> go.Figure:
	figure = go.Figure()
	colors = ["#237a68", "#d56a45", "#4677a8", "#9b6b9f", "#b59037"]
	for index, organism in enumerate(organisms):
		values = summary.loc[organism].tolist()
		antibiotics = summary.columns.tolist()
		figure.add_trace(
			go.Scatterpolar(
				r=values + values[:1],
				theta=antibiotics + antibiotics[:1],
				name=organism,
				fill="toself",
				opacity=0.68,
				line={"color": colors[index % len(colors)], "width": 2.5},
				hovertemplate="%{theta}: %{r:.1f}%<extra>%{fullData.name}</extra>",
			)
		)
	figure.update_layout(
		polar={
			"radialaxis": {"visible": True, "range": [0, 100], "ticksuffix": "%", "gridcolor": "#dce6e0"},
			"angularaxis": {"gridcolor": "#dce6e0"},
			"bgcolor": "#fbfcfa",
		},
		paper_bgcolor="rgba(0,0,0,0)",
		font={"family": "DM Sans, sans-serif", "color": "#253b34"},
		legend={"orientation": "h", "y": -0.16},
		margin={"l": 35, "r": 35, "t": 25, "b": 45},
		height=510,
	)
	return figure


st.markdown('<p class="eyebrow">Surveillance workspace</p>', unsafe_allow_html=True)
st.title("Antibiotic Resistance Radar")
st.markdown(
	'<p class="subtitle">Compare resistance patterns across organisms and antibiotics.</p>',
	unsafe_allow_html=True,
)

with st.sidebar:
	st.header("Dataset")
	uploaded_file = st.file_uploader("Upload a CSV", type=["csv"])
	st.caption("Expected: organism, antibiotic, and susceptibility result columns, or one antibiotic column per test.")

if uploaded_file is not None:
	try:
		raw_data = pd.read_csv(uploaded_file)
	except Exception as error:
		st.error(f"Could not read this CSV: {error}")
		st.stop()
	source_label = uploaded_file.name
else:
	raw_data = DEMO_DATA.copy()
	source_label = "Interactive demo data"

if raw_data.empty or len(raw_data.columns) < 2:
	st.error("The CSV needs at least two columns and one data row.")
	st.stop()

columns = raw_data.columns.tolist()
long_guess = (
	any("antibiotic" in normalized(column) or "drug" in normalized(column) for column in columns)
	and any(any(term in normalized(column) for term in ("result", "resistan", "suscept", "phenotype")) for column in columns)
)

with st.sidebar:
	layout = st.radio("Data layout", ["Long format", "Wide format"], index=0 if long_guess else 1)
	organism_column = st.selectbox(
		"Organism column",
		columns,
		index=columns.index(suggested_column(columns, ("organism", "bacteria", "species", "pathogen"))),
	)
	if layout == "Long format":
		antibiotic_column = st.selectbox(
			"Antibiotic column",
			columns,
			index=columns.index(suggested_column(columns, ("antibiotic", "drug", "agent"))),
		)
		result_column = st.selectbox(
			"Result column",
			columns,
			index=columns.index(suggested_column(columns, ("result", "resistan", "suscept", "phenotype"))),
		)
		antibiotic_columns: list[str] = []
	else:
		antibiotic_columns = [column for column in columns if column != organism_column]
		antibiotic_columns = st.multiselect("Antibiotic columns", antibiotic_columns, default=antibiotic_columns)
		antibiotic_column = None
		result_column = None
	numeric_threshold = st.slider(
		"Numeric resistance threshold (%)",
		min_value=1,
		max_value=100,
		value=50,
		help="For numeric results other than 0/1, values at or above this threshold count as resistant.",
	)

if layout == "Wide format" and not antibiotic_columns:
	st.warning("Select at least one antibiotic column to build the radar.")
	st.stop()

tidy_data = make_long_data(
	raw_data,
	layout,
	organism_column,
	antibiotic_column,
	result_column,
	antibiotic_columns,
	numeric_threshold,
)

if tidy_data.empty:
	st.warning("No recognizable resistance results were found. Check the selected columns and result values.")
	st.stop()

available_organisms = sorted(tidy_data["Organism"].unique().tolist())
with st.sidebar:
	selected_organisms = st.multiselect(
		"Organisms to compare",
		available_organisms,
		default=available_organisms[: min(3, len(available_organisms))],
	)

if not selected_organisms:
	st.info("Choose at least one organism in the sidebar to view its resistance profile.")
	st.stop()

filtered = tidy_data[tidy_data["Organism"].isin(selected_organisms)]
summary = (
	filtered.groupby(["Organism", "Antibiotic"])["Resistant"]
	.mean()
	.mul(100)
	.unstack(fill_value=0)
	.reindex(selected_organisms)
)
summary = summary.dropna(axis=1, how="all")

total_tests = len(filtered)
overall_rate = filtered["Resistant"].mean() * 100
organism_count = filtered["Organism"].nunique()
antibiotic_count = filtered["Antibiotic"].nunique()

metric_columns = st.columns(4)
metric_columns[0].metric("Organisms", f"{organism_count:,}")
metric_columns[1].metric("Antibiotics", f"{antibiotic_count:,}")
metric_columns[2].metric("Test results", f"{total_tests:,}")
metric_columns[3].metric("Overall resistance", f"{overall_rate:.1f}%")
st.caption(f"Source: {source_label} · Intermediate, unknown, and unrecognized results are excluded from rate calculations.")

radar_tab, table_tab, data_tab = st.tabs(["Resistance radar", "Rate table", "Dataset"])
with radar_tab:
	st.subheader("Resistance profile")
	st.plotly_chart(draw_radar(summary, selected_organisms), use_container_width=True)
	st.caption("Each axis shows the percentage of recorded tests classified as resistant. Hover for exact rates.")

with table_tab:
	rate_table = summary.rename_axis("Organism").reset_index()
	st.dataframe(
		rate_table,
		use_container_width=True,
		hide_index=True,
		column_config={
			column: st.column_config.NumberColumn(column, format="%.1f%%")
			for column in summary.columns
		},
	)
	st.download_button(
		"Download resistance rates",
		data=rate_table.to_csv(index=False).encode("utf-8"),
		file_name="antibiotic_resistance_rates.csv",
		mime="text/csv",
	)

with data_tab:
	st.subheader("Results included in analysis")
	st.dataframe(filtered, use_container_width=True, hide_index=True)
