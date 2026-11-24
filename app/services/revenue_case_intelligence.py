"""Read-only consolidated operational dashboard for revenue cases.

Dates are compared to a caller-supplied ISO date. Limitation dates are displayed as
manually entered review data only; the service never calculates legal limitation.
"""
from datetime import date

def _today(value=None):
    if value is None:return date.today().isoformat()
    if isinstance(value,date):return value.isoformat()
    return str(value)

def case_dashboard_rows(conn,today=None):
    today=_today(today)
    rows=conn.execute("""
      SELECT c.*,
       (SELECT COUNT(*) FROM revenue_case_parties p WHERE p.case_id=c.case_id) AS party_count,
       (SELECT COUNT(*) FROM revenue_case_evidence e WHERE e.case_id=c.case_id) AS evidence_count,
       (SELECT COUNT(*) FROM revenue_case_evidence e WHERE e.case_id=c.case_id AND lower(e.verification_status) NOT IN ('verified','legally_reviewed','copy_compared')) AS evidence_review_count,
       (SELECT COUNT(*) FROM revenue_case_issues i WHERE i.case_id=c.case_id AND lower(i.status) NOT IN ('closed','resolved')) AS open_case_issues,
       (SELECT COUNT(*) FROM legal_research_bundles b WHERE b.case_id=c.case_id) AS research_bundle_count,
       (SELECT COUNT(*) FROM legal_research_issues ri JOIN legal_research_bundles b USING(bundle_id) WHERE b.case_id=c.case_id AND lower(ri.issue_status) NOT IN ('closed','resolved')) AS open_research_issues,
       (SELECT COUNT(*) FROM revenue_case_drafts d WHERE d.case_id=c.case_id AND lower(d.status) NOT IN ('filed','finalised','finalized','archived')) AS working_drafts,
       (SELECT COUNT(*) FROM revenue_proceeding_plans pp WHERE pp.case_id=c.case_id AND lower(pp.status) NOT IN ('closed','completed','archived')) AS active_proceedings,
       (SELECT COUNT(*) FROM revenue_proceeding_steps ps JOIN revenue_proceeding_plans pp USING(proceeding_id)
          WHERE pp.case_id=c.case_id AND lower(ps.step_status) NOT IN ('completed','done','not applicable','n/a')) AS outstanding_steps,
       (SELECT COUNT(*) FROM revenue_proceeding_events pe JOIN revenue_proceeding_plans pp USING(proceeding_id)
          WHERE pp.case_id=c.case_id AND pe.deadline_date<>'' AND pe.deadline_date IS NOT NULL AND pe.deadline_date < ? AND lower(pe.status) NOT IN ('closed','completed','done','cancelled')) AS past_recorded_deadlines,
       (SELECT COUNT(*) FROM revenue_proceeding_events pe JOIN revenue_proceeding_plans pp USING(proceeding_id)
          WHERE pp.case_id=c.case_id AND pe.deadline_date>=? AND lower(pe.status) NOT IN ('closed','completed','done','cancelled')) AS future_recorded_deadlines
      FROM revenue_cases c ORDER BY
       CASE WHEN c.next_hearing_date IS NULL OR c.next_hearing_date='' THEN 1 ELSE 0 END,
       c.next_hearing_date,c.updated_at DESC,c.case_id DESC
    """,(today,today)).fetchall()
    return rows

def upcoming_hearings(conn,today=None,limit=200):
    today=_today(today)
    return conn.execute("""SELECT case_id,case_title,case_number,authority,next_hearing_date,status
      FROM revenue_cases WHERE next_hearing_date IS NOT NULL AND next_hearing_date<>'' AND next_hearing_date>=?
      ORDER BY next_hearing_date,case_title LIMIT ?""",(today,limit)).fetchall()

def recorded_deadlines(conn,today=None,limit=300):
    today=_today(today)
    return conn.execute("""SELECT pe.event_id,pp.proceeding_id,pp.case_id,c.case_title,pp.proceeding_type,
      pp.forum_name,pe.event_date,pe.event_type,pe.title,pe.deadline_date,pe.next_action,pe.source_reference,pe.status
      FROM revenue_proceeding_events pe JOIN revenue_proceeding_plans pp USING(proceeding_id)
      JOIN revenue_cases c USING(case_id)
      WHERE pe.deadline_date IS NOT NULL AND pe.deadline_date<>''
      ORDER BY CASE WHEN pe.deadline_date<? AND lower(pe.status) NOT IN ('closed','completed','done','cancelled') THEN 0 ELSE 1 END,
      pe.deadline_date,c.case_title LIMIT ?""",(today,limit)).fetchall()

def outstanding_steps(conn,limit=300):
    return conn.execute("""SELECT ps.step_id,pp.proceeding_id,pp.case_id,c.case_title,pp.proceeding_type,
      ps.step_title,ps.description,ps.step_status,ps.target_date,ps.responsible_person,
      ps.source_reference,ps.verification_status
      FROM revenue_proceeding_steps ps JOIN revenue_proceeding_plans pp USING(proceeding_id)
      JOIN revenue_cases c USING(case_id)
      WHERE lower(ps.step_status) NOT IN ('completed','done','not applicable','n/a')
        AND lower(pp.status) NOT IN ('closed','completed','archived')
      ORDER BY CASE WHEN ps.target_date IS NULL OR ps.target_date='' THEN 1 ELSE 0 END,
      ps.target_date,c.case_title LIMIT ?""",(limit,)).fetchall()

def manually_recorded_limitation_reviews(conn,today=None,limit=200):
    today=_today(today)
    return conn.execute("""SELECT pp.proceeding_id,pp.case_id,c.case_title,pp.proceeding_type,pp.forum_name,
      pp.limitation_start_date,pp.limitation_period_note,pp.limitation_source_reference,
      pp.limitation_reviewed_by,pp.limitation_reviewed_date,pp.limitation_due_date,pp.limitation_caveat
      FROM revenue_proceeding_plans pp JOIN revenue_cases c USING(case_id)
      WHERE pp.limitation_due_date IS NOT NULL AND pp.limitation_due_date<>''
      ORDER BY pp.limitation_due_date,c.case_title LIMIT ?""",(limit,)).fetchall()

def dashboard_summary(conn,today=None):
    today=_today(today);cases=case_dashboard_rows(conn,today)
    deadlines=recorded_deadlines(conn,today)
    steps=outstanding_steps(conn)
    return {
      "total_cases":len(cases),
      "active_cases":sum(1 for r in cases if str(r["status"]).lower() not in ("decided","closed","completed","archived","disposed")),
      "upcoming_hearings":len(upcoming_hearings(conn,today)),
      "open_research_issues":sum(r["open_research_issues"] for r in cases),
      "working_drafts":sum(r["working_drafts"] for r in cases),
      "outstanding_steps":len(steps),
      "past_recorded_deadlines":sum(1 for r in deadlines if r["deadline_date"]<today and str(r["status"]).lower() not in ("closed","completed","done","cancelled")),
      "unreviewed_evidence":sum(r["evidence_review_count"] for r in cases),
      "cases":cases
    }
