import json
import sys
from git import Repo

def calculate_churn(start_date, end_date, out_file, commit_details_mode=False):
    repo = Repo()
    commits = repo.iter_commits(date_order=True, reverse=True, before=end_date, after=start_date)
    churn = {}
    total_lines_added = 0
    total_lines_deleted = 0
    total_lines_changed = 0
    for commit in commits:
        stats = commit.stats
        total_lines_added += stats.total["insertions"]
        total_lines_deleted += stats.total["deletions"]
        total_lines_changed += stats.total["lines"]
        for file in stats.files:
            # Filter out metrics reports
            if "metrics/reports/" in file:
                continue
            # Filter out non-code files
            if ".py" not in file and ".css" not in file and ".js" not in file and ".sql" not in file:
                continue
            # Filter out .pyc and .json, which match .py and .js and need to be filtered separately
            if ".pyc" in file or ".json" in file:
                continue
            if file not in churn:
                churn[file] = {
                    "Total Lines Added": 0,
                    "Total Lines Deleted": 0,
                    "Total Lines Changed": 0,
                    "Commits on File": 0,
                    "Avg Lines Added Per Commit": 0,
                    "Avg Lines Deleted Per Commit": 0,
                    "Avg Lines Changed Per Commit": 0
                }
                if commit_details_mode:
                    churn[file]["Commits"] = []
            churn[file]["Total Lines Added"] += stats.files[file]["insertions"]
            churn[file]["Total Lines Deleted"] += stats.files[file]["deletions"]
            churn[file]["Total Lines Changed"] += stats.files[file]["lines"]
            churn[file]["Commits on File"] += 1
            cof = churn[file]["Commits on File"]
            churn[file]["Avg Lines Added Per Commit"] = churn[file]["Total Lines Added"] / cof
            churn[file]["Avg Lines Deleted Per Commit"] = churn[file]["Total Lines Deleted"] / cof
            churn[file]["Avg Lines Changed Per Commit"] = churn[file]["Total Lines Changed"] / cof
            if commit_details_mode:
                commit_details = {}
                commit_details["SHA"] = commit.hexsha
                commit_details["Datetime"] = str(commit.committed_datetime)
                commit_details["Lines Added"] = stats.files[file]["insertions"]
                commit_details["Lines Deleted"] = stats.files[file]["deletions"]
                commit_details["Lines Changed"] = stats.files[file]["lines"]
                commit_details["Change Type"] = stats.files[file]["change_type"]
                churn[file]["Commits"].append(commit_details)
    with open(out_file, "w+", newline="") as out:
        json.dump(churn, out, indent=1)
    print("Total Lines Added During Period: " + str(total_lines_added))
    print("Total Lines Deleted During Period: " + str(total_lines_deleted))
    print("Total Lines Changed During Period: " + str(total_lines_changed))

def main():
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    try:
        detailed_string = sys.argv[3]
        if "t" in detailed_string.lower():
            detailed = True
        else:
            detailed = False
    except:
        detailed = False
    out_name = "metrics/reports/churn_" + start_date + "_to_" + end_date
    if detailed:
        out_name += "_detailed"
    out_name += ".json"
    calculate_churn(start_date, end_date, out_name, detailed)

if __name__ == "__main__":
    main()
