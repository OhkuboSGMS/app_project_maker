from pathlib import Path

from app_project_maker import AppProjectMaker
from app_project_maker.app_project_maker import Project
from app_project_maker.project_manage_config import ProjectManageConfig


def test_create_project():
    project = AppProjectMaker(base_dir_path='projects')
    assert Path('projects').exists()

    new_project: Project = project.create_project('NewCompany')
    assert Path('projects/NewCompany').is_dir()
    assert Path('projects/NewCompany/.prj').exists()
    assert Path('projects/project.json').exists()

    with open('projects/project.json') as f:
        assert len(f.read()) == len(ProjectManageConfig(set()).to_json(indent=2, ensure_ascii=False))

    project.save_project()
    with open('projects/project.json') as f:
        assert len(f.read()) > 0

    project.remove_all_project()


def test_copy_project():
    project = AppProjectMaker(base_dir_path='projects')
    new_project: Project = project.create_project('NewCompany')
    another_project: Project = project.copy_project('AnotherCompany', new_project)

    assert another_project.path.is_dir()
    assert another_project.path.stem == 'AnotherCompany'
    project.remove_all_project()


def test_remove_project():
    project = AppProjectMaker(base_dir_path='projects')
    new_project = project.create_project('NewCompany')
    another_project = project.copy_project('UGen', new_project)
    project.remove_project('NewCompany')
    assert not Path('projects/NewCompany').exists()
    assert Path('projects/UGen').exists()
    try:
        project.remove_project('NotCreateProject')
        assert False
    except Exception:
        pass

    project.remove_all_project()


def test_remove_all_project():
    project = AppProjectMaker(base_dir_path='projects')
    new_project = project.create_project('NewCompany')
    project.copy_project('AnotherCompany', new_project)

    project.remove_all_project()
    assert not Path('projects').exists()
