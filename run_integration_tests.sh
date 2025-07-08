#!/bin/bash
# run_integration_tests.sh
# KPP Simulator Integration Test Runner

set -e  # Exit on any error

echo "🧪 Running KPP Simulator Integration Tests"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "simulation/engine.py" ]; then
    print_status "ERROR" "Please run this script from the KPP simulator root directory"
    exit 1
fi

# Check Python environment
print_status "INFO" "Checking Python environment..."
if ! command -v python &> /dev/null; then
    print_status "ERROR" "Python is not installed or not in PATH"
    exit 1
fi

python_version=$(python --version 2>&1)
print_status "INFO" "Using $python_version"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_status "WARNING" "No virtual environment detected. Consider using one."
else
    print_status "INFO" "Virtual environment: $VIRTUAL_ENV"
fi

# Install dependencies if needed
print_status "INFO" "Checking dependencies..."
if ! python -c "import pytest" &> /dev/null; then
    print_status "WARNING" "pytest not found, installing..."
    pip install pytest pytest-cov
fi

# Run validation first
print_status "INFO" "Running integration status validation..."
if python validate_integration_status.py; then
    print_status "SUCCESS" "Integration validation passed"
else
    print_status "WARNING" "Integration validation found issues - continuing with tests"
fi

echo ""
echo "🧪 Running Test Suite"
echo "===================="

# Run unit tests
print_status "INFO" "Running unit tests..."
if python -m pytest tests/unit/ -v --tb=short; then
    print_status "SUCCESS" "Unit tests passed"
else
    print_status "ERROR" "Unit tests failed"
    unit_test_failed=true
fi

# Run integration tests
print_status "INFO" "Running integration tests..."
if python -m pytest tests/integration/ -v --tb=short; then
    print_status "SUCCESS" "Integration tests passed"
else
    print_status "ERROR" "Integration tests failed"
    integration_test_failed=true
fi

# Run performance tests
print_status "INFO" "Running performance tests..."
if python -m pytest tests/performance/ -v --tb=short; then
    print_status "SUCCESS" "Performance tests passed"
else
    print_status "WARNING" "Performance tests failed or not found"
fi

# Run system integration test
print_status "INFO" "Running system integration test..."
if python test_system_integration.py; then
    print_status "SUCCESS" "System integration test passed"
else
    print_status "ERROR" "System integration test failed"
    system_test_failed=true
fi

# Run critical fixes implementation
print_status "INFO" "Running critical fixes validation..."
if python implement_critical_fixes.py; then
    print_status "SUCCESS" "Critical fixes validation passed"
else
    print_status "WARNING" "Critical fixes validation found issues"
fi

echo ""
echo "📊 Test Results Summary"
echo "======================"

# Count test results
if [ "$unit_test_failed" = true ]; then
    print_status "ERROR" "Unit tests: FAILED"
else
    print_status "SUCCESS" "Unit tests: PASSED"
fi

if [ "$integration_test_failed" = true ]; then
    print_status "ERROR" "Integration tests: FAILED"
else
    print_status "SUCCESS" "Integration tests: PASSED"
fi

if [ "$system_test_failed" = true ]; then
    print_status "ERROR" "System integration test: FAILED"
else
    print_status "SUCCESS" "System integration test: PASSED"
fi

# Overall result
if [ "$unit_test_failed" = true ] || [ "$integration_test_failed" = true ] || [ "$system_test_failed" = true ]; then
    echo ""
    print_status "ERROR" "Some tests failed! Please review the output above."
    print_status "INFO" "Recommendations:"
    print_status "INFO" "  1. Check the specific test failures"
    print_status "INFO" "  2. Review the integration status validation"
    print_status "INFO" "  3. Implement missing components or fix integration issues"
    print_status "INFO" "  4. Re-run tests after fixes"
    exit 1
else
    echo ""
    print_status "SUCCESS" "All tests passed! 🎉"
    print_status "INFO" "The KPP simulator is ready for use."
    exit 0
fi 