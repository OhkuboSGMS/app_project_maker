# アプリのマスクの保存やクロップ箇所の切り出し保存など一括して引き受ける
import os
import shutil
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Dict, Type, List, Tuple, Union

from loguru import logger

from app_project_maker.error import DirectoryNotFoundError
from app_project_maker.hidden_project_config import ProjectMeta, META_HIDDEN_FILE
from app_project_maker.project_manage_config import ProjectManageConfig


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
    """
    AppProjectMakerから生成された1プロジェクト.
    """

    def __init__(self, path: Path, name: str = None):
        self.path = path
        self.name = path.stem
        self.components = {}
        if name:
            self.name = name

    def hidden_config(self):
        return ProjectMeta.read(self.path)

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

    def remove_component(self, resource_path: str):
        if resource_path in self.components.keys():
            self.components.pop(resource_path)


class AppProjectMaker:
    """
    アプリの設定データをプロジェクトフォルダを作成して管理するクラス

    add_componentで新たにリソースを追加:どのように管理するかはAbstractComponentの具象クラスが操作する
    create_projectでアプリのルートプロジェクトを作成する

    """
    project_file_path = "project.json"

    def __init__(self, cur_dir: str = os.path.curdir, base_dir_path: str = ".prj"):
        self.working_dir_path = Path(cur_dir)
        self.base_dir_path = self.working_dir_path.joinpath(base_dir_path)

        if not self.base_dir_path.exists():
            self.base_dir_path.mkdir(parents=True, exist_ok=True)

        self.projects: Dict[str, Project] = self.load_projects()

        if not os.path.exists(self.project_manage_config_path):
            self.save_project()

    def __getitem__(self, project_name: str) -> Project:
        if type(project_name) is not str:
            raise TypeError(project_name, type(project_name))
        if project_name not in self.projects:
            raise FileNotFoundError(project_name)
        if not self.projects[project_name].path.exists():
            raise DirectoryNotFoundError(self.projects[project_name].path)

        return self.projects[project_name]

    def exist_project(self, project_name: str) -> bool:
        """
        プロジェクトフォルダが既に存在しているかチェック
        :param project_name:
        :return:
        """
        return os.path.exists(self.base_dir_path.joinpath(project_name))

    def create_project(self, project_name: str) -> Project:
        """新しくプロジェクトを作成"""
        new_project_path = Path(self.base_dir_path).joinpath(project_name)
        if not new_project_path.exists():
            logger.info(f"新規プロジェクト作成: {new_project_path.absolute()}")
            new_project_path.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"既存プロジェクト使用: {new_project_path.absolute()}")

        # このフォルダがAppMakerによって作成されたことを示す，隠しファイルを作成.中身はjson
        if not os.path.exists(ProjectMeta.meta_file_path(new_project_path)):
            ProjectMeta.write(new_project_path, project_name)

        project = Project(new_project_path, name=project_name)
        self.projects[project_name] = project
        return project

    def copy_project(self, project_name: str, src_project: Project) -> Project:
        """プロジェクトのコピーを作成"""
        new_path = Path(self.base_dir_path).joinpath(project_name)
        shutil.copytree(src_project.path, new_path, dirs_exist_ok=True,)
        new_project = Project(new_path, name=project_name)
        self.projects[project_name] = new_project
        # メタファイルを上書き
        ProjectMeta.write(new_path, project_name)
        logger.info(f"コピーされたプロジェクトを使用: {new_path.absolute()}")
        return new_project

    def remove_project(self, project: Union[str, Project]):
        if isinstance(project, Project):
            project = project.name
        if project in self.projects:
            shutil.rmtree(self.projects[project].path)
            self.projects.pop(project)
        else:
            raise KeyError(f'削除不可.{project}は 認識されていません')

    def remove_all_project(self):
        shutil.rmtree(self.base_dir_path, ignore_errors=True)
        self.projects = {}

    def project_root_path(self, abs: bool = True) -> str:
        if abs:
            return str(self.base_dir_path.absolute())
        return str(self.base_dir_path)

    def list_projects(self, other_path: List[str]) -> Tuple[Tuple[str], Tuple[Path]]:
        """
        既存のプロジェクトを列挙.
        フォルダがプロジェクトフォルダかそうでないかは,プロジェクト生成時に
        自動的に作成される隠しファイル'.prj'の存在をもって判定する．
        :return:
        """
        dirs = list(self.base_dir_path.iterdir())
        dirs.extend(other_path)
        prj_dir_path = tuple(list(filter(lambda p: p.joinpath(META_HIDDEN_FILE).exists(), dirs)))
        prj_dir_name = tuple(map(lambda p: p.stem, prj_dir_path))
        return prj_dir_name, prj_dir_path

    def load_projects(self) -> Dict[str, Project]:
        if os.path.exists(self.project_file_path):
            manage_config = ProjectManageConfig.read(self.project_manage_config_path)
        else:
            manage_config = ProjectManageConfig(set())

        project_names, project_path = self.list_projects(list(manage_config.project_list))

        projects: Dict[str, Project] = {name: Project(path) for name, path in zip(project_names, project_path)}

        return projects

    def save_project(self):
        print(self.projects.values())
        manage_config = ProjectManageConfig(set(map(lambda p: str(p.path.absolute()), self.projects.values())))
        manage_config.write(self.project_manage_config_path)

    @property
    def project_manage_config_path(self) -> str:
        return str(self.base_dir_path.joinpath(self.project_file_path))

    def __del__(self):
        self.save_project()
