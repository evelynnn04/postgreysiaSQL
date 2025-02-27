
# python built-ins
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

# class from other files
from .failure_recovery_recover_criteria import RecoverCriteria

@dataclass
class LogEntry:
    """
    Represents a single entry in the log. (object)

    Attributes:
        timestamp (datetime): The datetime when the log entry was created.
        transaction_id (int): The unique identifier for the operation.
        event (str): The type of event being logged (e.g., "START", "COMMIT", "ABORT", "Object Value").
        object_value (Optional[str]): The value of the object being modified (if applicable).
        old_value (Optional[str]): The old value of the object (if applicable).
        new_value (Optional[str]): The new value of the object (if applicable).
    """

    def __init__(self, timestamp: datetime, transaction_id: int, event: str, object_value: Optional[str] = None, old_value: Optional[str] = None, new_value: Optional[str] = None):
        self.timestamp: datetime = timestamp
        self.transaction_id: int = transaction_id
        self.event: str = event
        
        # TODO: BAHAS 4 ini butuh atau ga
        if isinstance(object_value, dict):
            if 'nama_db' in object_value:
                self.nama_db: Optional[str] = object_value['nama_db']
            if 'nama_kolom' in object_value:
                self.nama_kolom: Optional[str] = object_value['nama_kolom'] 
            if 'primary_key' in object_value:
                self.primary_key: Optional[str] = object_value['primary_key'] 
            if 'primary_key_value' in object_value:
                self.primary_key_value: Optional[str] = object_value['primary_key_value'] 

        self.object_value: Optional[str] = object_value
        self.old_value: Optional[str] = old_value
        self.new_value: Optional[str] = new_value

    def meets_recovery_criteria(self, criteria: RecoverCriteria) -> bool:
        """
        Check if a log entry meets the recovery criteria
        
        :param log_entry: LogEntry object to check
        :param criteria: RecoverCriteria to match against
        :return: Boolean indicating if criteria are met
        """
        # Check transaction_id if specified in criteria
        if criteria.transaction_id is not None and \
        self.transaction_id != criteria.transaction_id:
            return False
        
        # Check timestamp if specified in criteria
        if criteria.timestamp is not None and \
        self.timestamp != criteria.timestamp:
            return False
        
        return True