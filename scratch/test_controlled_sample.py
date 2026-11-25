import sys
import json
from pathlib import Path

# Setup paths
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.database.session import SessionLocal
from app.models.company import Company
from app.models.job import JobOpportunity
from app.services.discovery_service import DiscoveryService
from app.services.company_service import CompanyService


def run_controlled_verification():
    print("=== PHASE 6 CONTROLLED SAMPLE VERIFICATION ===\n")

    # Sample extracted directly from the authenticated Haveloc portal
    sample_listings = [
        {
            "company_name": "C-DOT(Centre for Development of Telematics)",
            "job_title": "Scientist 'B'",
            "salary_original": "22.4L",
            "salary_min_lpa": 22.4,
            "salary_max_lpa": 22.4,
            "stipend_original": None,
            "stipend_min": None,
            "stipend_max": None,
            "stipend_period": None,
            "job_type": "Full Time",
            "apply_before": "2026-11-05 00:00:00",
            "date_of_visit": "2026-11-16 00:00:00",
            "job_status": "Closed For Applications",
            "target_batch": None,
            "job_posted_date": "2026-10-30 16:26:01",
            "location": "Bangalore",
            "source_url": "https://placements.haveloc.com/jobs/details?jid=16316&juuid=52c26f7a-8d4c-4740-8824-5d3b1a4fc866&cId=2323&cuuid=c618923b-7337-4571-b6ab-1d7329bef6d0",
        },
        {
            "company_name": "Quest Global",
            "job_title": "Trainee Engineer",
            "salary_original": "4.5L – 6.5L",
            "salary_min_lpa": 4.5,
            "salary_max_lpa": 6.5,
            "stipend_original": None,
            "stipend_min": None,
            "stipend_max": None,
            "stipend_period": None,
            "job_type": "Full Time",
            "apply_before": "2026-11-05 00:00:00",
            "date_of_visit": "2026-11-17 00:00:00",
            "job_status": "Closed For Applications",
            "target_batch": None,
            "job_posted_date": "2026-11-04 12:34:53",
            "location": "PAN India",
            "source_url": "https://placements.haveloc.com/jobs/details?jid=16432&juuid=b6a773b3-b588-4842-b4bd-861153dcff52&cId=1939&cuuid=50c07163-e747-4c44-920d-f7b4bdd78af8",
        },
        {
            "company_name": "KPMG",
            "job_title": "Analyst 1",
            "salary_original": "5L",
            "salary_min_lpa": 5.0,
            "salary_max_lpa": 5.0,
            "stipend_original": "20K",
            "stipend_min": 20000.0,
            "stipend_max": 20000.0,
            "stipend_period": "Per Month",
            "job_type": "Intern + Full Time",
            "apply_before": "2026-11-05 00:00:00",
            "date_of_visit": "2026-11-18 00:00:00",
            "job_status": "Closed For Applications",
            "target_batch": None,
            "job_posted_date": "2026-11-04 16:25:02",
            "location": "PAN India",
            "source_url": "https://placements.haveloc.com/jobs/details?jid=16449&juuid=597329aa-940e-4245-8c55-ae1ae522da49&cId=3269&cuuid=bc806e82-c063-48e0-9971-57b25833f8b7",
        },
        {
            "company_name": "Docto Technologies",
            "job_title": "Software Engineer",
            "salary_original": "4.5L",
            "salary_min_lpa": 4.5,
            "salary_max_lpa": 4.5,
            "stipend_original": "10K – 18K",
            "stipend_min": 10000.0,
            "stipend_max": 18000.0,
            "stipend_period": "Per Month",
            "job_type": "Intern Leads to Full Time",
            "apply_before": "2026-11-05 00:00:00",
            "date_of_visit": "2026-11-10 00:00:00",
            "job_status": "Closed For Applications",
            "target_batch": None,
            "job_posted_date": "2026-11-05 09:20:40",
            "location": "Chennai",
            "source_url": "https://placements.haveloc.com/jobs/details?jid=16450&juuid=02620e05-a37f-4ae1-94fc-5545f4efe789&cId=10634&cuuid=cc674099-c7fe-4b4f-bd3a-e94a475a7389",
        },
        {
            "company_name": "Infocepts",
            "job_title": "Intern",
            "salary_original": "4.5L",
            "salary_min_lpa": 4.5,
            "salary_max_lpa": 4.5,
            "stipend_original": "20K",
            "stipend_min": 20000.0,
            "stipend_max": 20000.0,
            "stipend_period": "Per Month",
            "job_type": "Intern Leads to Full Time",
            "apply_before": "2026-11-04 00:00:00",
            "date_of_visit": "2026-11-19 00:00:00",
            "job_status": "Closed For Applications",
            "target_batch": None,
            "job_posted_date": "2026-11-03 14:16:13",
            "location": "Pan India",
            "source_url": "https://placements.haveloc.com/jobs/details?jid=16390&juuid=bc47c59f-d560-4bfb-a981-c24908109d03&cId=3683&cuuid=33b0b704-8a86-4003-8d99-67aec18a1078",
        },
        {
            "company_name": "ClearTax",
            "job_title": "Sales Development Representative",
            "salary_original": "6.4L – 8L",
            "salary_min_lpa": 6.4,
            "salary_max_lpa": 8.0,
            "stipend_original": "22K – 27K",
            "stipend_min": 22000.0,
            "stipend_max": 27000.0,
            "stipend_period": "Per Month",
            "job_type": "Intern Leads to Full Time",
            "apply_before": "2026-11-04 00:00:00",
            "date_of_visit": "2026-11-09 00:00:00",
            "job_status": "Closed For Applications",
            "target_batch": None,
            "job_posted_date": "2026-11-03 14:59:47",
            "location": "Bangalore",
            "source_url": "https://placements.haveloc.com/jobs/details?jid=16401&juuid=4e5d4794-7bc3-47e0-84c2-ea327435033e&cId=2209&cuuid=def12752-4cf5-4a50-8d0d-338a8a577119",
        },
        {
            "company_name": "Health & Glow Pvt. Ltd.",
            "job_title": "IT interns",
            "salary_original": None,  # Portal visibly has '—'
            "salary_min_lpa": None,
            "salary_max_lpa": None,
            "stipend_original": "5K – 10K",
            "stipend_min": 5000.0,
            "stipend_max": 10000.0,
            "stipend_period": "Per Month",
            "job_type": "Regular Intern",
            "apply_before": "2026-11-03 00:00:00",
            "date_of_visit": "2026-11-04 00:00:00",
            "job_status": "Closed For Applications",
            "target_batch": None,
            "job_posted_date": "2026-11-02 16:59:15",
            "location": "Bengaluru",
            "source_url": "https://placements.haveloc.com/jobs/details?jid=16365&juuid=fc955fab-8739-4314-be08-6a2d246518ad&cId=10596&cuuid=6a37d564-a637-4f7f-92d9-9fb59e15db99",
        }
    ]

    with SessionLocal() as db:
        print("--- STEP 1: First Pass (Ingesting / Repairing Records) ---")
        for item in sample_listings:
            comp, job, is_new_c, is_new_j = DiscoveryService.save_discovered_listing(db, item)
            print(f"Saved: {comp.company_name} | {job.job_title} | Peak: {job.maximum_ctc} LPA | Stipend: {job.stipend_amount} | NewComp: {is_new_c} | NewJob: {is_new_j}")

        # Record counts after Pass 1
        companies_count_1 = db.query(Company).count()
        jobs_count_1 = db.query(JobOpportunity).count()
        print(f"\nPass 1 Total Companies: {companies_count_1}, Total Jobs: {jobs_count_1}")

        print("\n--- STEP 2: Re-running Extraction (Deduplication Check) ---")
        for item in sample_listings:
            comp, job, is_new_c, is_new_j = DiscoveryService.save_discovered_listing(db, item)
            assert not is_new_c, f"Duplicate company created on re-run for {item['company_name']}"
            assert not is_new_j, f"Duplicate job created on re-run for {item['job_title']}"

        companies_count_2 = db.query(Company).count()
        jobs_count_2 = db.query(JobOpportunity).count()
        assert companies_count_2 == companies_count_1, "Company count increased on re-run!"
        assert jobs_count_2 == jobs_count_1, "Job count increased on re-run!"
        print(f"Pass 2 verified: Zero duplicates created (Companies: {companies_count_2}, Jobs: {jobs_count_2})")

        print("\n--- STEP 3: Verifying Database Records Field Values ---")

        # 1. C-DOT verification
        cdot = db.query(Company).filter(Company.company_name.ilike("%C-DOT%")).first()
        assert cdot is not None, "C-DOT company missing"
        assert cdot.company_name == "C-DOT(Centre for Development of Telematics)", f"Unexpected C-DOT name: {cdot.company_name}"
        cdot_job = db.query(JobOpportunity).filter(JobOpportunity.company_id == cdot.id).first()
        assert cdot_job.job_title == "Scientist 'B'", f"Unexpected C-DOT job title: {cdot_job.job_title}"
        assert cdot_job.maximum_ctc == 22.4, f"Unexpected C-DOT max CTC: {cdot_job.maximum_ctc}"
        assert cdot_job.salary_lpa == 22.4, f"Unexpected C-DOT salary_lpa: {cdot_job.salary_lpa}"
        assert cdot_job.stipend_amount is None, "C-DOT stipend should be None"
        print("PASS: C-DOT company and Scientist 'B' are separate. Salary: 22.4 LPA, Stipend: None.")

        # 2. Quest Global verification
        quest = db.query(Company).filter(Company.company_name.ilike("%Quest Global%")).first()
        assert quest is not None
        quest_job = db.query(JobOpportunity).filter(JobOpportunity.company_id == quest.id).first()
        assert quest_job.job_title == "Trainee Engineer"
        assert quest_job.minimum_ctc == 4.5, f"Quest min CTC mismatch: {quest_job.minimum_ctc}"
        assert quest_job.maximum_ctc == 6.5, f"Quest max CTC mismatch: {quest_job.maximum_ctc}"
        print("PASS: Quest Global Trainee Engineer salary: 4.5–6.5 LPA.")

        # 3. KPMG verification
        kpmg = db.query(Company).filter(Company.company_name.ilike("%KPMG%")).first()
        assert kpmg is not None
        kpmg_job = db.query(JobOpportunity).filter(JobOpportunity.company_id == kpmg.id).first()
        assert kpmg_job.job_title == "Analyst 1"
        assert kpmg_job.maximum_ctc == 5.0, f"KPMG max CTC mismatch: {kpmg_job.maximum_ctc}"
        assert kpmg_job.stipend_amount == 20000.0, f"KPMG stipend mismatch: {kpmg_job.stipend_amount}"
        assert kpmg_job.stipend_period == "Per Month"
        assert kpmg_job.original_stipend_text == "20K"
        print("PASS: KPMG Analyst 1 salary: 5 LPA, stipend: 20K/month.")

        # 4. ClearTax verification
        cleartax = db.query(Company).filter(Company.company_name.ilike("%ClearTax%")).first()
        assert cleartax is not None
        ct_job = db.query(JobOpportunity).filter(JobOpportunity.company_id == cleartax.id).first()
        assert ct_job.job_title == "Sales Development Representative"
        assert ct_job.minimum_ctc == 6.4, f"ClearTax min CTC mismatch: {ct_job.minimum_ctc}"
        assert ct_job.maximum_ctc == 8.0, f"ClearTax max CTC mismatch: {ct_job.maximum_ctc}"
        assert ct_job.stipend_min == 22000.0, f"ClearTax stipend min mismatch: {ct_job.stipend_min}"
        assert ct_job.stipend_max == 27000.0, f"ClearTax stipend max mismatch: {ct_job.stipend_max}"
        print("PASS: ClearTax SDR salary: 6.4–8 LPA, stipend: 22K–27K/month.")

        # 5. Missing salary verification (Health & Glow)
        hg = db.query(Company).filter(Company.company_name.ilike("%Health & Glow%")).first()
        assert hg is not None
        hg_job = db.query(JobOpportunity).filter(JobOpportunity.company_id == hg.id).first()
        assert hg_job.maximum_ctc is None, f"Health & Glow salary should be None, got: {hg_job.maximum_ctc}"
        assert hg_job.salary_lpa is None, f"Health & Glow salary_lpa should be None, got: {hg_job.salary_lpa}"
        assert hg_job.stipend_amount == 5000.0, f"Health & Glow stipend min should be 5000"
        print("PASS: Health & Glow missing salary remains None (not 0.0), stipend: 5K–10K.")

        print("\n--- STEP 4: Verifying CompanyService API Serialization ---")
        companies, total = CompanyService.get_companies(db, skip=0, limit=20)
        print(f"CompanyService returned {len(companies)} companies (total: {total})")
        for c in companies:
            print(f"  Company: '{c.company_name}' | Role: '{c.job_role}' | Peak: {c.max_ctc} LPA | Loc: '{c.location}' | Type: '{c.job_type}' | Status: '{c.job_status}'")
            # Verify company name does not have concatenated job title
            if "C-DOT" in c.company_name:
                assert "Scientist" not in c.company_name, "C-DOT company name still has Scientist!"
                assert c.job_role == "Scientist 'B'", f"C-DOT job_role expected Scientist 'B', got {c.job_role}"
                assert c.max_ctc == 22.4, f"C-DOT peak package expected 22.4, got {c.max_ctc}"
            if "Quest Global" in c.company_name:
                assert "Trainee" not in c.company_name
                assert c.job_role == "Trainee Engineer"
                assert c.max_ctc == 6.5
            if "KPMG" in c.company_name:
                assert "Analyst" not in c.company_name
                assert c.job_role == "Analyst 1"
                assert c.max_ctc == 5.0
            if "Health & Glow" in c.company_name:
                assert c.max_ctc is None, "Health & Glow max_ctc should be None (Not Available)!"

    print("\n================================================")
    print("ALL PHASE 6 VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
    print("================================================")


if __name__ == "__main__":
    run_controlled_verification()

