namespace java com.uber.devexp.uberstudio
namespace go uberstudio

include "./studio_scenario_configuration.thrift"

typedef string RunID

// Run default timeout is 30 mins
const i16 DEFAULT_RUN_TIMEOUT_SECS = 1800
// Transition default interval is 1sec
const i16 DEFAULT_TRANSITION_INTERVAL_SECS = 1
// The default flowID
const string DEFAULT_FLOW_ID = "uberx"
// The default delay, in seconds, before starting run
const i16 DEFAULT_DELAY_START_SECS = 0

enum RunState {
  CREATED = 0
  INITIALIZED = 1
  RUNNING = 2
  PAUSED = 3
  DEINITIALIZED = 4
  COMPLETED = 5
  CANCELED = 6
  FAILED = 7
}

enum DepopulateOnState {
  NEVER = 0
  SUCCESS = 1
  FAILURE = 2
  ALWAYS = 3
}

enum Action {
  StoreBootstrap = 100
  // ExecActionRequest.params is the order UUID
  StoreAwaitAndAcceptOrder = 101
  StoreMarkOrderReady = 102
  DriverAwaitAndAcceptOrder = 103
  // Pick up the food and head to eater
  DriverBeginTripEats = 104
  // Drop off the food
  DriverDropoffOrder = 105
  // Driver ends the trip
  DriverEndTripEats = 106
  // Update driver device lat-lon
  // The ExecActionRequest.params must be filled with comma separated
  // latitude and longitude: e.g., "37.3,-122.07"
  DriverUpdateDeviceLocation = 110
}

struct Run {
  1: required RunID id            (go.tag='yaml:"id"')
  2: required RunState state      (go.tag='yaml:"state"')
  3: required string flowID       (go.tag='yaml:"flowID"')
  4: optional RunOptions options  (go.tag='yaml:"options"')
  11: optional studio_scenario_configuration.ScenarioConfiguration originalScenario     (go.tag='yaml:"originalScenario"')
  12: optional studio_scenario_configuration.ScenarioConfiguration populatedScenario    (go.tag='yaml:"populatedScenario"')
  13: optional list<ActorAssignment> actorAssignments (go.tag='yaml:"actorAssignments"')
  14: optional string depopulationToken
  15: optional string jobUUID     	(go.tag='yaml:"jobUUID"')
}

struct RunOptions {
  1: optional i16 transitionIntervalInSecs = DEFAULT_TRANSITION_INTERVAL_SECS (go.tag='yaml:"transitionIntervalInSecs"')
  2: optional i16 runTimeoutInSecs = DEFAULT_RUN_TIMEOUT_SECS                 (go.tag='yaml:"runTimeoutInSecs"')

  // allowDriverCancellation determines whether a driver can be cancelled while on a job
  3: optional bool allowDriverCancellation = false                            (go.tag='yaml:"allowDriverCancellation"')

  // isSynchronous determines whether a call to StartRun will block until success, failure or timeout
  4: optional bool isSynchronous = false (go.tag='yaml:"isSynchronous"')

  // depopulateOn will depopulate the scenario based the given state
  5: optional DepopulateOnState depopulateOn = DepopulateOnState.SUCCESS (go.tag='yaml:"depopulateOn"')

  // delayStartInSecs is the number of seconds to wait before starting the run
  6: optional i16 delayStartInSecs = DEFAULT_DELAY_START_SECS     (go.tag='yaml:"delayStartInSecs"')
  7: optional string runID     (go.tag='yaml:"runID"')
}

struct ActorAssignment {
  1: required string actorID                (go.tag='yaml:"actorID"')
  2: required string roleID                 (go.tag='yaml:"roleID"')
  3: optional bool automate = false         (go.tag='yaml:"automate"')
  4: optional list<string> pauseOnStateIDs  (go.tag='yaml:"pauseOnStateIDs"')
}

// The timeout attribute is different from RunOptions.runTimeoutInSecs which indicates
// timeout for the entire flow. Instead, this timeout attribute limits the processing time
// for this single request (StartRunRequest) only.
// The default value is set to 45 seconds due to lengthy test account creation.
struct StartRunRequest {
  1: required string flowID
  2: optional string scenarioUUID
  3: optional studio_scenario_configuration.ScenarioConfiguration scenario
  4: optional list<ActorAssignment> actorAssignments
  5: optional RunOptions options
  6: optional string scenarioYAML
  7: optional i16 timeout = 45        (go.tag='yaml:"timeout"')
}

struct DriverGoOnlineRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct DriverGoOnlineResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct DriverAcceptRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 45         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct DriverAcceptResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct DriverArrivedRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct DriverArrivedResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct DriverBeginRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct DriverBeginResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct DriverDropoffRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct DriverDropoffResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct DriverCancelRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct DriverCancelResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct DriverGoOfflineRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct DriverGoOfflineResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct RiderRequestRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct RiderRequestResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct RiderCancelRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct RiderCancelResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

struct RiderAddDestinationRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  4: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct RiderAddDestinationResponse {
  1: optional string message  (go.tag='yaml:"message"')
}

// We'll use a universal ExecActionRequest struture for all the orchestrator requests
// to reduce redundancy and simplify the data structure design and code implementation.
// The 3rd argument is newly added for action type, the 7th argument is optional for
// additional params in JSON form.
// The 8th argument is defined to accomodate the requirement of InteractiveRequest interface though
// not used
struct ExecActionRequest {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: required Action action            (go.tag='yaml:"action"')
  4: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  5: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  7: optional string params            (go.tag='yaml:"params"')
  8: optional studio_scenario_configuration.Location location        (go.tag='yaml:"location"')
}

struct ExecActionResponse {
  1: optional string message           (go.tag='yaml:"message"')
}

// ExecActionRequest2 adds a freely named action. Validation of the action is done
// on the server side.
struct ExecActionRequest2 {
  1: required string runID             (go.tag='yaml:"runID"')
  2: required string actorID           (go.tag='yaml:"actorID"')
  3: required string action            (go.tag='yaml:"action"')
  4: optional i64 timestamp            (go.tag='yaml:"timestamp"')
  5: optional i16 timeout = 10         (go.tag='yaml:"timeout"')
  6: optional string params            (go.tag='yaml:"params"')
  8: optional string cadenceTaskList   (go.tag='yaml:"cadenceTaskList"')
}

// ExecActionResponse2 uses testScenario as the domain model to maintain the test state.
// The result field is optional, the return value of the action.
struct ExecActionResponse2 {
 1: optional string message           (go.tag='yaml:"message"')
 2: optional string result			  (go.tag='yaml:"result"')
}

// QueryTestAccountsPoolRequest is the request to query test accounts pool status
// Only one of the attribues is required.
struct QueryTestAccountsPoolRequest {
  1: optional string runID
  2: optional studio_scenario_configuration.ScenarioConfiguration scenario
  3: optional string scenarioYAML
}

// QueryTestAccountsPoolResponse is the response of test accounts pool query
// It lists current active group workflow IDs.
struct QueryTestAccountsPoolResponse {
  1: optional string poolWorkflowID
  2: optional list<string> groupWorkflowID
}

service Orchestrator {
  // Start
  Run StartRun(
    1: StartRunRequest request
  )
  // Pause
  void PauseRun(
    1: RunID id
  )
  // Resume
  void ResumeRun(
    1: RunID id
  )
  // End
  void EndRun(
    1: RunID id
  )
  // Cancel
  void CancelRun(
    1: RunID id
  )
  // Get
  Run GetRun(
    1: RunID id
  )


  //// Interactive Endpoints ////

  // Driver Endpoints //

  // DriverGoOnline will call the RTAPI go-online endpoint for the given runID session and
  // driver actorID specified in the `StartRun` call's scenario configuration
  DriverGoOnlineResponse DriverGoOnline(
    1: DriverGoOnlineRequest request
  )

  // DriverAccept will, for the given runID session and driver actorID specified in the
  // `StartRun` call's scenario configuration, poll RTAPI for dispatched jobs and accept the job if dispatched
  DriverAcceptResponse DriverAccept(
  1: DriverAcceptRequest request
  )

  // DriverArrived will, for the given runID session and driver actorID specified in the
  // `StartRun` call's scenario configuration, hit an RTAPI endpoint to indicate the driver has arrived
  DriverArrivedResponse DriverArrived(
    1: DriverArrivedRequest request
  )

  // DriverBegin will, for the given runID session and driver actorID specified in the
  // `StartRun` call's scenario configuration, hit an RTAPI endpoint to indicate the driver begun the trip
  DriverBeginResponse DriverBegin(
    1: DriverBeginRequest request
  )

  // DriverDropoff will, for the given runID session and driver actorID specified in the
  // `StartRun` call's scenario configuration, hit an RTAPI endpoint to indicate the driver has dropped off the rider
  DriverDropoffResponse DriverDropoff(
    1: DriverDropoffRequest request
  )

  // DriverGoOffline will, for the given runID session and driver actorID specified in the
  // `StartRun` call's scenario configuration, hit an RTAPI endpoint to indicate the driver gone offline
  DriverGoOfflineResponse DriverGoOffline(
    1: DriverGoOfflineRequest request
  )

  // DriverCancel will, for the given runID session and driver actorID specified in the
  // `StartRun` call's scenario configuration, hit an RTAPI endpoint to indicate the driver has canceled the trip
  DriverCancelResponse DriverCancel(
    1: DriverCancelRequest request
  )

  // Rider Endpoints //

  // RiderRequest will, for the given runID session and rider actorID specified in the
  // `StartRun` call's scenario configuration, request a fare estimate and trip from RTAPI
  RiderRequestResponse RiderRequest(
    1: RiderRequestRequest request
  )

  // RiderCancel will, for the given runID session and rider actorID specified in the
  // `StartRun` call's scenario configuration, cancel a previously requested trip through RTAPI.
  // The request may happen at any time after RiderRequest was made.
  RiderCancelResponse RiderCancel(
    1: RiderCancelRequest request
  )

  // RiderAddDestination will, for the given runID session and rider actorID specified in the
  // `StartRun` call's scenario configuration, add a destination to the previously requested trip through RTAPI.
  // The request may happen at any time after a Rider has been dispatched to a Driver.
  RiderAddDestinationResponse RiderAddDestination(
    1: RiderAddDestinationRequest request
  )

  // ExecAction sends an action to Studio Orchestrator synchronously
  // Starting eats core flow implementation, all the actions are handled by
  // this single endpoint
  ExecActionResponse ExecAction(
    1: ExecActionRequest request
  )

  // ExecAction2 is an enhanced version of ExecAction with test scenario and named action fields defined
  // in the request.
  ExecActionResponse2 ExecAction2(
   1: ExecActionRequest2 request
  )

  // QueryTestAccountsPool queries the test accounts pool status
  QueryTestAccountsPoolResponse QueryTestAccountsPool(
   1: QueryTestAccountsPoolRequest request
  )
}