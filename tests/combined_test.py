import unittest
import os
from HtmlTestRunner import HTMLTestRunner
from datetime import datetime
from tests.test_framework import TestDataDriven

# List of test modules to run
test_modules = ['test_sample']#, 'test_reconciliation' ]

# Load tests from modules
loader = unittest.TestLoader()

suites = unittest.TestSuite(
    [loader.loadTestsFromName(mod) for mod in test_modules] +
    [loader.loadTestsFromTestCase(TestDataDriven)]
)


# Combine all suites
combined_suite = unittest.TestSuite(suites)
# Run tests and capture results
# runner = unittest.TextTestRunner(resultclass=unittest.TextTestResult, verbosity=2)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_filename = f"Agent_DataDriven_Test_Report.html"
runner = HTMLTestRunner(
    output="testdata/",
    report_name=report_filename.replace('.html', ''),  # report_name is for the file name base
    report_title='Agent Data Driven Unittest Report',
    # description='Excel Data Driven Tests for Addition Logic',
    combine_reports=True # Ensures one single report file is created
)
result = runner.run(combined_suite)

# Summary
print("\n--- Test Summary ---")
print(f"Total tests run: {result.testsRun}")
print(f"Failures: {len(result.failures)}")
print(f"Errors: {len(result.errors)}")
print(f"Skipped: {len(result.skipped)}")


# Write results to GitHub Actions output (preferred: GITHUB_OUTPUT)
gh_out_path = os.environ.get("GITHUB_OUTPUT")
if gh_out_path:
    try:
        with open(gh_out_path, "w") as gh:
            gh.write(f"tests_run={result.testsRun}\n")
            gh.write(f"failures={len(result.failures)}\n")
            gh.write(f"errors={len(result.errors)}\n")
            gh.write(f"skipped={len(result.skipped)}\n")
    except Exception as e:
        print(f"Warning: failed to write GITHUB_OUTPUT: {e}")
else:
    # Fallback: print workflow command (deprecated but may work on older runners)
    print(f"::set-output name=tests_run::{result.testsRun}")
    print(f"::set-output name=failures::{len(result.failures)}")
    print(f"::set-output name=errors::{len(result.errors)}")
    print(f"::set-output name=skipped::{len(result.skipped)}")
