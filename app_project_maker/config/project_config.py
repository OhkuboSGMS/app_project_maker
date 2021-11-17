from dataclasses import dataclass
from typing import List

import typing
from dataclasses_json import dataclass_json

Color = typing.Tuple[int, int, int]


@dataclass_json()
@dataclass()
class DetectionConfig:
    # TODO RGB or #RRRGGGBBB
    gpu: bool
    text_color: Color
    size_w: int
    size_h: int


@dataclass_json()
@dataclass()
class ComponentConfig:
    resource_path: str


@dataclass_json()
@dataclass()
class RecordConfig:
    directory: str
    interval_minutes: int
    record_raw: bool
    record_detection: bool


@dataclass_json()
@dataclass
class ProjectConfig:
    components: List[ComponentConfig]
    record: RecordConfig
    # detection: DetectionConfig
    # mode: str
