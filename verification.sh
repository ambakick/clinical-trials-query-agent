#!/bin/bash
  BASE="http://localhost:8000/api/v1/query"
  PASS=0; FAIL=0

  check() {
    local name="$1"; shift
    local result
    result=$(curl -s -X POST "$BASE" -H "Content-Type: application/json" -d "$1")
    local data_len
    data_len=$(echo "$result" | python3 -c "
  import json,sys
  r=json.load(sys.stdin)
  v=r.get('visualization',{})
  d=v.get('data',{})
  if isinstance(d,list): print(len(d))
  elif 'nodes' in d: print(len(d['nodes']))
  else: print(0)
  " 2>/dev/null)
    if [ "$data_len" -gt 0 ] 2>/dev/null; then
      echo "PASS: $name (data_len=$data_len)"
      ((PASS++))
    else
      echo "FAIL: $name (data_len=$data_len)"
      echo "  Response: $(echo "$result" | head -c 200)"
      ((FAIL++))
    fi
  }

  check "time_trend"   '{"query":"Pembrolizumab trials per year since 2015","drug_name":"Pembrolizumab","start_year":2015}'
  check "distribution" '{"query":"How are lung cancer trials distributed across phases?","condition":"Lung cancer"}'
  check "comparison"   '{"query":"Compare phases for Pembrolizumab vs Nivolumab"}'
  check "geographic"   '{"query":"Which countries have the most melanoma trials?","condition":"Melanoma"}'
  check "network"      '{"query":"Show sponsor drug network for breast cancer","condition":"Breast cancer"}'
  check "ranking"      '{"query":"Top 10 sponsors for completed melanoma trials","condition":"Melanoma","status":["COMPLETED"]}'
  check "phase_filter" '{"query":"Phase 3 lung cancer trials per year","condition":"Lung cancer","trial_phase":["PHASE3"],"start_year":2015}'
  check "multi_status" '{"query":"Recruiting and active diabetes trials by phase","condition":"Diabetes","status":["RECRUITING","ACTIVE_NOT_RECRUITING"]}'

  echo ""
  echo "Results: $PASS passed, $FAIL failed"