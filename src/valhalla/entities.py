from pydantic import BaseModel


class ExitTowardElement(BaseModel):
    text: str
    consecutive_count: int | None = None


class Sign(BaseModel):
    exit_toward_elements: list[ExitTowardElement] | None = None


class Maneuver(BaseModel):
    type: int
    instruction: str
    time: float
    length: float
    cost: float
    begin_shape_index: int
    end_shape_index: int
    travel_mode: str
    travel_type: str

    verbal_succinct_transition_instruction: str | None = None
    verbal_pre_transition_instruction: str | None = None
    verbal_post_transition_instruction: str | None = None
    verbal_transition_alert_instruction: str | None = None
    street_names: list[str] | None = None
    bearing_before: float | None = None
    bearing_after: float | None = None
    sign: Sign | None = None
    verbal_multi_cue: bool | None = None


class Summary(BaseModel):
    has_time_restrictions: bool
    has_toll: bool
    has_highway: bool
    has_ferry: bool
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    time: float
    length: float
    cost: float


class Leg(BaseModel):
    maneuvers: list[Maneuver]
    summary: Summary
    shape: str


class TripLocation(BaseModel):
    type: str
    lat: float
    lon: float
    original_index: int
    side_of_street: str | None = None


class Trip(BaseModel):
    locations: list[TripLocation]
    legs: list[Leg]
    summary: Summary
    status_message: str
    status: int
    units: str
    language: str


class Coordinate(BaseModel):
    lat: float
    lng: float


