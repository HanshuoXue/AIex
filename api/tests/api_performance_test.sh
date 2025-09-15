#!/bin/bash

# API Performance Test Script
# Usage: ./api_performance_test.sh [options]
# Options:
#   -1    Run quick match test
#   -2    Run detailed analysis test  
#   -3    Run complete analysis test
#   -a    Run all tests (default)
#   -h    Show help information

API_BASE_URL="https://api-alex-test-1757506758.azurewebsites.net"
TEST_DATA='{
  "name": "Test User",
  "age": 24,
  "bachelor_major": "Computer Science",
  "gpa": 3.5,
  "gpa_value": 85,
  "ielts": 6.5,
  "ielts_overall": 6.5,
  "budget": 50000,
  "interests": ["Computer Science", "AI"],
  "location_preference": "Auckland"
}'

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Show help information
show_help() {
    echo "API Performance Test Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -1    Run quick match test"
    echo "  -2    Run detailed analysis test"
    echo "  -3    Run complete analysis test"
    echo "  -a    Run all tests (default)"
    echo "  -h    Show help information"
    echo ""
}

# Calculate time difference
calculate_duration() {
    local start_time=$1
    local end_time=$2
    local duration=$(echo "$end_time - $start_time" | bc -l)
    printf "%.3f" $duration
}

# Run test and record time
run_test() {
    local test_name=$1
    local endpoint=$2
    local jq_filter=$3
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}$test_name${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Record start time
    start_time=$(date +%s.%N)
    start_timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}Start time: $start_timestamp${NC}"
    
    # Execute API call
    response=$(curl -s -X POST "$API_BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$TEST_DATA")
    
    # Record end time
    end_time=$(date +%s.%N)
    end_timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}End time: $end_timestamp${NC}"
    
    # Calculate total duration
    duration=$(calculate_duration $start_time $end_time)
    echo -e "${RED}Total duration: ${duration} seconds${NC}"
    
    # Display results
    if [ -n "$jq_filter" ]; then
        echo -e "${YELLOW}Results:${NC}"
        echo "$response" | jq -r "$jq_filter"
    else
        echo -e "${YELLOW}Results:${NC}"
        echo "$response" | jq .
    fi
    
    echo ""
}

# Quick match test
test_quick_match() {
    run_test "1️⃣ Quick Match (Find 3 eligible programs)" "/match" ". | length"
}

# Detailed analysis test
test_detailed_analysis() {
    run_test "2️⃣ Detailed Analysis (First 3 programs, show eligible + rejected)" "/match/detailed" '"Total: \(.total_evaluated), Eligible: \(.eligible_matches | length), Rejected: \(.rejected_matches | length)"'
}

# Complete analysis test
test_complete_analysis() {
    run_test "3️⃣ Complete Analysis (First 5 programs, show eligible + rejected)" "/match/all" '"Total: \(.total_evaluated), Eligible: \(.eligible_matches | length), Rejected: \(.rejected_matches | length)"'
}

# Run all tests
run_all_tests() {
    echo -e "${BLUE}🚀 Starting API Performance Tests${NC}"
    echo -e "${BLUE}Test time: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
    
    test_quick_match
    test_detailed_analysis
    test_complete_analysis
    
    echo -e "${GREEN}✅ All tests completed${NC}"
}

# Main program
main() {
    # Check if required tools are installed
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq tool is required${NC}"
        exit 1
    fi
    
    if ! command -v bc &> /dev/null; then
        echo -e "${RED}Error: bc tool is required${NC}"
        exit 1
    fi
    
    # Parse command line arguments
    case "${1:-}" in
        -1)
            test_quick_match
            ;;
        -2)
            test_detailed_analysis
            ;;
        -3)
            test_complete_analysis
            ;;
        -a|"")
            run_all_tests
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo -e "${RED}Error: Unknown option '$1'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main program
main "$@"
