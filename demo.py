from app_project_maker.app_project_maker import AppProjectMaker, Project

if __name__ == '__main__':
    app_maker = AppProjectMaker(base_dir_path='projects')
    project_name = '2021_11_26_Tomato'
    one_project = app_maker.create_project(project_name)
    print(one_project.hidden_config().create_date.strftime("%Y/%m/%d %H:%M:%S"))

    two_project = app_maker.copy_project('2021_11_26_Salad', one_project)

    app_maker.save_project()
    print(app_maker.exist_project('2021_11_26_Salad'))

    app_maker.remove_project(project_name)
