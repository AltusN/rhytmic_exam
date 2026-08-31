from decimal import Decimal

import pytest

from exams.models import (
    Exam,
    ExamComponent,
    ExamKind,
    GradeBandRow,
    MarkingScheme,
    MarkingTableRow,
)
from exams.tables import build_grade_bands, build_marking_table
from scoring.aggregate import grade


@pytest.mark.django_db
def test_legacy_single_row_scheme_builds():
    exam = Exam.objects.create(
        level=1,
        kind=ExamKind.PRACTICAL,
        year=2026,
    )
    component = ExamComponent.objects.create(
        exam=exam,
        name="Legacy Single Row Scheme",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DA",
        difference_steps=[
            Decimal("0.00"),
            Decimal("0.10"),
            Decimal("0.20"),
        ],
    )
    MarkingTableRow.objects.create(
        component=component,
        expert_minimum=Decimal("0.00"),
        percentages=[
            Decimal("100"),
            Decimal("90"),
            Decimal("80"),
        ],
    )

    component.refresh_from_db()

    marking_table = build_marking_table(component)

    # The one stored row is selected because 0.30 >= 0.00.
    # The difference 0.05 lies in the first column, [0.00, 0.10),
    # whose stored percentage is 100. The row assertion also pins the
    # complete percentage sequence and its tuple representation.

    assert marking_table.lookup(
        expert=Decimal("0.30"), difference=Decimal("0.05")
    ) == Decimal("100")

    assert marking_table.rows[0].percentages == (
        Decimal("100"),
        Decimal("90"),
        Decimal("80"),
    )


@pytest.mark.django_db
def test_a_two_dimensional_table_builds():
    exam = Exam.objects.create(
        level=1,
        kind=ExamKind.PRACTICAL,
        year=2026,
    )
    component = ExamComponent.objects.create(
        exam=exam,
        name="Two Dimensional Table Scheme",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DA",
        difference_steps=[
            Decimal("0.00"),
            Decimal("0.10"),
            Decimal("0.20"),
        ],
    )
    # Insert descending bounds so the table only builds if queryset ordering sorts them.
    MarkingTableRow.objects.create(
        component=component,
        expert_minimum=Decimal("2.00"),
        percentages=[
            Decimal("100"),
            Decimal("95"),
            Decimal("85"),
        ],
    )
    MarkingTableRow.objects.create(
        component=component,
        expert_minimum=Decimal("0.00"),
        percentages=[
            Decimal("100"),
            Decimal("90"),
            Decimal("80"),
        ],
    )

    component.refresh_from_db()

    marking_table = build_marking_table(component)

    assert tuple(row.expert_minimum for row in marking_table.rows) == (
        Decimal("0.00"),
        Decimal("2.00"),
    )
    assert marking_table.rows[1].percentages == (
        Decimal("100"),
        Decimal("95"),
        Decimal("85"),
    )

    assert marking_table.lookup(
        expert=Decimal("2.50"),
        difference=Decimal("0.15"),
    ) == Decimal("95")


@pytest.mark.django_db
def test_a_row_with_wrong_number_of_percentages_raises():
    exam = Exam.objects.create(
        level=1,
        kind=ExamKind.PRACTICAL,
        year=2026,
    )
    component = ExamComponent.objects.create(
        exam=exam,
        name="Incorrect Percentages Row",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DA",
        difference_steps=[
            Decimal("0.00"),
            Decimal("0.10"),
            Decimal("0.20"),
        ],
    )
    MarkingTableRow.objects.create(
        component=component,
        expert_minimum=Decimal("0.00"),
        percentages=[
            Decimal("100"),
            Decimal("90"),
        ],
    )
    component.refresh_from_db()
    with pytest.raises(ValueError, match="percentages, but there are"):
        build_marking_table(component)


@pytest.mark.django_db
def test_difficulty_and_artistry_bands_differ():
    exam = Exam.objects.create(
        level=1,
        kind=ExamKind.PRACTICAL,
        year=2026,
    )
    component_db = ExamComponent.objects.create(
        exam=exam,
        name="Difficulty Body component",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DB",
        # The check constraint still requires non-empty difference_steps on a
        # NUMERIC component, even though this test never builds a marking table.
        difference_steps=[
            Decimal("0.00"),
            Decimal("0.10"),
            Decimal("0.20"),
        ],
    )
    GradeBandRow.objects.create(
        component=component_db, name="Excellent", minimum=Decimal("80.00")
    )
    GradeBandRow.objects.create(
        component=component_db, name="Pass", minimum=Decimal("50.00")
    )

    component_av = ExamComponent.objects.create(
        exam=exam,
        name="Artistic Value component",
        position=2,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="AV",
        difference_steps=[
            Decimal("0.00"),
            Decimal("0.10"),
            Decimal("0.20"),
        ],
    )
    GradeBandRow.objects.create(
        component=component_av, name="Excellent", minimum=Decimal("90.00")
    )
    GradeBandRow.objects.create(
        component=component_av, name="Pass", minimum=Decimal("50.00")
    )

    component_db.refresh_from_db()
    component_av.refresh_from_db()

    # 85 is the load-bearing number: above the 80 Difficulty floor, below the
    # 90 Artistry floor, the only region where the two band sets disagree.
    assert (
        grade(percentage=Decimal("85"), bands=build_grade_bands(component_db))
        == "Excellent"
    )
    assert (
        grade(percentage=Decimal("85"), bands=build_grade_bands(component_av)) == "Pass"
    )


@pytest.mark.django_db
def test_grade_bands_are_ordered_by_minimum():
    exam = Exam.objects.create(
        level=1,
        kind=ExamKind.PRACTICAL,
        year=2026,
    )
    component = ExamComponent.objects.create(
        exam=exam,
        name="Ordering Check Component",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DB",
        difference_steps=[
            Decimal("0.00"),
            Decimal("0.10"),
            Decimal("0.20"),
        ],
    )
    # Created descending so the test only passes if ordering sorts them.
    GradeBandRow.objects.create(
        component=component, name="Excellent", minimum=Decimal("80.00")
    )
    GradeBandRow.objects.create(
        component=component, name="Pass", minimum=Decimal("50.00")
    )

    component.refresh_from_db()

    assert [row.minimum for row in component.grade_bands.all()] == [
        Decimal("50.00"),
        Decimal("80.00"),
    ]
