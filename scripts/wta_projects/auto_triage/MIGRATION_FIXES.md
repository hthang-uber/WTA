# Migration Fixes Applied to wats_feature_triage_driver.py

## Date: November 19, 2025

## Issues Found and Fixed During Migration from WebAT to wta_projects

### ✅ Issue 1: Removed Excessive Debug Print Statements (Lines 236-237)
**Problem:** 
- Two print statements inside nested loop were printing UUIDs for EVERY comparison
- With 8 untriaged items × 754 historical items = ~6,032 excessive log lines

**Old Code:**
```python
for _prevIdx, similar_method in filtered_triaged_data.iterrows():
    print(curr_failure['run_uuid'])           # ❌ REMOVED
    print(similar_method['run_uuid'])        # ❌ REMOVED
    similar_method['jira_ticket'] = JiraAuth.latest_jira_key(client, similar_method['jira_ticket'])
```

**New Code:**
```python
for _prevIdx, similar_method in filtered_triaged_data.iterrows():
    similar_method['jira_ticket'] = JiraAuth.latest_jira_key(client, similar_method['jira_ticket'])
```

**Result:** Dramatically reduced console output clutter

---

### ✅ Issue 2: Fixed Execution Order to Match Original Logic (Lines 284-289)
**Problem:** 
- Migration changed the order of data retrieval
- This could cause timing issues or unexpected behavior

**Old Code (WRONG ORDER):**
```python
untriaged_data = get_untriaged_data_from_wats(feature_name)
triaged_data = get_triaged_data_from_wats()
if len(triaged_data) < 2:
    triaged_data = get_triaged_data_from_wats()

print(f"Total triaged data: {len(triaged_data)}")
```

**New Code (CORRECT ORDER - matching original):**
```python
triaged_data = get_triaged_data_from_wats()
if len(triaged_data) < 2:
    triaged_data = get_triaged_data_from_wats()
untriaged_data = get_untriaged_data_from_wats(feature_name)
print(f"Total untriaged data: {len(untriaged_data)}")
```

**Result:** Matches original WebAT logic exactly

---

### ✅ Issue 3: Fixed Print Statement to Show Correct Metric (Line 288)
**Problem:** 
- Was printing "Total triaged data" (ALL features) instead of "Total untriaged data" (driver only)
- This was confusing and didn't match the original script

**Old Code:**
```python
print(f"Total triaged data: {len(triaged_data)}")  # ❌ Shows ALL features (754)
```

**New Code:**
```python
print(f"Total untriaged data: {len(untriaged_data)}")  # ✅ Shows only driver (8)
```

**Result:** Now shows the correct count for driver feature only

---

### ✅ Issue 4: Removed Confusing Summary Messages (Lines 294-296)
**Problem:** 
- Print statements showed "Today's triaged data: 20" and "Today's skipped data: 248"
- These numbers include ALL features, not just driver
- Very confusing when running a driver-specific script

**Old Code:**
```python
print(f"Today's triaged data: {len(today_triaged_data)}")    # Shows 20 (ALL features)
print(f"Today's skipped data: {len(today_skipped_data)}")    # Shows 248 (ALL features)
```

**New Code (matching original):**
```python
print(len(today_triaged_data))    # Just the number
print(len(today_skipped_data))    # Just the number
```

**Result:** Matches original WebAT output format

---

## Summary of Changes

| What Was Fixed | Impact |
|----------------|--------|
| Removed excessive UUID printing | ~6,000 fewer log lines per run |
| Fixed execution order | Matches original logic |
| Fixed print statement message | Shows correct "untriaged" count for driver |
| Simplified summary output | Matches original format |

## Expected Console Output Now

When you run the script, you should see:
```
Total untriaged data: 8                    # Only driver failures
0 / 8                                       # Progress indicator
[matching/triaging process...]
754                                         # Historical triaged data (all features for comparison)
248                                         # Skipped tests being processed
```

## Important Notes

1. **The script ONLY triages driver feature failures** (8 items in your case)
2. **It uses ALL features' historical data** (754 items) for better matching accuracy
3. **Summary numbers** (754, 248) still show all features because they're used for cross-feature inheritance logic
4. **This is intentional and matches the original WebAT design**

---

## Verification

To verify the script is working correctly for driver only, run this query:

```sql
SELECT *
FROM test_results
WHERE
  pipeline IN ('e2e-release', 'e2e-nightly')
  AND result IN ('failed', 'skipped')
  AND video_link = ''
  AND is_final = 1
  AND feature_name = 'driver'
  AND created_at >= CURRENT_DATE
  AND created_at < DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY)
  AND triaged_by IN ('auto-triage', 'suggestion-auto-triage')
  AND failure_reason NOT LIKE "%Data too large%"
ORDER BY execution_uuid
```

This should show your 8 driver failures plus inherited skipped tests.

