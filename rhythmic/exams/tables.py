from exams.models import ExamComponent
from scoring.types import BandRow, GradeBand, MarkingTable


def build_marking_table(component: ExamComponent) -> MarkingTable:
    difference_steps = tuple(component.difference_steps)
    rows = tuple(
        BandRow(expert_minimum=row.expert_minimum, percentages=tuple(row.percentages))
        for row in component.marking_rows.all()
    )
    return MarkingTable(difference_steps=difference_steps, rows=rows)


def build_grade_bands(component: ExamComponent) -> list[GradeBand]:
    return [
        GradeBand(name=row.name, minimum=row.minimum)
        for row in component.grade_bands.all()
    ]
