"""
プロジェクト生成時にプロジェクトディレクトリ内に生成する隠しファイルメタデータjson
"""
from __future__ import annotations

import ctypes
import os
import platform
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

from dataclasses_json import dataclass_json

META_HIDDEN_FILE = '.prj'


def as_hidden_file_windows(full_path: str):
    """
    Windows特有の隠しファイル設定を実行
    :param full_path:
    :return:
    """
    if platform.system() != 'Windows':
        return

    if not os.path.isabs(full_path):
        raise TypeError(f'{full_path} is not absolute path')
    try:
        __import__('ctypes.wintypes')
        SetFileAttributes = ctypes.windll.kernel32.SetFileAttributesW
        SetFileAttributes.argtypes = ctypes.wintypes.LPWSTR, ctypes.wintypes.DWORD
        SetFileAttributes.restype = ctypes.wintypes.BOOL

        FILE_ATTRIBUTE_HIDDEN = 0x02

        ret = SetFileAttributes(full_path, FILE_ATTRIBUTE_HIDDEN)
        if not ret:
            raise ctypes.WinError()
    except Exception as e:
        print(e)


@dataclass_json()
@dataclass()
class ProjectMeta:
    name: str
    create_date: datetime
    update_date: datetime = datetime.now()
    user: str = ''
    maker: str = ''

    @classmethod
    def meta_file_path(cls, directory_path: str):
        return os.path.join(directory_path, META_HIDDEN_FILE)

    def write_current(self, directory_path: Union[str, Path]):
        file_path = ProjectMeta.meta_file_path(directory_path)
        with open(file_path, 'w', encoding='UTF-8') as fp:
            fp.write(ProjectMeta.to_json(self, indent=2, ensure_ascii=False))

    @classmethod
    def write(cls, directory_path: Union[str, Path], name: str, user: str = 'No Name', maker: str = 'Project Maker'):
        now = datetime.now()
        meta = ProjectMeta(name, now, now, user, maker)
        file_path = ProjectMeta.meta_file_path(directory_path)
        with open(file_path, 'w', encoding='UTF-8') as fp:
            fp.write(ProjectMeta.to_json(meta, indent=2, ensure_ascii=False))

        # as_hidden_file_windows(os.path.abspath(file_path))

    @classmethod
    def read(cls, directory_path: Union[str, Path]) -> ProjectMeta:
        with open(os.path.join(directory_path, META_HIDDEN_FILE), 'r', encoding='UTF-8') as fp:
            return ProjectMeta.from_json(fp.read())
