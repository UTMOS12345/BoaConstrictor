from pg_explain.models import PlanNode
from pg_explain.rules import (
    seq_scan_large_table, sort_spilled_to_disk, row_estimate_mismatch,
    nested_loop_no_index, bitmap_scan_few_rows, cte_materialized,
    parallel_not_used, filter_not_pushed, no_index_only_scan, sort_on_indexed_column,
    ALL_RULES, RULE_NAMES,
)

# Test 1: seq_scan_large_table
seq = PlanNode(node_type='Seq Scan', relation_name='orders', plan_rows=100000, filter="(total > 100)")
issues = seq_scan_large_table(seq, seq)
assert len(issues) == 1, f"Expected 1 issue, got {len(issues)}"
assert issues[0].severity == 'critical'
assert issues[0].rule_id == 'seq_scan_large_table'
print("PASS: seq_scan_large_table")

# Test 2: seq_scan_large_table should NOT fire for small tables
small = PlanNode(node_type='Seq Scan', relation_name='small', plan_rows=500, filter="(x > 1)")
assert len(seq_scan_large_table(small, small)) == 0
print("PASS: seq_scan_large_table skips small tables")

# Test 3: sort_spilled_to_disk
sort_node = PlanNode(node_type='Sort', sort_method='external merge', temp_written=1234)
issues = sort_spilled_to_disk(sort_node, sort_node)
assert len(issues) == 1
assert issues[0].rule_id == 'sort_spilled_to_disk'
print("PASS: sort_spilled_to_disk")

# Test 4: sort_spilled_to_disk should NOT fire for in-memory sort
mem_sort = PlanNode(node_type='Sort', sort_method='quicksort')
assert len(sort_spilled_to_disk(mem_sort, mem_sort)) == 0
print("PASS: sort_spilled_to_disk skips in-memory sorts")

# Test 5: row_estimate_mismatch
mismatch = PlanNode(node_type='Index Scan', relation_name='orders', plan_rows=1500, actual_rows=31240)
issues = row_estimate_mismatch(mismatch, mismatch)
assert len(issues) == 1
assert issues[0].rule_id == 'row_estimate_mismatch'
print("PASS: row_estimate_mismatch")

# Test 6: row_estimate_mismatch should NOT fire for small actuals
small_actual = PlanNode(node_type='Index Scan', plan_rows=10, actual_rows=500)
assert len(row_estimate_mismatch(small_actual, small_actual)) == 0
print("PASS: row_estimate_mismatch skips small actuals")

# Test 7: nested_loop_no_index
inner = PlanNode(node_type='Seq Scan', relation_name='orders', plan_rows=5000)
nl = PlanNode(node_type='Nested Loop', join_type='Inner', children=[PlanNode(node_type='Index Scan'), inner])
inner.parent = nl
issues = nested_loop_no_index(nl, nl)
assert len(issues) == 1
assert issues[0].rule_id == 'nested_loop_no_index'
print("PASS: nested_loop_no_index")

# Test 8: bitmap_scan_few_rows
bitmap = PlanNode(node_type='Bitmap Heap Scan', plan_rows=3, actual_rows=3)
issues = bitmap_scan_few_rows(bitmap, bitmap)
assert len(issues) == 1
assert issues[0].rule_id == 'bitmap_scan_few_rows'
print("PASS: bitmap_scan_few_rows")

# Test 9: cte_materialized
cte = PlanNode(node_type='CTE Scan', cte_name='my_cte', relation_name='my_cte')
issues = cte_materialized(cte, cte)
assert len(issues) == 1
assert issues[0].rule_id == 'cte_materialized'
print("PASS: cte_materialized")

# Test 10: parallel_not_used
large = PlanNode(node_type='Seq Scan', relation_name='orders', plan_rows=200000, parallel_aware=False)
issues = parallel_not_used(large, large)
assert len(issues) == 1
assert issues[0].rule_id == 'parallel_not_used'
print("PASS: parallel_not_used")

# Test 11: parallel_not_used should NOT fire for small tables
small = PlanNode(node_type='Seq Scan', plan_rows=50000)
assert len(parallel_not_used(small, small)) == 0
print("PASS: parallel_not_used skips small tables")

# Test 12: filter_not_pushed
idx = PlanNode(node_type='Index Scan', relation_name='orders', filter="(total > 100)")
issues = filter_not_pushed(idx, idx)
assert len(issues) == 1
assert issues[0].rule_id == 'filter_not_pushed'
print("PASS: filter_not_pushed")

# Test 13: sort_on_indexed_column
s = PlanNode(node_type='Sort', sort_key=['created_at DESC'])
issues = sort_on_indexed_column(s, s)
assert len(issues) == 1
assert issues[0].rule_id == 'sort_on_indexed_column'
print("PASS: sort_on_indexed_column")

# Test 14: no_index_only_scan
idx_scan = PlanNode(node_type='Index Scan', relation_name='orders', actual_rows=500)
issues = no_index_only_scan(idx_scan, idx_scan)
assert len(issues) == 1
assert issues[0].rule_id == 'no_index_only_scan'
print("PASS: no_index_only_scan")

# Test 15: ALL_RULES has expected keys
expected = {'seq-scan', 'sort-spill', 'row-estimate', 'nested-loop-no-index',
            'bitmap-few-rows', 'cte-materialized', 'parallel-not-used',
            'filter-not-pushed', 'no-index-only', 'sort-indexed'}
assert set(ALL_RULES.keys()) == expected
print(f"PASS: ALL_RULES has {len(ALL_RULES)} rules")

print("\n=== All Phase 5 tests passed! ===")