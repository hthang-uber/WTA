from utility import LocalDBQueries
from utility import utils


utils.remove_path("new_ticket")
utils.remove_path("testImg")
LocalDBQueries.delete_all_execution_status_dbs()