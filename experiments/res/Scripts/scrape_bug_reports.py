import BugReportBuilder
import os

CSP_tests_folder = "../../pages/CSP"
bugReportBuilder = BugReportBuilder.BugReportBuilder()

# Iterate over all test folders
for PoC_folder in [os.path.join(CSP_tests_folder, d) for d in os.listdir(CSP_tests_folder) if os.path.isdir(os.path.join(CSP_tests_folder, d))]:
    bug_id = os.path.basename(os.path.normpath(PoC_folder))
    bugReportBuilder.scrape_bug_report(bug_id=bug_id, save_scraped_content=True)

        

