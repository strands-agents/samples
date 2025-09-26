from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import langsmith as ls
import pandas as pd
import plotly.express as px
from collections import Counter

c = ls.Client()
print("Fetching projects...")
with ThreadPoolExecutor() as executor:
    experiments = list(
        executor.map(
            lambda p: c.read_project(project_id=p.id, include_stats=True),
            c.list_projects(
                reference_dataset_id="d5fb1fd5-387e-48fe-8e17-e132a018fbee"
            ),
        )
    )
error_rates = [e.error_rate for e in experiments]
print(f"Error Rates: {Counter(e.error_rate for e in experiments)}")
print(f"Run Counts: {Counter(e.run_count for e in experiments)}")
filtered = [
    e
    for e in experiments
    # Only include experiments that have completed 100 runs (or a multiple of 100, in cases where we do repetitions)
    if e.metadata["end_index"] == 100
    and ((e.run_count + 1) % 100 == 1)
    and e.error_rate < 0.1
]
print(f"Filtered {len(filtered)} experiments out of {len(experiments)}")
print(f"FilteredRun Counts: {Counter(e.run_count for e in filtered)}")


def get_score(exp):
    return exp.feedback_stats["reward"]["avg"]


def get_key(exp):
    met = exp.metadata
    return (met["agent_strategy"], met["n_distractors"])


d = defaultdict(list)
for e in filtered:
    score = get_score(e)
    d[get_key(e)].append(score)

# Couldn't scale
d[("single", 8)] = [0]
data = {k: d[k] for k in sorted(d)}

tool_count_map = {0: 16, 1: 26, 2: 44, 4: 82, 6: 120, 8: 157}


def generate_fig(data, score_title: str = "Score"):
    # Dataframe
    df = pd.DataFrame(
        [
            {"Architecture": arch, "Num Distractors": n, score_title: score}
            for (arch, n), scores in data.items()
            for score in scores
        ]
    )
    df["Tool Count"] = df["Num Distractors"].map(tool_count_map)

    fig = px.line(
        df,
        x="Num Distractors",
        y=score_title,
        color="Architecture",
        markers=True,
        hover_data=["Tool Count", "Architecture", "Num Distractors", score_title],
        title="Multi-agent scaling performance",
        labels={
            "Num Distractors": "Number of Distractors Domains",
            score_title: score_title,
        },
    )

    fig.update_traces(marker=dict(size=10))
    fig.update_layout(
        template="simple_white",
        legend_title="Architecture",
        title_font_size=20,
        hoverlabel=dict(bgcolor="white", font_size=12),
        autosize=False,
        width=800,
        height=500,
    )

    fig.show()
    return fig


cost_data = defaultdict(list)
failed = []
for e in filtered:
    score = e.total_tokens
    cost_data[get_key(e)].append(score)
cost_data.pop(("single", 8), None)
cost_data = {k: cost_data[k][:1] for k in sorted(cost_data)}

fig_performance = generate_fig(data)
fig_performance.write_image("performance_scaling.png")

fig_cost = generate_fig(cost_data, "Cost (Tokens)")
fig_cost.write_image("token_cost_scaling.png")

print("Figures saved as 'performance_scaling.png' and 'token_cost_scaling.png'")
