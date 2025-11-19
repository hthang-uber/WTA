from utility import AutoTriageUtility
from utility import DBQueryExecutor


if __name__ == "__main__":

    feature_name = "customerobsession"

    triaged_data = DBQueryExecutor.get_triaged_data_from_wats()
    untriaged_data = DBQueryExecutor.get_untriaged_data_from_wats()
    AutoTriageUtility.iterate_matching_failure_for_wats(untriaged_data, triaged_data)




