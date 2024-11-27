from main_log_entry import LogEntry

def write_log_entry_to_file(log_file: str, entry: LogEntry):
        """
        Write a new log entry to the log file.
        """
        try:
            with open(log_file, 'a') as f:
                f.write(f"{entry.database_name},{entry.timestamp.isoformat(timespec='seconds')},{entry.transaction_id},{entry.event},{entry.object_value or ''},{entry.new_value or ''}\n")
        except FileNotFoundError:
            return []