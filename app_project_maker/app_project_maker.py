# アプリのマスクの保存やクロップ箇所の切り出し保存など一括して引き受ける
import os
import shutil
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Dict, Type, List, Tuple

from app_project_maker.config.project_config import ComponentConfig, ProjectConfig
from loguru import logger


class AbstractComponent(metaclass=ABCMeta):
    """機能ごとリソース管理のための抽象Projectクラス
       AppProjectMakerからリソースを追加時にこのクラスを実装した具体クラスが使用される
       """
    mode = "None"

    def __init__(self, resource: str, base_path: Path):
        self.resource_name = resource
        self.resource_directory = base_path.joinpath(resource)
        if not self.resource_directory.exists():
            self.resource_directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Create Component Directory:{self.resource_directory}")

    @abstractmethod
    def create(self, ):
        """デフォルトのリソースを生成"""
        raise NotImplementedError()

    @abstractmethod
    def valid(self) -> bool:
        """現存するリソースが再利用可能かをチェック"""
        raise NotImplementedError()

    @property
    def resource_path(self) -> Path:
        """コンポーネントの保存パス"""
        return self.resource_directory

    @property
    @abstractmethod
    def resources(self) -> Dict[str, str]:
        """設定データで使用するデータのパスを渡す"""
        raise NotImplementedError


class Project:
    def __init__(self, path: Path):
        self.path = path


class AppProjectMaker:
    """
    アプリの設定データをプロジェクトフォルダを作成して管理するクラス

    add_componentで新たにリソースを追加:どのように管理するかはAbstractComponentの具象クラスが操作する
    create_projectでアプリのルートプロジェクトを作成する

    """
    default_project_path = Path(__file__).parent.joinpath('default_project.json')
    project_file_path = "project.json"

    def __init__(self, cur_dir: str = os.path.curdir, base_dir_path: str = ".prj"):
        self.working_dir_path = Path(cur_dir)
        self.base_dir_path = self.working_dir_path.joinpath(base_dir_path)
        self.path = self.base_dir_path

        self.components: Dict[str, AbstractComponent] = {}
        if not self.base_dir_path.exists():
            self.base_dir_path.mkdir(parents=True, exist_ok=True)
            # Path(self.path).joinpath(self.project_file_path).write_text(Project.to_json(self._project_config))

        self.project_dir: Dict[str, Path] = {dir.stem: dir for dir in self.path.iterdir()}

        _project_path = Path(self.default_project_path)
        if _project_path.exists():
            self._project_config = ProjectConfig.from_json(_project_path.read_text())
            self._project_config_default = ProjectConfig.from_json(_project_path.read_text())
        else:
            logger.warning(f"Backend::プロジェクト:{_project_path}がありません.デフォルトのフォルダを使用します")
            self._project_config = ProjectConfig()
            self._project_config_default = ProjectConfig()

    def __getitem__(self, item: str):
        if type(item) is not str:
            raise TypeError(item, type(item))
        return self.components[item]

    @property
    def components_config(self) -> List[ComponentConfig]:
        return list(map(lambda item: ComponentConfig(resource_path=item[0]),
                        self.components.items()))

    # Reset path
    def reset_path(self):
        self.path = Path(self.base_dir_path)

    def remove_component(self, resource_path: str):
        if resource_path in self.components.keys():
            self.components.pop(resource_path)

    def add_component(self, resource_path: str, source_name: str, new_project: Type[AbstractComponent]) \
            -> Tuple[Dict[str, str], AbstractComponent]:
        """
        プロジェクトにコンポーネントを追加
        コンポーネントは検知、オプティカルフローなどの機能ごとに追加して設定ファイルを管理する
        :param resource_path: 画像リソースの場所そのままを示す
        :type resource_path: str
        :param source_name: 画像リソースをディレクトリとして配置する際のフォルダ名
        :type source_name: str
        :param new_project:
        :type new_project:
        :return:
        :rtype:
        """
        component_path = self.path.joinpath(source_name)
        # このリソースに対するディレクトリパス
        self.components[resource_path] = component = new_project(source_name, self.path)

        # パスが現存し、機能に使えるデータがそろっている
        if component_path.exists() and component.valid():
            logger.info(f"Use Exist Resource : {component_path}")
        # パスが存在していないので、新規にコンポーネントディレクトリおよびデフォルトのデータを作成
        else:
            logger.info(f"Create New Resource Directory : {component_path}")
            component.create()

        return component.resources, component

    def create_project(self, project_name: str) -> Project:
        """新しくプロジェクトを作成"""
        self.path = Path(self.base_dir_path).joinpath(project_name)
        self.project_dir[self.path.stem] = self.path
        if not self.path.exists():
            logger.info(f"新しいプロジェクトを作成: {self.path.absolute()}")
            self.path.mkdir(parents=True, exist_ok=True)
            project_config_path = self.path.joinpath(self.project_file_path)
            project_config_path.write_text(ProjectConfig.to_json(self._project_config_default, indent=1))
            self._project_config = ProjectConfig.from_json(project_config_path.read_text())

        else:
            logger.info(f"既存のプロジェクトを使用: {self.path.absolute()}")
            self._project_config = ProjectConfig.from_json(self.path.joinpath(self.project_file_path).read_text())
        return Project(self.path)

    def copy_project(self, project_name: str) -> Project:
        """プロジェクトのコピーを作成"""
        new_path = Path(self.base_dir_path).joinpath(project_name)
        shutil.copytree(self.path, new_path, dirs_exist_ok=True)

        self.path = new_path
        self.project_dir[self.path.stem] = self.path

        logger.info(f"コピーされたプロジェクトを使用: {self.path.absolute()}")
        self._project_config = ProjectConfig.from_json(self.path.joinpath(self.project_file_path).read_text())
        return Project(self.path)

    def remove_project(self, project_name: str):
        if project_name in self.project_dir:
            shutil.rmtree(self.project_dir[project_name])
        else:
            logger.warning(f'削除不可.{project_name}は 認識されていません')

    def remove_all_project(self):
        shutil.rmtree(self.base_dir_path)

    def project_root_path(self, abs: bool = True) -> str:
        if abs:
            return str(self.base_dir_path.absolute())
        return str(self.base_dir_path)

    @property
    def project_config(self) -> ProjectConfig:
        return self._project_config

    @property
    def project_config_path(self) -> str:
        return str(self.path.joinpath(self.project_file_path))
