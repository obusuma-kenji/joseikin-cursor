from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Literal, Tuple

from dateutil.relativedelta import relativedelta

from .models import CaseInput


ResultLevel = Literal["OK", "WARN", "NG"]


@dataclass(frozen=True)
class CheckItem:
    id: str
    title: str
    level: ResultLevel
    detail: str


@dataclass(frozen=True)
class Evaluation:
    eligible: bool
    summary: str
    checks: List[CheckItem]
    missing_documents: List[str]
    ng_warnings: List[str]


def _between(d: date, start: date, end: date) -> bool:
    return start <= d <= end


def _is_within_two_months(payment_date: date, submit_date: date) -> Tuple[bool, date]:
    # 「翌日から起算して2か月以内」→ payment_date+1 から 2か月後の前日まで
    start = payment_date + timedelta(days=1)
    end = start + relativedelta(months=2) - timedelta(days=1)
    return (start <= submit_date <= end), end


def evaluate_case(case: CaseInput) -> Evaluation:
    checks: List[CheckItem] = []
    missing: List[str] = []
    warnings: List[str] = []

    c = case.company
    w = case.worker
    wage = case.wage
    dl = case.deadline

    # ①対象企業か（rules.mdの順序に従う）
    in_plan = _between(w.conversion_date, c.career_up_plan_start, c.career_up_plan_end)
    checks.append(
        CheckItem(
            id="company.plan_period",
            title="キャリアアップ計画期間内の転換",
            level="OK" if in_plan else "NG",
            detail=f"転換日={w.conversion_date} / 計画期間={c.career_up_plan_start}〜{c.career_up_plan_end}",
        )
    )
    if not in_plan:
        warnings.append("転換日がキャリアアップ計画期間外だと原則対象外（Q&A: 計画期間外の転換は対象外）。")
        missing.append("キャリアアップ計画（計画期間・受理控え等）")

    if not c.conversion_rule_exists:
        checks.append(
            CheckItem(
                id="company.conversion_rule",
                title="正社員転換制度の規定（就業規則等）",
                level="NG",
                detail="転換制度の規定が確認できません。",
            )
        )
        warnings.append("転換制度の規定がない場合、支給対象外になりやすい。")
        missing.append("就業規則等（転換制度の規定が確認できるもの）")
    else:
        checks.append(
            CheckItem(
                id="company.conversion_rule",
                title="正社員転換制度の規定（就業規則等）",
                level="OK",
                detail="転換制度の規定あり。",
            )
        )
        if not c.conversion_rule_has_objective_procedure:
            checks.append(
                CheckItem(
                    id="company.conversion_objective",
                    title="手続き・要件・実施時期の客観性",
                    level="NG",
                    detail="手続き/要件/実施時期が客観的に確認できる形で規定されていない可能性。",
                )
            )
            warnings.append("転換要件の例外運用や曖昧規定はNGになりやすい（要件の客観性）。")
        else:
            checks.append(
                CheckItem(
                    id="company.conversion_objective",
                    title="手続き・要件・実施時期の客観性",
                    level="OK",
                    detail="客観的に確認可能な転換制度として入力されています。",
                )
            )

    regular_ok = c.regular_rule_has_bonus_or_retirement and c.regular_rule_has_raise
    checks.append(
        CheckItem(
            id="company.regular_definition",
            title="正社員定義（賞与/退職金 + 昇給）",
            level="OK" if regular_ok else "NG",
            detail="正社員に賞与/退職金と昇給が適用される規定が必要。",
        )
    )
    if not regular_ok:
        warnings.append("正社員の定義要件（賞与/退職金 + 昇給）が不十分だと不支給リスク。")
        missing.append("就業規則等（正社員の賞与/退職金・昇給の規定が分かる箇所）")

    if not c.nonregular_rule_has_wage_diff:
        checks.append(
            CheckItem(
                id="company.nonregular_wage_diff",
                title="非正規の賃金差（額または計算方法の差）",
                level="NG",
                detail="正社員と異なる賃金の額/計算方法が就業規則等で確認できない前提。",
            )
        )
        warnings.append("就業規則等で正規・非正規の区分と賃金差が確認できないと対象外になりやすい。")
        missing.append("就業規則等（非正規雇用区分の適用範囲・賃金規定）")
    else:
        checks.append(
            CheckItem(
                id="company.nonregular_wage_diff",
                title="非正規の賃金差（額または計算方法の差）",
                level="OK",
                detail="正社員と異なる賃金の額/計算方法の差がある前提。",
            )
        )

    if not c.work_rules_not_edited:
        checks.append(
            CheckItem(
                id="company.documents_original",
                title="添付書類（原本/複写）前提",
                level="WARN",
                detail="加工・転記物は不正受給認定リスクになり得るため注意。",
            )
        )
        warnings.append("添付書類の加工・転記は不正受給リスク（原本/複写提出が原則）。")

    # ②対象労働者か
    if w.is_foreign_trainee_or_specified_skill1:
        checks.append(
            CheckItem(
                id="worker.foreign_excluded",
                title="外国人（技能実習/特定技能1号等）",
                level="NG",
                detail="正社員化コースでは対象外となる類型がある。",
            )
        )
        warnings.append("外国人技能実習生・特定技能1号などは対象外になり得る。")
    else:
        checks.append(
            CheckItem(
                id="worker.foreign_excluded",
                title="外国人（除外類型の確認）",
                level="OK",
                detail="除外類型には該当しない前提。",
            )
        )

    if w.is_new_graduate and (w.months_since_graduation_at_hire is not None) and (w.months_since_graduation_at_hire < 12):
        checks.append(
            CheckItem(
                id="worker.new_graduate_1y",
                title="新規学卒者（雇入れから1年未満）",
                level="NG",
                detail="新規学卒者で雇入れから1年未満は支給対象外になり得る。",
            )
        )
        warnings.append("新規学卒者で雇入れから1年未満は対象外になり得る（Q&A）。")
    else:
        checks.append(
            CheckItem(
                id="worker.new_graduate_1y",
                title="新規学卒者（1年要件）",
                level="OK",
                detail="入力範囲では対象外要件に該当しない前提。",
            )
        )

    if w.is_over_retirement_age_at_conversion:
        checks.append(
            CheckItem(
                id="worker.retirement_age",
                title="定年超の正社員転換",
                level="NG",
                detail="定年年齢超の正社員転換は対象外になり得る。",
            )
        )
        warnings.append("定年年齢超の正社員転換は対象外になり得る。")
    else:
        checks.append(
            CheckItem(
                id="worker.retirement_age",
                title="定年要件",
                level="OK",
                detail="定年要件はクリアしている前提。",
            )
        )

    if w.has_probation_after_conversion:
        checks.append(
            CheckItem(
                id="worker.probation",
                title="転換後の試用期間",
                level="WARN",
                detail="試用期間があると取扱いが変わり得る（無期→正規扱い等）。",
            )
        )
        warnings.append("転換後に試用期間を設けると正社員とみなされない期間が生じ、申請計算もズレる。")
    else:
        checks.append(
            CheckItem(
                id="worker.probation",
                title="転換後の試用期間",
                level="OK",
                detail="試用期間なしの前提。",
            )
        )

    if w.employment_before != "派遣" and w.tenure_months_before_conversion < 6:
        checks.append(
            CheckItem(
                id="worker.tenure_6m",
                title="転換前の雇用期間（6か月）",
                level="NG",
                detail=f"転換前の雇用期間が6か月未満（入力={w.tenure_months_before_conversion}か月）。",
            )
        )
        warnings.append("有期雇用等の適用を6か月以上受けていないと対象外になり得る。")
    else:
        checks.append(
            CheckItem(
                id="worker.tenure_6m",
                title="転換前の雇用期間（6か月）",
                level="OK",
                detail="入力上は要件を満たす前提。",
            )
        )

    if not w.social_insurance_applied_after_conversion:
        checks.append(
            CheckItem(
                id="worker.social_insurance",
                title="転換後の社会保険",
                level="WARN",
                detail="適用事業所では原則、加入が必要。",
            )
        )
        warnings.append("適用事業所の場合、転換後に社会保険加入がないと対象外リスク。")
        missing.append("社会保険の加入が分かる資料（適用事業所の場合）")
    else:
        checks.append(
            CheckItem(
                id="worker.social_insurance",
                title="転換後の社会保険",
                level="OK",
                detail="加入ありの前提。",
            )
        )

    # ③対象経費か → 本ツールでは「賃金3%」中心
    wage_ok = wage.increase_percent >= 3.0
    checks.append(
        CheckItem(
            id="wage.3percent",
            title="賃金3%以上の増額",
            level="OK" if wage_ok else "NG",
            detail=f"増額率={wage.increase_percent:.2f}%（3.00%以上が必要。四捨五入不可）",
        )
    )
    if not wage_ok:
        warnings.append("賃金増額が2.99%などの場合は要件未達（四捨五入不可）。")
        missing.append("転換前後6か月の賃金台帳・給与明細（算定根拠）")

    # ④提出期限内か
    within, deadline_end = _is_within_two_months(dl.six_month_wage_payment_date, dl.application_submit_date)
    checks.append(
        CheckItem(
            id="deadline.within_2m",
            title="支給申請期間（2か月以内）",
            level="OK" if within else "NG",
            detail=f"6か月賃金支払日={dl.six_month_wage_payment_date} / 提出予定日={dl.application_submit_date} / 期限（目安）={deadline_end}",
        )
    )
    if not within:
        warnings.append("申請期間外は不受理になり得る（到着日基準にも注意）。")

    # 不足資料の最小セット（状況に応じて加算）
    base_docs = [
        "支給申請書（所定様式）",
        "就業規則等（正社員定義・非正規区分・転換制度・賃金規定）",
        "雇用契約書/労働条件通知書（転換前・転換後）",
        "賃金台帳・給与明細（転換前6か月・転換後6か月）",
        "キャリアアップ計画（受理控え等）",
    ]
    for d in base_docs:
        if d not in missing:
            missing.append(d)

    # eligible: NGが1つでもあればfalse（WARNは許容）
    eligible = all(ci.level != "NG" for ci in checks)
    summary = "申請できる可能性が高い（入力上の要件は概ね充足）" if eligible else "申請不可/要件未達の可能性（入力上でNGあり）"

    # 取り回しのため重複排除（順序維持）
    def dedupe(xs: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in xs:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    return Evaluation(
        eligible=eligible,
        summary=summary,
        checks=checks,
        missing_documents=dedupe(missing),
        ng_warnings=dedupe(warnings),
    )

