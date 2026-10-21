# History 

(Example Entry)
## 2026-10-20 — F2.1
- Done: dedup on (txn_id, posted_at); nulls in cost_center → 'UNASSIGNED'
- Decision: dropped rows with null amount instead of imputing (per Gavin)
- Next: F2.2. Open question: which FX rate source?