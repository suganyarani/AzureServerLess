import unittest
import os

# List of test modules to run
test_modules = ['test_reconciliation', 'test_sample']

# Load tests from modules
loader = unittest.TestLoader()
suites = [loader.loadTestsFromName(mod) for mod in test_modules]

# Combine all suites
combined_suite = unittest.TestSuite(suites)

# Run tests and capture results
runner = unittest.TextTestRunner(resultclass=unittest.TextTestResult, verbosity=2)
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
        with open(gh_out_path, "a") as gh:
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
