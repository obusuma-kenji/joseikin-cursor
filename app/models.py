from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional

EmploymentType = Literal["有期", "無期", "派遣"]
EmploymentAfter = Literal["正社員", "多様な正社員"]


@dataclass(frozen=True)
class CompanyInput:
    company_name: str
    employee_count: int
    is_large_company: bool
    career_up_plan_start: date
    career_up_plan_end: date
    conversion_rule_exists: bool
    conversion_rule_has_objective_procedure: bool  # 手続き・要件・実施時期が明記
    regular_rule_has_bonus_or_retirement: bool
    regular_rule_has_raise: bool
    nonregular_rule_has_wage_diff: bool  # 正社員と賃金の額/計算方法が異なる規定が確認できる
    work_rules_not_edited: bool  # 原本/複写で提出できる前提


@dataclass(frozen=True)
class WorkerInput:
    worker_name: str
    hire_date: date
    conversion_date: date
    employment_before: EmploymentType
    employment_after: EmploymentAfter
    tenure_months_before_conversion: int
    is_new_graduate: bool
    months_since_graduation_at_hire: Optional[int]  # 新規学卒者判定の補助（不明ならNone）
    is_foreign_trainee_or_specified_skill1: bool
    has_probation_after_conversion: bool
    is_over_retirement_age_at_conversion: bool
    social_insurance_applied_after_conversion: bool


@dataclass(frozen=True)
class WageInput:
    # 3%増額判定用（簡易版）
    before_total_yen_6m: int
    after_total_yen_6m: int
    increase_percent: float  # 実計算結果（UI側で計算しても、CLIで直指定しても良い）


@dataclass(frozen=True)
class DeadlineInput:
    six_month_wage_payment_date: date  # 「6か月分の賃金を支給した日（実際）」の想定
    application_submit_date: date


@dataclass(frozen=True)
class CaseInput:
    company: CompanyInput
    worker: WorkerInput
    wage: WageInput
    deadline: DeadlineInput

