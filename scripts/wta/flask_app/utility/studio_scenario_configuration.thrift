namespace java com.uber.devexp.studioscenarios
namespace go studioscenarios

typedef string ExperimentKey
typedef map<ExperimentKey, TreatmentGroupEnrollment> Experiments
typedef map<string, ParamValue> ParameterMap

struct Location {
    1: optional i32 cityID          (go.tag='yaml:"cityID,omitempty"')
    2: optional double latitude     (go.tag='yaml:"latitude,omitempty"')
    3: optional double longitude    (go.tag='yaml:"longitude,omitempty"')
}

struct Device {
    1: optional string id           (go.tag='yaml:"id,omitempty"')
    2: optional string type         (go.tag='yaml:"type,omitempty"')
    3: optional string model        (go.tag='yaml:"model,omitempty"')
    4: optional string osName       (go.tag='yaml:"osName,omitempty"')
    5: optional string osVersion    (go.tag='yaml:"osVersion,omitempty"')
    6: optional string appVersion   (go.tag='yaml:"appVersion,omitempty"')
    7: optional string locale       (go.tag='yaml:"locale,omitempty"')
    8: optional string serialNumber (go.tag='yaml:"serialNumber,omitempty"')
    9: optional Location location   (go.tag='yaml:"location,omitempty"')
}

struct Vehicle {
    1: optional string uuid                  (go.tag='yaml:"uuid,omitempty"')
    2: optional list<string> includedTags    (go.tag='yaml:"includedTags,omitempty"')
    3: optional list<string> excludedTags    (go.tag='yaml:"excludedTags,omitempty"')
    4: optional list<string> includedTraits  (go.tag='yaml:"includedTraits,omitempty"')
    5: optional list<string> excludedTraits  (go.tag='yaml:"excludedTraits,omitempty"')
}

struct Stage {
    1: required Location location                                   (go.tag='yaml:"location"')
    2: optional string tenancy                                      (go.tag='yaml:"tenancy,omitempty"')
    3: optional string productName                                  (go.tag='yaml:"productName,omitempty"')
    // Platform specific settings e.g. Studio map settings
    100: optional map<string,map<string,string>> platformSettings   (go.tag='yaml:"platformSettings,omitempty"')
}

// Shadow of XPC ParamValue to allow us to omitempty for YAML
union ParamValue {
  1: string stringVal (go.tag='yaml:"stringVal,omitempty"')
  2: i32 intVal       (go.tag='yaml:"intVal,omitempty"')
  3: double doubleVal (go.tag='yaml:"doubleVal,omitempty"')
  4: bool boolVal     (go.tag='yaml:"boolVal,omitempty"')
}

struct TreatmentGroupEnrollment {
    // The key of the treatment group. This can be found in Morpheus.
    // Specifying a key to a non-existent treatment group for the experiment will cause population to fail
    1: required string treatmentGroupKey                        (go.tag='yaml:"treatmentGroupKey"')
    // Populated parameters from XP configuration
    100: optional ParameterMap populatedParameterMap (go.tag='yaml:"populatedParameterMap,omitempty"')
}

enum ActorType {
    UNKNOWN = 0
    RIDER = 1
    DRIVER = 2
    STORE = 3
    FREIGHT_DRIVER = 4
    INVALID = 5
    // Later can add other types e.g. EATER, MERCHANT, ...
}

struct Actor {
    1: required string id                                   (go.tag='yaml:"id"')
    2: required ActorType type                              (go.tag='yaml:"type"')
    // Create a new test account
    3: optional bool create                                 (go.tag='yaml:"create,omitempty"')
    // Or use an existing account with uuid
    4: optional string accountUUID                          (go.tag='yaml:"accountUUID,omitempty"')
    5: optional string accountToken                         (go.tag='yaml:"accountToken,omitempty"')
    6: optional Device device                               (go.tag='yaml:"device,omitempty"')
    7: optional list<string> includedTags                   (go.tag='yaml:"includedTags,omitempty"')
    8: optional list<string> excludedTags                   (go.tag='yaml:"excludedTags,omitempty"')
    9: optional list<string> includedTraits                 (go.tag='yaml:"includedTraits,omitempty"')
    10: optional list<string> excludedTraits                (go.tag='yaml:"excludedTraits,omitempty"')
    // experimentKey: this can be found in Morpheus.
    // Specifying a key to a non-existent experiment will cause population to fail
    11: optional Experiments experiments  (go.tag='yaml:"experiments,omitempty"')
    12: optional string tenancy                             (go.tag='yaml:"tenancy,omitempty"')

    // Warning: Do not use production credentials in these fields, or do so at your own risk!
    // These fields are intended only for Populated ephemeral test-account credentials
    13: optional string accountEmail                        (go.tag='yaml:"accountEmail,omitempty"')
    14: optional string accountMobile                       (go.tag='yaml:"accountMobile,omitempty"')
    15: optional string accountPassword                     (go.tag='yaml:"accountPassword,omitempty"')
    16: optional bool requiresCashPaymentProfile            (go.tag='yaml:"requiresCashPaymentProfile,omitempty"')
    17: optional bool noPaymentProfile                      (go.tag='yaml:"noPaymentProfile,omitempty"')
    18: optional string traceSpan                           (go.tag='yaml:"traceSpan,omitempty"')
    19: optional LoyaltyData loyaltyData                    (go.tag='yaml:"loyaltyData,omitempty"')
    20: optional string accountPayload                      (go.tag='yaml:"accountPayload,omitempty"')

    // These fields are populated after the test account is created, for internal use only
    30: optional string firstName  (go.tag='yaml:"firstName,omitempty"')
    31: optional string lastName  (go.tag='yaml:"lastName,omitempty"')
    32: optional string territoryUUID  (go.tag='yaml:"territoryUUID,omitempty"')
    // only populated if this is a partner account
    33: optional i32 territoryID (go.tag='yaml:"territoryID,omitempty"')

    // Actor type specific fields
    100: optional ActorMetadata actorMetadata               (go.tag='yaml:"actorMetadata,omitempty"')

    // Generic definitions
    110: optional string actorType           (go.tag='yaml:"actorType,omitempty"')
    // Generic attributes, either in JSON or YAML form
    111: optional string attributes          (go.tag='yaml:"attributes,omitempty"')
}

union ActorMetadata {
    1: optional RiderMetadata rider     (go.tag='yaml:"rider,omitempty"')
    2: optional DriverMetadata driver   (go.tag='yaml:"driver,omitempty"')
    3: optional StoreMetadata store     (go.tag='yaml:"store,omitempty"')
}

struct RiderMetadata {
    1: optional Location pickupLocation     (go.tag='yaml:"pickupLocation,omitempty"')
    2: optional Location dropoffLocation    (go.tag='yaml:"dropoffLocation,omitempty"')
    3: optional i32  vvid                   (go.tag='yaml:"vvid,omitempty"')
    4: optional list<Location> viaLocations (go.tag='yaml:"viaLocations,omitempty"')
}

struct DriverMetadata {
    1: optional Vehicle vehicle             (go.tag='yaml:"vehicle,omitempty"')
    2: optional string productUUID          (go.tag='yaml:"productUUID,omitempty"')
    3: optional string globalProductUUID    (go.tag='yaml:"globalProductUUID,omitempty"')
    4: optional bool eatsDelivery           (go.tag='yaml:"eatsDelivery,omitempty"')
    5: optional i16 flowType                (go.tag='yaml:"flowType,omitempty"')
    6: optional bool createVehicle          (go.tag='yaml:"createVehicle,omitempty"')
}

struct StoreMetadata {
  1: required Location location             (go.tag='yaml:"location"')
  2: required string businessName           (go.tag='yaml:"businessName"')
  3: optional i16 avePrepTime               (go.tag='yaml:"avePrepTime,omitempty"')
  4: optional string pickupInstructions     (go.tag='yaml:"pickupInstructions,omitempty"')
  5: optional double maxDeliveryRadiusMiles (go.tag='yaml:"maxDeliveryRadiusMiles,omitempty"')

  // StoreMenu is optional. When a test account is created, a default menu is created with
  // one section, one sub-section, and one item. Passing this to Studio will upsert pre-defined
  // menu items to the store. The Menu struct is imported from eats-store/menu.thrift directly
  6: optional StoreMenu menu                (go.tag='yaml:"menu,omitempty"')
}

struct StoreMenu {
  1: optional string sectionUUID          (go.tag='yaml:"sectionUUID,omitempty"')
  2: optional string subsectionUUID       (go.tag='yaml:"subsectionUUID,omitempty"')
  3: optional string itemUUID             (go.tag='yaml:"itemUUID,omitempty"')
}

struct LoyaltyData {
  1: optional i32 qualifyingPoints        (go.tag='yaml:"qualifyingPoints,omitempty"')
  2: optional i32 lifetimeRewardPoints    (go.tag='yaml:"lifetimeRewardPoints,omitempty"')
  3: required string requestedTier        (go.tag='yaml:"requestedTier,omitempty"')
}

struct ScenarioConfiguration {
    1: optional string name                       (go.tag='yaml:"name,omitempty"')
    2: optional string description                (go.tag='yaml:"description,omitempty"')
    3: optional string ownerID                    (go.tag='yaml:"ownerID,omitempty"')
    4: optional string teamID                     (go.tag='yaml:"teamID,omitempty"')
    5: optional i64 (js.type = "Long") createdAt  (go.tag='yaml:"createdAt,omitempty"')
    6: optional i64 (js.type = "Long") updatedAt  (go.tag='yaml:"updatedAt,omitempty"')
    7: optional string traceSpan                  (go.tag='yaml:"traceSpan,omitempty"')
    100: optional Stage stage                     (go.tag='yaml:"stage"')
    101: optional list<Actor> actors              (go.tag='yaml:"actors"')

    // data is a newly added and of free-form. Any additional data that needs to be understood by
    // a studio orchetrator action can be defined here, make sure each test has its own block of
    // data understandable. Recommended to use YAML form (use '|')
    200: optional string data                     (go.tag='yaml:"data"')
}
