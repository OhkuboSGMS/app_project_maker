from pathlib import Path

from app_project_maker import AppProjectMaker
from app_project_maker.app_project_maker import Project


def test_create_project():
    project = AppProjectMaker(base_dir_path='projects')
    assert Path('projects').exists()

    new_project: Project = project.create_project('NewCompany')
    assert Path('projects/NewCompany').is_dir()
    assert Path('projects/NewCompany/project.json').is_file()

    project.remove_all_project()


def test_copy_project():
    project = AppProjectMaker(base_dir_path='projects')
    new_project: Project = project.create_project('NewCompany')
    another_project: Project = project.copy_project('AnotherCompany')

    assert another_project.path.is_dir()
    assert another_project.path.stem == 'AnotherCompany'
    project.remove_all_project()


def test_remove_project():
    project = AppProjectMaker(base_dir_path='projects')
    project.create_project('NewCompany')
    project.copy_project('AnotherCompany')

    project.remove_project('NewCompany')
    assert not Path('projects/NewCompany').exists()
    assert Path('projects/AnotherCompany').exists()
    project.remove_all_project()


def test_remove_all_project():
    project = AppProjectMaker(base_dir_path='projects')
    project.create_project('NewCompany')
    project.copy_project('AnotherCompany')

    project.remove_all_project()
    assert not Path('projects').exists()
