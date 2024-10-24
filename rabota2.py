import zipfile
import xml.etree.ElementTree as ET
import toml
import graphviz
import os


def load_config(config_file):
    """Загрузить конфигурацию из TOML-файла."""
    return toml.load(config_file)


def get_dependencies(package_name, max_depth):
    """Извлекает зависимости из пакета .nupkg"""
    nupkg_path = f'{package_name}.nupkg'  # Путь к nupkg-файлу

    # Проверяем, существует ли файл .nupkg
    if not os.path.exists(nupkg_path):
        print(f"{nupkg_path} not found.")
        return {}

    dependencies = {}
    try:
        # Распаковываем .nupkg как zip-файл
        with zipfile.ZipFile(nupkg_path, 'r') as zip_ref:
            # Ищем файл .nuspec внутри архива
            nuspec_file = [f for f in zip_ref.namelist() if f.endswith('.nuspec')]
            if nuspec_file:
                with zip_ref.open(nuspec_file[0]) as file:
                    # Парсим .nuspec как XML
                    tree = ET.parse(file)
                    root = tree.getroot()

                    # Пространства имен в файле .nuspec
                    namespaces = {'ns': 'http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd'}

                    # Поиск зависимостей
                    for dependency in root.findall(".//ns:dependency", namespaces):
                        dep_id = dependency.get('id')
                        dep_version = dependency.get('version')
                        dependencies.setdefault(package_name, []).append(dep_id)
                        dependencies.setdefault(dep_id, [])
    except Exception as e:
        print(f"Error in found denendencies of {package_name}: {e}")

    return dependencies


def create_graph(dependencies, package_name, max_depth):
    """Создает граф зависимостей."""
    dot = graphviz.Digraph()
    added_packages = set()  # Множество для отслеживания уже добавленных пакетов
    added_edges = set()  # Множество для отслеживания добавленных рёбер (ребро — это пара (узел1, узел2))

    def add_edges(package, depth):
        """Рекурсивно добавляет пакеты и зависимости в граф."""
        if depth < 0 or package not in dependencies:
            return

        if package not in added_packages:  # Если пакет ещё не добавлен
            dot.node(package)
            added_packages.add(package)  # Помечаем как добавленный

        for dep in dependencies[package]:
            edge = (package, dep)  # Ребро между package и dep
            if edge not in added_edges:  # Проверяем, добавлено ли уже такое ребро
                dot.edge(package, dep)
                added_edges.add(edge)  # Добавляем ребро в множество
            add_edges(dep, depth - 1)  # Рекурсивно продолжаем для зависимостей

    add_edges(package_name, max_depth)
    return dot


def main():
    # Загрузка конфигурации
    config = load_config("config.toml")
    package_name = config['visualizer']['package_name']
    output_image = config['visualizer']['output_image']
    max_depth = config['visualizer']['max_depth']

    # Получение зависимостей
    dependencies = get_dependencies(package_name, max_depth)

    # Создание графа
    if dependencies:
        graph = create_graph(dependencies, package_name, max_depth)

        # Сохранение графа в PNG
        graph.render(output_image, format='png', cleanup=True)
        print(f"Successfully saved in {output_image}")
    else:
        print(f"Not found {package_name}")


if __name__ == "__main__":
    main()
