from utility import utils
from queryrunner_client import Client
import pandas as pd
import os

"""
The queryrunner_client module provides a client for executing SQL queries against Uber's databases.

Key features:
- Supports both consumer and user-based authentication
- Handles query execution and result fetching
- Returns results as pandas DataFrames
- Provides error handling and retries

For more details see: https://engdocs.uberinternal.com/queryrunner_client/usage.ticket

"""



def execute_query(query, consumer=False, db='metesv2'):
    """
    Execute a query on the specified database and return the results as a DataFrame.

    Args:
        query (str): The query to be executed.
        consumer (bool): If True, use the consumer client, otherwise use the user email client.
        db (str): The name of the database in which the query is to be executed (default is 'metesv2').

    Returns:
        pd.DataFrame: The result of the query from the database, or an empty DataFrame if an error occurs.
    """
    print(query)
    try:
        if consumer:
            qr = Client(consumer_name="mta-internal-group")
        else:
            username = os.environ.get("USERNAME") or os.environ.get("USER")
            qr = Client(user_email=f"{username}@ext.uber.com")
        
        cursor = qr.execute(db, query)
        df = pd.DataFrame(cursor.fetchall(), columns=cursor.columns)
        return df
    except Exception as e:
        print(f"Error while executing query '{query}' with error: {e}")
        return pd.DataFrame()

def poll(poll_id, consumer=False, db='metesv2'):
    
    print(poll_id)
    try:
        if consumer:
            qr = Client(consumer_name="mta-internal-group")
        else:
            qr = Client(user_email="akumar577@ext.uber.com")
            # qr = Client(user_email="akumar577@ext.uber.com")
        cursor = qr.get_result(poll_id)
        print(cursor)
        df = pd.DataFrame(cursor.fetchall(), columns=cursor.columns)
        return df
    except Exception as e:
        print(f"Error while executing query with Error :: {e}")

    return pd.DataFrame()

def get_test_scene_id_list(run_uuid):
    assertion_query = f'''
    select
      *
    from
      test_scene_result
     where run_uuid = '{run_uuid}'
    order by result desc
    '''
    return execute_query(assertion_query, True)

def get_feature_name(test_method):
    query = f'''
        select
        scenarioname as feature_name
        from
        core_Automation_platform.test_case
        where
            parsedautomationname = '{test_method}'
            or appiumautomationname = '{test_method}'
        LIMIT 1
        '''
    return execute_query(query, consumer=False, db="presto")['feature_name']

def get_healthline_crash_uuids(userUUIDs):
    query_healthline = f'''
    select
        *
    from
        rta.healthline_crash_event_prod
    where
        user_uuid in ({userUUIDs})
    order by
        report_time DESC
    limit
        1
    '''
    return execute_query(query_healthline, consumer=False, db='neutrino')


def get_mtp_data(run_uuids):
    run_uuids = utils.list_to_string(run_uuids)
    select_query = f'''
    select 
    a.test_method, 
    a.run_uuid, 
    a.failure_reason, 
    a.created_at, 
    b.ticket_id, 
    a.failure_category_l1_triaged, 
    a.failure_category_l1,
    a.failure_category_l2,
    a.failure_category_l2_triaged, 
    a.execution_uuid, 
    a.os_version,
    a.node_type, 
    a.wisdom_issue_id,
    b.screen_shots_link,
    b.triaged_by,
    b.studio_uuid,
    b.video_link,
    b.log_link,
    a.platform,
    a.app_name,
    c.build_version,
    c.build_type,
    c.test_bundle_id
    from test_run a 
    join test_run_info b on a.run_uuid = b.run_uuid 
    join test_execution c on a.execution_uuid = c.execution_uuid
    where
    a.run_uuid in ({run_uuids}) '''
    return execute_query(select_query)


def get_mtp_data_from_group_execution(group_execution_uuids):
    group_execution_uuids = utils.list_to_string(group_execution_uuids)
    select_query = f'''
    select
      a.test_method,
      a.run_uuid,
      a.failure_reason,
      a.created_at,
      b.ticket_id,
      a.result,
      c.state,
      a.failure_category_l1_triaged,
      a.failure_category_l1,
      a.failure_category_l2,
      a.failure_category_l2_triaged,
      a.execution_uuid,
      a.os_version,
      a.node_type,
      b.screen_shots_link,
      b.triaged_by,
      b.studio_uuid,
      b.video_link,
      b.log_link,
      a.platform,
      a.app_name,
      c.build_version,
      c.execution_uuid,
      c.build_type,
      c.execution_group_id
    from
      test_run a
      join test_run_info b on a.run_uuid = b.run_uuid
      join (
        select
          execution_uuid,
          build_version,
          build_type,
          execution_group_id,
          state
        from
          test_execution
        where
          execution_group_id in ({group_execution_uuids})
        order by
          created_at
      ) c on a.execution_uuid = c.execution_uuid
    where 
        a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        '''
        
    return execute_query(select_query)


def get_consecutive_CD_builds(platform, app_name, build_version, total_consecutive_builds):
    consecutive_builds_query = f'''
    with cte_base as (
              select
                build_uuid,
                build_version
              from
                app_bundle
              where
                platform = '{platform.lower()}'
                and app_name = '{app_name.lower()}'
                and created_at > (select created_at from app_bundle where build_version = "{build_version}" limit 1)
                and build_version != "{build_version}"
                and state = "passed"
                and build_type = "NIGHTLY"
              group by
                build_uuid,
                build_version
            ),
            cte_final as (
              select
                build_uuid,
                build_version,
                created_at,
                dense_rank() over(
                  order by
                    created_at
                ) as rn
              from
                (
                  select
                    x.*,
                    created_at,
                    dense_rank() over (
                      partition by build_version
                      order by
                        created_at desc
                    ) as rnk
                  from
                    cte_base x
                    join app_bundle y on x.build_version = y.build_version
                  group by
                    1,
                    2,
                    3
                  order by
                    3
                ) t
              where
                rnk = 1
            )
            select
              *
            from
              cte_final
            where
              rn <= {total_consecutive_builds}
            '''
    return execute_query(consecutive_builds_query, True)


def get_mtp_data_from_jira(ticket_list):
    
    open_ticket_mtp_query = f'''
    select 
    a.test_method, 
    a.run_uuid, 
    a.failure_reason, 
    a.created_at, 
    b.ticket_id, 
    a.failure_category_l1_triaged, 
    a.failure_category_l1,
    a.failure_category_l2,
    a.failure_category_l2_triaged, 
    a.execution_uuid, 
    a.os_version,
    a.node_type, 
    c.test_bundle_id,
    c.build_version,
    c.build_uuid,
    b.screen_shots_link,
    b.triaged_by,
    b.video_link,
    b.log_link,
    b.crash_log_link,
    b.studio_uuid,
    a.platform,
    a.app_name
    from test_run a 
    join test_run_info b on a.run_uuid = b.run_uuid
    join test_execution c on a.execution_uuid = c.execution_uuid
    where 
    a.run_uuid !="0290595d-4de6-4b5f-8fcc-20b629fea425"
    and b.ticket_id in ('''
    
    open_ticket_mtp_query = f'''{open_ticket_mtp_query}{utils.list_to_string(ticket_list)})'''
    
    
    open_ticket_mtp_result = execute_query(open_ticket_mtp_query, consumer=True)
    return open_ticket_mtp_result.drop_duplicates(subset=['ticket_id'])


def get_mtp_data_from_methods_and_bundle(bundle, all_methods):
    query = f'''
    SELECT
      a.test_method,
      a.run_uuid,
      a.failure_reason,
      a.created_at,
      b.ticket_id,
      a.failure_category_l1_triaged,
      a.failure_category_l1,
      a.failure_category_l2,
      a.failure_category_l2_triaged,
      a.execution_uuid,
      a.os_version,
      a.node_type,
      b.screen_shots_link,
      b.triaged_by,
      b.studio_uuid,
      b.video_link,
      b.log_link,
      a.platform,
      a.app_name,
      c.build_version,
      c.build_type
    FROM
      test_run a
      JOIN test_run_info b ON a.run_uuid = b.run_uuid
      JOIN (
        SELECT
          execution_uuid,
          build_version,
          build_type
        FROM
          test_execution
        WHERE
          trigger_by = 'v2-auto-trigger'
          AND test_bundle_name in ({bundle})
          AND state in ('time_out', 'fail')
          AND created_at >= DATE_SUB(CURDATE(), INTERVAL 0 DAY)
      ) c ON a.execution_uuid = c.execution_uuid
    WHERE
      a.result = 'FAILED'
      AND a.test_method in ({all_methods})
      AND a.is_final_retry is true
      and a.is_final_retry_group is true
    ORDER BY
      a.created_at DESC
    '''

    return execute_query(query)


def get_query_of_bundle_execution_completion(bundles, exe_date):
    bundle_string = utils.list_to_string(bundles, "' ,'", "'")
    query = f'''
    WITH completed_execution AS (
      WITH execution AS (
        SELECT
          teg.*,
          te.test_bundle_name,
          te.execution_uuid,
          te.node_type
        FROM
          test_execution te
          JOIN (
            SELECT
              app_name,
              build_type,
              build_uuid,
              build_version,
              created_at,
              id AS group_uuid,
              name,
              os_versions,
              platform,
              state,
              test_bundle_id,
              trigger_by
            FROM
              test_execution_group
            WHERE
              name IN ({bundle_string})
              AND trigger_by = 'v2-auto-trigger'
              AND created_at LIKE "%{exe_date}%"
          ) teg on teg.group_uuid = te.execution_group_id
        WHERE
            te.state IN ('fail', 'success', 'aborted')
            AND te.execution_order = 2
        ORDER BY
          te.test_bundle_name ASC,
          te.execution_order DESC
      )
      SELECT
        *
      FROM
        execution
    )
    SELECT
      *
    FROM
      completed_execution
    WHERE
      state IN ('time_out', 'fail')
    '''
    return query


def get_triaged_data(bundles, failure_type):
    bundle_list = utils.list_to_string(bundles)
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid
            from
            test_execution
            where test_bundle_name in ({bundle_list})
            and trigger_by in ('v2-auto-trigger')
            and state in ('time_out','fail')
            and created_at >= DATE_SUB(NOW(), INTERVAL 5 DAY)
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') != '' 
        and b.triaged_by != 'suggestion-auto-triage'
        and a.failure_reason like "{failure_type}%"
        and a.is_final_retry_group is true
        and a.is_final_retry is true 
        order by a.created_at desc
    '''

    return execute_query(query, consumer=True, db='metesv2')


def get_triaged_data_for_freight(bundles, failure_type):
    bundle_list = utils.list_to_string(bundles)
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid
            from
            test_execution
            where test_bundle_name in ({bundle_list})
            and trigger_by in ('vramal@ext.uber.com')
            and state in ('time_out','fail')
            and created_at >= DATE_SUB(NOW(), INTERVAL 5 DAY)
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') != '' 
        and b.triaged_by != 'suggestion-auto-triage'
        and a.failure_reason like "{failure_type}%"
        and a.is_final_retry_group is true
        and a.is_final_retry is true 
        order by a.created_at desc
    '''

    return execute_query(query, consumer=True, db='metesv2')


def get_untriaged_data_for_freight(bundle, failure_type, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle}'
                    AND trigger_by in ('vramal@ext.uber.com')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at >= DATE('{date}')
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and b.triaged_by != 'suggestion-auto-triage'
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason like "{failure_type}%"
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')


def get_triaged_data_without_failure_type_for_freight(bundles, failure_type):
    bundle_list = utils.list_to_string(bundles)
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid
            from
            test_execution
            where test_bundle_name in ({bundle_list})
            and trigger_by in ('vramal@ext.uber.com')
            and state in ('time_out','fail')
            and created_at >= DATE_SUB(NOW(), INTERVAL 5 DAY)
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') != '' 
        and b.triaged_by != 'suggestion-auto-triage'
        and a.failure_reason not like "%StaleElementReferenceException%"
        and a.failure_reason not like "{failure_type}%"
        and a.is_final_retry_group is true
        and a.is_final_retry is true 
        order by a.created_at desc
    '''

    return execute_query(query, consumer=True, db='metesv2')


def get_untriaged_data_without_failure_type_for_freight(bundle, not_failure_type, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle}'
                    AND trigger_by in ('vramal@ext.uber.com')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at >= DATE('{date}')
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason not like "%StaleElementReferenceException%"
        and a.failure_reason not like "{not_failure_type}%"
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')


def get_triaged_data_without_failure_type(bundles, failure_type):
    bundle_list = utils.list_to_string(bundles)
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid
            from
            test_execution
            where test_bundle_name in ({bundle_list})
            and trigger_by in ('v2-auto-trigger')
            and state in ('time_out','fail')
            and created_at >= DATE_SUB(NOW(), INTERVAL 5 DAY)
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') != '' 
        and b.triaged_by != 'suggestion-auto-triage'
        and a.failure_reason not like "%StaleElementReferenceException%"
        and a.failure_reason not like "%NetworkCallException%"
        and a.failure_reason not like "{failure_type}%"
        and a.is_final_retry_group is true
        and a.is_final_retry is true 
        order by a.created_at desc
    '''

    return execute_query(query, consumer=True, db='metesv2')


def get_untriaged_data(bundle, failure_type, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle}'
                    AND trigger_by in ('v2-auto-trigger')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at LIKE "%{date}%"
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason like "{failure_type}%"
        and a.os_version in ('18', '14')
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')

def get_untriaged_data_with_bundle_uuid_os_version(bundle_name, bundle_uuid, os_version, failure_type, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle_name}'
                    and id = '{bundle_uuid}'
                    AND trigger_by in ('v2-auto-trigger')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at LIKE "%{date}%"
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason like "{failure_type}%"
        and a.os_version = '{os_version}'
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')

def get_untriaged_data_without_failure_type(bundle, not_failure_type, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle}'
                    AND trigger_by in ('v2-auto-trigger')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at LIKE "%{date}%"
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason not like "%StaleElementReferenceException%"
        and a.failure_reason not like "%NetworkCallException%"
        and a.failure_reason not like "{not_failure_type}%"
        and a.os_version in ('18', '14')
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')

def get_untriaged_data_without_failure_type_with_bundle_uuid_os_version(bundle_name, bundle_uuid, os_version, not_failure_type, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged, 
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged, 
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle_name}'
                    and id = '{bundle_uuid}'
                    AND trigger_by in ('v2-auto-trigger')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at LIKE "%{date}%"
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason not like "%StaleElementReferenceException%"
        and a.failure_reason not like "%NetworkCallException%"
        and a.failure_reason not like "{not_failure_type}%"
        and a.os_version = '{os_version}'
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')


def get_untriaged_data_all_failure_type(bundle, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged,
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged,
        a.wisdom_issue_id,
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.studio_uuid,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name,
        c.build_version,
        c.build_type
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle}'
                    AND trigger_by in ('v2-auto-trigger')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at LIKE "%{date}%"
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason not like "%StaleElementReferenceException%"
        and a.failure_reason not like "%NetworkCallException%"
        and a.os_version in ('18', '14')
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')

def get_untriaged_data_all_failure_type_with_bundle_uuid_all_os_version(bundle_name, bundle_uuid, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged,
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged,
        a.wisdom_issue_id,
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.studio_uuid,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name,
        c.build_version,
        c.build_type
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle_name}'
                    AND id = '{bundle_uuid}'
                    AND trigger_by in ('v2-auto-trigger')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at LIKE "%{date}%"
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason not like "%StaleElementReferenceException%"
        and a.failure_reason not like "%NetworkCallException%"
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')



def get_untriaged_data_all_failure_type_for_freight(bundle, date):
    query = f'''
    select 
        a.test_method, 
        a.run_uuid, 
        a.failure_reason, 
        a.created_at, 
        b.ticket_id, 
        a.failure_category_l1_triaged,
        a.failure_category_l1,
        a.failure_category_l2,
        a.failure_category_l2_triaged,
        a.wisdom_issue_id,
        a.execution_uuid, 
        a.os_version,
        a.node_type, 
        b.screen_shots_link,
        b.triaged_by,
        b.studio_uuid,
        b.video_link,
        b.log_link,
        a.platform,
        a.app_name,
        c.build_version,
        c.build_type
        from test_run a 
        join test_run_info b on a.run_uuid = b.run_uuid 
        join (select
            execution_uuid,
            build_version,
            build_type
            from
            test_execution
            JOIN (
                  SELECT
                    id AS group_uuid
                  FROM
                    test_execution_group
                  WHERE
                    name = '{bundle}'
                    AND trigger_by in ('vramal@ext.uber.com')
                    AND state IN ('time_out', 'fail', 'retry_in_progress')
                    AND created_at >= DATE('{date}')
                ) teg on teg.group_uuid = test_execution.execution_group_id
            order by created_at desc) c on a.execution_uuid = c.execution_uuid
        where
        a.result='FAILED' 
        and COALESCE(b.ticket_id, '') = ''
        and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
        and a.failure_reason not like "%StaleElementReferenceException%"
        and a.is_final_retry is true
        and a.is_final_retry_group is true
        order by a.failure_reason desc
    '''

    return execute_query(query, consumer=True, db='metesv2')

def get_today_triaged_data_from_wats():
    query = '''
    SELECT
      *
    FROM
      test_results
    WHERE
      pipeline IN ('e2e-release', 'e2e-nightly')
      AND result = 'failed'
      AND is_final=1
      AND jira_ticket IS NOT NULL
      AND jira_ticket <> ''
      AND created_at >= CURRENT_DATE
      AND failure_reason not like "%Data too large%" 
    '''
    return execute_query(query, consumer=True, db='wats')


def get_untriaged_skipped_data_from_wats():
    query = '''
    SELECT
      *
    FROM
      test_results
    WHERE
      pipeline IN ('e2e-release', 'e2e-nightly')
      AND result = 'skipped'
      AND video_link =''
      AND is_final=1
      AND (jira_ticket IS NULL OR jira_ticket = '')
      AND created_at >= CURRENT_DATE
      AND failure_reason not like "%Data too large%" 
    '''
    return execute_query(query, consumer=True, db='wats')

def get_triaged_data__for_all_failure_type(bundle, date):
  query = f'''
  select 
      a.test_method, 
      a.run_uuid, 
      a.failure_reason, 
      a.created_at, 
      b.ticket_id, 
      a.failure_category_l1_triaged,
      a.failure_category_l1,
      a.failure_category_l2,
      a.failure_category_l2_triaged,
      a.execution_uuid, 
      a.os_version,
      a.node_type, 
      b.screen_shots_link,
      b.triaged_by,
      b.studio_uuid,
      b.video_link,
      b.log_link,
      a.platform,
      a.app_name,
      c.build_version,
      c.build_type
      from test_run a 
      join test_run_info b on a.run_uuid = b.run_uuid 
      join (select
          execution_uuid,
          build_version,
          build_type
          from
          test_execution
          JOIN (
                SELECT
                  id AS group_uuid
                FROM
                  test_execution_group
                WHERE
                  name = '{bundle}'
                  AND trigger_by in ('v2-auto-trigger')
                  AND state IN ('time_out', 'fail', 'retry_in_progress')
                  AND created_at LIKE "%{date}%"
              ) teg on teg.group_uuid = test_execution.execution_group_id
          order by created_at desc) c on a.execution_uuid = c.execution_uuid
      where
      a.result='FAILED' 
      and COALESCE(b.ticket_id, '') != ''
      and b.triaged_by != 'suggestion-auto-triage'
      and a.failure_category_l1 not in ("INFRA", "INFRA_DL")
      and a.is_final_retry is true
      and a.is_final_retry_group is true
      order by a.failure_reason desc
  '''

  return execute_query(query, consumer=True, db='metesv2')
  


def get_methods_to_offboard():
    query=f'''
    WITH last_tuesday AS (
      SELECT
        DATE_SUB(
          CURDATE(),
          INTERVAL (WEEKDAY(CURDATE()) - 1 + 7) % 7 DAY
        ) AS date_value
    ),
    second_last_tuesday AS (
      SELECT
        DATE_SUB(
          (
            SELECT
              date_value
            FROM
              last_tuesday
          ),
          INTERVAL 7 DAY
        ) AS date_value
    ),
    last_tuesday_failures AS (
      WITH failed_tests AS (
          SELECT
            test_run.test_method,
            test_run.platform,
            test_execution_group.test_bundle_id,
            test_run_info.ticket_id AS first_ticket,
            ROW_NUMBER() OVER (PARTITION BY test_run.test_method ORDER BY test_execution_group.created_at) AS row_num
          FROM
            test_run
            JOIN test_run_info ON test_run.run_uuid = test_run_info.run_uuid
            JOIN test_execution ON test_run.execution_uuid = test_execution.execution_uuid
            JOIN test_execution_group ON test_execution.execution_group_id = test_execution_group.id
          WHERE
            test_execution_group.name IN (
              'android_eats_release_appium_main',
              'ios_eats_release_appium_main',
              'android_helix_dual_release_appium_main',
              'ios_helix_dual_release_appium_main',
              'android_carbon_release_appium_main',
              'ios_carbon_release_appium_main'
            )
            AND test_execution_group.trigger_by = 'v2-auto-trigger'
            AND DATE(test_execution_group.created_at) = (
              SELECT
                date_value
              FROM
                last_tuesday
            )
            AND test_run.result = 'FAILED'
            AND test_run.failure_category_l1 NOT IN ('INFRA', 'INFRA_DL')
            AND test_run.is_final_retry = TRUE
            AND test_run.is_final_retry_group = TRUE
        ),
        filtered_tests AS (
          SELECT 
            test_method,
            platform
          FROM failed_tests
          GROUP BY test_method, platform
          HAVING 
            (platform = 'android' AND COUNT(*) > 2) OR
            (platform = 'ios' AND COUNT(*) > 1)
        )
        SELECT 
          ft.test_method, 
          ft.platform,
          ft.test_bundle_id, 
          ft.first_ticket
        FROM failed_tests ft
        JOIN filtered_tests ftf 
          ON ft.test_method = ftf.test_method AND ft.platform = ftf.platform
        WHERE ft.row_num = 1
        ORDER BY ft.platform, ft.test_method
    ),
    second_last_tuesday_failures AS (
      WITH failed_tests AS (
          SELECT
            test_run.test_method,
            test_run.platform,
            test_execution_group.test_bundle_id,
            test_run_info.ticket_id AS second_ticket,
            ROW_NUMBER() OVER (PARTITION BY test_run.test_method ORDER BY test_execution_group.created_at) AS row_num
          FROM
            test_run
            JOIN test_run_info ON test_run.run_uuid = test_run_info.run_uuid
            JOIN test_execution ON test_run.execution_uuid = test_execution.execution_uuid
            JOIN test_execution_group ON test_execution.execution_group_id = test_execution_group.id
          WHERE
            test_execution_group.name IN (
              'android_eats_release_appium_main',
              'ios_eats_release_appium_main',
              'android_helix_dual_release_appium_main',
              'ios_helix_dual_release_appium_main',
              'android_carbon_release_appium_main',
              'ios_carbon_release_appium_main'
            )
            AND test_execution_group.trigger_by = 'v2-auto-trigger'
            AND DATE(test_execution_group.created_at) = (
              SELECT
                date_value
              FROM
                second_last_tuesday
            )
            AND test_run.result = 'FAILED'
            AND test_run.failure_category_l1 NOT IN ('INFRA', 'INFRA_DL')
            AND test_run.is_final_retry = TRUE
            AND test_run.is_final_retry_group = TRUE
        ),
        filtered_tests AS (
          SELECT 
            test_method,
            platform
          FROM failed_tests
          GROUP BY test_method, platform
          HAVING 
            (platform = 'android' AND COUNT(*) > 2) OR
            (platform = 'ios' AND COUNT(*) > 1)
        )
        SELECT 
          ft.test_method, 
          ft.platform,
          ft.second_ticket
        FROM failed_tests ft
        JOIN filtered_tests ftf 
          ON ft.test_method = ftf.test_method AND ft.platform = ftf.platform
        WHERE ft.row_num = 1
        ORDER BY ft.platform, ft.test_method
    )
    SELECT
      DISTINCT last_tuesday_failures.test_method,
      test_bundle_id,
      first_ticket,
      second_ticket
    FROM
      last_tuesday_failures
      JOIN second_last_tuesday_failures ON last_tuesday_failures.test_method = second_last_tuesday_failures.test_method
      where
  last_tuesday_failures.test_method not in (
    'com.uber.e2e.android.eats.test.gmp.VerifyOOSViewEventTest/testVerifyOosViewEvent',
    'com.uber.e2e.android.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest',
    'com.uber.e2e.ios.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess',
    'com.uber.e2e.android.carbon.test.userworkflow.DriverAcceptTripTest/testDriverAcceptTrip_dogfooding',
    'com.uber.e2e.android.helix.test.userworkflow.HomeScreenMoreTapTest/testHomeScreenMoreTapFlow_dogfooding',
    'com.uber.e2e.android.helix.test.userworkflow.USLSLSRRiderTest/verifySignInFeature_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.VerifyOOSViewEventTest/testVerifyOosViewEvent_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.CheckoutFromCartTabTesttestCheckoutFromCartTab_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.WelcomeLoginTest/testWelcomeScreenOptions_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.StoreSuggestionTapTest/testStoreSuggestionTap_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.AddToCartToCheckoutTest/testAddToCartToCheckout_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.PlaceOrderTest/testPlaceOrder_dogfooding',
    'com.uber.e2e.android.eats.test.userworkflow.CheckoutClickPromotionTest/testCheckoutClickPromotionApplied_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.PaymentOnboardingWalletTest/testPaymentOnboardingFromWallet_dogfooding',
    'com.uber.e2e.android.eats.test.identity.UnifiedSignupAndLoginWithChromeTest/testSignInWithOtpAndPasswordFeature_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.CheckoutFromCartTabTest/testCheckoutFromCartTab_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.PlaceOrderTest/testPickupStartFromStore_dogfooding',
    'com.uber.e2e.ios.eats.test.userworkflow.CheckoutClickPromotionTest/testCheckoutClickPromotionApplied_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.PaymentOnboardingWalletTest/testPaymentOnboardingFromWallet_dogfooding',
    'com.uber.e2e.ios.carbon.test.userworkflow.DriverAcceptTripTest/testDriverAcceptTrip_dogfooding',
    'com.uber.e2e.ios.helix.test.userworkflow.HomeScreenMoreTapTest/testHomeScreenMoreTapFlow_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding'
  )
  and COALESCE(first_ticket, '') != ''
  and COALESCE(second_ticket, '') != ''
  AND NOT (
    first_ticket LIKE 'MTA%'
    OR first_ticket LIKE 'CIDL%'
    OR first_ticket LIKE 'CAPINFRA%'
  )
  AND NOT (
    second_ticket LIKE 'MTA%'
    OR second_ticket LIKE 'CIDL%'
    OR second_ticket LIKE 'CAPINFRA%'
  )
    '''
    
    return execute_query(query, consumer=True, db="metesv2")

def get_methods_to_onboard_status():
    query=f'''
    SELECT
      test_run.test_method,
      test_run.test_bundle_name,
      test_run.result,
      test_execution_group.test_bundle_id,
      test_execution_group.id
    FROM
      test_run
      join test_execution_group on test_run.test_bundle_name = test_execution_group.name
    WHERE
      test_run.test_bundle_name IN (
        'Auto_off_boarding_iOS_Eats',
        'Auto_off_boarding_iOS_Helix_Dual',
        'Auto_off_boarding_iOS_Carbon',
        'Auto_off_boarding_Android_Eats',
        'Auto_off_boarding_Android_Helix_Dual',
        'Auto_off_boarding_Android_Carbon'
      )
      AND test_run.tags like "%v2-auto-trigger%"
      AND test_run.created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
      AND test_run.os_version in ('18', '14')
      AND test_run.failure_category_l1 NOT IN ('INFRA', 'INFRA_DL')
      AND test_run.is_final_retry = TRUE
      AND test_run.is_final_retry_group = TRUE
      AND test_run.test_method not in (
    'com.uber.e2e.android.eats.test.gmp.VerifyOOSViewEventTest/testVerifyOosViewEvent',
    'com.uber.e2e.android.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest',
    'com.uber.e2e.ios.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess',
    'com.uber.e2e.android.carbon.test.userworkflow.DriverAcceptTripTest/testDriverAcceptTrip_dogfooding',
    'com.uber.e2e.android.helix.test.userworkflow.HomeScreenMoreTapTest/testHomeScreenMoreTapFlow_dogfooding',
    'com.uber.e2e.android.helix.test.userworkflow.USLSLSRRiderTest/verifySignInFeature_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.VerifyOOSViewEventTest/testVerifyOosViewEvent_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.CheckoutFromCartTabTesttestCheckoutFromCartTab_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.WelcomeLoginTest/testWelcomeScreenOptions_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.StoreSuggestionTapTest/testStoreSuggestionTap_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.AddToCartToCheckoutTest/testAddToCartToCheckout_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.PlaceOrderTest/testPlaceOrder_dogfooding',
    'com.uber.e2e.android.eats.test.userworkflow.CheckoutClickPromotionTest/testCheckoutClickPromotionApplied_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.PaymentOnboardingWalletTest/testPaymentOnboardingFromWallet_dogfooding',
    'com.uber.e2e.android.eats.test.identity.UnifiedSignupAndLoginWithChromeTest/testSignInWithOtpAndPasswordFeature_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.CheckoutFromCartTabTest/testCheckoutFromCartTab_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.PlaceOrderTest/testPickupStartFromStore_dogfooding',
    'com.uber.e2e.ios.eats.test.userworkflow.CheckoutClickPromotionTest/testCheckoutClickPromotionApplied_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.PaymentOnboardingWalletTest/testPaymentOnboardingFromWallet_dogfooding',
    'com.uber.e2e.ios.carbon.test.userworkflow.DriverAcceptTripTest/testDriverAcceptTrip_dogfooding',
    'com.uber.e2e.ios.helix.test.userworkflow.HomeScreenMoreTapTest/testHomeScreenMoreTapFlow_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.CheckoutFromCartTabTest/testCheckoutFromCartTab_dogfooding'
  )
    '''
    return execute_query(query, consumer=True, db="metesv2")





def get_methods_to_onboard():
    query=f'''
    SELECT
      test_run.test_method,
      test_run.test_bundle_name,
      test_run.result,
      test_execution_group.test_bundle_id,
      test_execution_group.id
    FROM
      test_run
      join test_execution_group on test_run.test_bundle_name = test_execution_group.name
    WHERE
      test_run.test_bundle_name IN (
        'Auto_off_boarding_iOS_Eats',
        'Auto_off_boarding_iOS_Helix_Dual',
        'Auto_off_boarding_iOS_Carbon',
        'Auto_off_boarding_Android_Eats',
        'Auto_off_boarding_Android_Helix_Dual',
        'Auto_off_boarding_Android_Carbon'
      )
      AND test_run.tags like "%v2-auto-trigger%"
      AND test_run.created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
      AND test_run.os_version in ('18', '14')
      AND test_run.failure_category_l1 NOT IN ('INFRA', 'INFRA_DL')
      AND test_run.is_final_retry = TRUE
      AND test_run.is_final_retry_group = TRUE
      AND test_run.test_method not in (
    'com.uber.e2e.android.eats.test.gmp.VerifyOOSViewEventTest/testVerifyOosViewEvent',
    'com.uber.e2e.android.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest',
    'com.uber.e2e.ios.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess',
    'com.uber.e2e.android.carbon.test.userworkflow.DriverAcceptTripTest/testDriverAcceptTrip_dogfooding',
    'com.uber.e2e.android.helix.test.userworkflow.HomeScreenMoreTapTest/testHomeScreenMoreTapFlow_dogfooding',
    'com.uber.e2e.android.helix.test.userworkflow.USLSLSRRiderTest/verifySignInFeature_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.VerifyOOSViewEventTest/testVerifyOosViewEvent_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.CheckoutFromCartTabTesttestCheckoutFromCartTab_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.WelcomeLoginTest/testWelcomeScreenOptions_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.StoreSuggestionTapTest/testStoreSuggestionTap_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.AddToCartToCheckoutTest/testAddToCartToCheckout_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.PlaceOrderTest/testPlaceOrder_dogfooding',
    'com.uber.e2e.android.eats.test.userworkflow.CheckoutClickPromotionTest/testCheckoutClickPromotionApplied_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.PaymentOnboardingWalletTest/testPaymentOnboardingFromWallet_dogfooding',
    'com.uber.e2e.android.eats.test.identity.UnifiedSignupAndLoginWithChromeTest/testSignInWithOtpAndPasswordFeature_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.CheckoutFromCartTabTest/testCheckoutFromCartTab_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.PlaceOrderTest/testPickupStartFromStore_dogfooding',
    'com.uber.e2e.ios.eats.test.userworkflow.CheckoutClickPromotionTest/testCheckoutClickPromotionApplied_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.PaymentOnboardingWalletTest/testPaymentOnboardingFromWallet_dogfooding',
    'com.uber.e2e.ios.carbon.test.userworkflow.DriverAcceptTripTest/testDriverAcceptTrip_dogfooding',
    'com.uber.e2e.ios.helix.test.userworkflow.HomeScreenMoreTapTest/testHomeScreenMoreTapFlow_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.CheckoutFromCartTabTest/testCheckoutFromCartTab_dogfooding'
  )
    '''

    return execute_query(query, consumer=True, db="metesv2")





def get_methods_triaged_tickets(method_list):
    methods = "'"+"', '".join(method_list)+"'"
    query=f'''
    SELECT
      test_run.test_method,
      test_run_info.ticket_id
    FROM
      test_run
      JOIN test_run_info ON test_run.run_uuid = test_run_info.run_uuid
      join test_execution_group on test_run.test_bundle_name = test_execution_group.name
    WHERE
      test_run.test_bundle_name IN (
        'Auto_off_boarding_iOS_Eats',
        'Auto_off_boarding_iOS_Helix_Dual',
        'Auto_off_boarding_iOS_Carbon',
        'Auto_off_boarding_Android_Eats',
        'Auto_off_boarding_Android_Helix_Dual',
        'Auto_off_boarding_Android_Carbon',
        'android_eats_release_appium_main',
        'ios_eats_release_appium_main',
        'android_helix_dual_release_appium_main',
        'ios_helix_dual_release_appium_main',
        'android_carbon_release_appium_main',
        'ios_carbon_release_appium_main'
      )
      AND test_run.tags like "%v2-auto-trigger%"
      and COALESCE(test_run_info.ticket_id, '') != ''
      AND test_run.created_at >= DATE_SUB(NOW(), INTERVAL 6 DAY)
      AND test_run.os_version in ('18', '14')
      AND test_run.failure_category_l1 NOT IN ('INFRA', 'INFRA_DL')
      AND test_run.is_final_retry = TRUE
      AND test_run.is_final_retry_group = TRUE
      AND test_run.test_method in ({methods})
    '''
    return execute_query(query, consumer=True, db="metesv2")



def get_distinct_ticket_methods_from_presto(ticket_ids):
    """
    Fetch DISTINCT (ticket_id, test_method) pairs for the specified tickets
    from Atlantis Presto.
    Args:
        ticket_ids (List[str]): List of ticket keys/ids (e.g., ["MTA-123", ...]).
    Returns:
        pd.DataFrame: Columns [ticket_id, test_method]
    """
    if not ticket_ids:
        return pd.DataFrame(columns=["ticket_id", "test_method"])  # empty
    ticket_list_str = utils.list_to_string(ticket_ids)
    query = f'''
    SELECT DISTINCT ticket_id, test_method
    FROM rawdata_user.mysql_metesv2_metesv2_test_run_rows
    WHERE ticket_id IN ({ticket_list_str})
    '''
    return execute_query(query, consumer=False, db='presto-secure')


def summarize_impacts(ticket_methods_df):
    """
    Produce simple impact summaries:
      - per_ticket: number of DISTINCT test_method per ticket_id
      - per_method: number of DISTINCT ticket_id per test_method
    Args:
        ticket_methods_df (pd.DataFrame): Columns [ticket_id, test_method]
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (per_ticket_df, per_method_df)
          per_ticket_df columns: [ticket_id, num_distinct_methods]
          per_method_df columns: [test_method, num_distinct_tickets]
    """
    if ticket_methods_df is None or ticket_methods_df.empty:
        return (
            pd.DataFrame(columns=["ticket_id", "num_distinct_methods"]),
            pd.DataFrame(columns=["test_method", "num_distinct_tickets"]),
        )
    # Ensure only distinct pairs are considered
    distinct_pairs = ticket_methods_df.drop_duplicates(subset=["ticket_id", "test_method"])  # type: ignore[arg-type]
    per_ticket = (
        distinct_pairs
        .groupby("ticket_id", as_index=False)
        .agg(num_distinct_methods=("test_method", "nunique"))
        .sort_values(["num_distinct_methods", "ticket_id"], ascending=[False, True])
    )
    per_method = (
        distinct_pairs
        .groupby("test_method", as_index=False)
        .agg(num_distinct_tickets=("ticket_id", "nunique"))
        .sort_values(["num_distinct_tickets", "test_method"], ascending=[False, True])
    )
    return per_ticket, per_method

    
if __name__ == "__main__":
    
    query=f'''
    select
              scenarioname as feature_name
            from
              core_Automation_platform.test_case
            where
                parsedautomationname = 'com.uber.e2e.ios.eats.test.userworkflow.PaymentUpfrontChargeTest/verifyAddAndRemovePaymentMethod'
                or appiumautomationname = 'com.uber.e2e.ios.eats.test.userworkflow.PaymentUpfrontChargeTest/verifyAddAndRemovePaymentMethod'
            LIMIT 1
    '''
    
    print(execute_query(query, consumer=False, db="presto-secure"))



if __name__ == "__main__":
    regular_runs_data = get_mtp_data_from_methods_and_bundle("'android_helix_dual_nightly_appium_main', 'ios_helix_dual_nightly_appium_main', 'android_helix_dual_release_appium_main', 'ios_helix_dual_release_appium_main'", "'com.uber.e2e.ios.helix.test.rider.riderCoreRegression.ActivityHomeTest/testListOfReservedTripCardValidation'")

    regular_method_status = regular_runs_data.loc[regular_runs_data['test_method'] == "com.uber.e2e.ios.helix.test.rider.riderCoreRegression.ActivityHomeTest/testListOfReservedTripCardValidation"]

    print(regular_method_status)
    print(regular_method_status['ticket_id'] if len(regular_method_status)>0 else "")
    print(f'''=HYPERLINK("https://t3.uberinternal.com/browse/{regular_method_status['ticket_id'][0]}", "{regular_method_status['ticket_id'][0]}")''' if len(regular_method_status)>0 else "")


