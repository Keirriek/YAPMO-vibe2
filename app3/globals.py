config_data={}
log_content=[]
log_local=False

# Add the aborted flag
aborted = False

# Progress tracking variables
progress_total = 0
progress_done = 0
progress_todo = 0
progress_success = 0
progress_failures = 0
progress_files_sec = 0.0000  # 4 decimalen
progress_percentage = 0.0
progress_status = "idle"  # idle, working, finished