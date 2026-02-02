from collections import defaultdict


def build_year_over_year(kpi_rows: list[dict]) -> dict[str, dict[int, float]]:
    matrix: dict[str, dict[int, float]] = defaultdict(dict)
    for row in kpi_rows:
        matrix[row["kpi_id"]][int(row["year"])] = float(row["value"])
    return dict(matrix)
