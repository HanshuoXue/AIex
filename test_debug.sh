#!/bin/bash

echo "🔍 Testing Debug Endpoints..."
echo "================================"

API_URL="https://api-alex-12345.azurewebsites.net"

echo "1. Basic health check:"
curl -s "$API_URL/" | jq . || echo "API not responding"

echo -e "\n2. Debug info:"
curl -s "$API_URL/debug" | jq '{flow_path_exists, flows_exists}'

echo -e "\n3. Matcher debug info (NEW!):"
curl -s "$API_URL/debug/matcher" | jq '.'

echo -e "\n4. Test match with debug:"
curl -s -X POST "$API_URL/match/all" \
  -H "Content-Type: application/json" \
  -d '{"bachelor_major": "Computer Science", "gpa_scale": "4.0", "gpa_value": 3.5, "ielts_overall": 6.5}' \
  | jq '{
    total_evaluated,
    eligible_count: (.eligible_matches | length),
    rejected_count: (.rejected_matches | length),
    first_error: .rejected_matches[0].error
  }'

echo -e "\n✅ Debug test complete!"
