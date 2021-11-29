from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set

from dataclasses_json import dataclass_json


@dataclass_json()
@dataclass()
class ProjectManageConfig:
    """
    プロジェクトを管理するためのコンフィグ
    """
    # プロジェクトのフォルダのパス
    project_list: Set[str]

    @classmethod
    def read(cls, json_path: str) -> ProjectManageConfig:
        with open(json_path, 'r', encoding='UTF-8') as fp:
            return ProjectManageConfig.from_json(fp.read())

    def write(self, json_path: str):
        with open(json_path, 'w', encoding='UTF-8') as fp:
            fp.write(self.to_json(indent=2, ensure_ascii=False))
