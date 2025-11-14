"""
Клиент для тестирования gRPC API сервера глоссария.
"""

import grpc
import sys
import os

# Добавляем путь к сгенерированным proto-файлам
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from glossary import glossary_pb2
    from glossary import glossary_pb2_grpc
except ImportError as e:
    import traceback
    print(f"Ошибка: Не найдены сгенерированные proto-файлы.")
    print(f"Детали ошибки: {e}")
    traceback.print_exc()
    print("\nВыполните команду для генерации:")
    print("python -m grpc_tools.protoc -I src/protobufs --python_out=src/glossary --grpc_python_out=src/glossary src/protobufs/glossary.proto")
    print("\nПосле генерации убедитесь, что в src/glossary/glossary_pb2_grpc.py строка 6 содержит:")
    print("from . import glossary_pb2 as glossary__pb2")
    sys.exit(1)


def run():
    """Тестирование gRPC API."""
    channel = grpc.insecure_channel('localhost:50051')
    stub = glossary_pb2_grpc.GlossaryServiceStub(channel)
    
    print("=== Тестирование gRPC API глоссария ===\n")
    
    # 1. Добавление терминов
    print("1. Добавление терминов...")
    terms_to_add = [
        ("State", "Состояние, данные компонента, которые могут изменяться со временем"),
        ("Redux", "Библиотека для управления состоянием JavaScript-приложений"),
        ("MobX", "Библиотека для управления состоянием, основанная на реактивном программировании"),
        ("Context API", "Встроенный в React механизм для передачи данных через дерево компонентов"),
        ("Hook", "Специальная функция в React, позволяющая использовать состояние в функциональных компонентах")
    ]
    
    for keyword, description in terms_to_add:
        try:
            response = stub.AddTerm(glossary_pb2.AddTermRequest(
                keyword=keyword,
                description=description
            ))
            if response.success:
                print(f"  ✓ Добавлен термин: {keyword}")
            else:
                print(f"  ✗ Ошибка при добавлении {keyword}: {response.message}")
        except grpc.RpcError as e:
            print(f"  ✗ gRPC ошибка при добавлении {keyword}: {e.details()}")
    
    # 2. Получение списка всех терминов
    print("\n2. Получение списка всех терминов...")
    try:
        response = stub.GetTerms(glossary_pb2.GetTermsRequest())
        print(f"  Найдено терминов: {len(response.terms)}")
        for term in response.terms:
            print(f"  - {term.keyword}: {term.description[:50]}...")
    except grpc.RpcError as e:
        print(f"  ✗ Ошибка: {e.details()}")
    
    # 3. Получение конкретного термина
    print("\n3. Получение термина 'Redux'...")
    try:
        response = stub.GetTerm(glossary_pb2.GetTermRequest(keyword="Redux"))
        if response.success:
            print(f"  ✓ {response.term.keyword}: {response.term.description}")
        else:
            print(f"  ✗ {response.message}")
    except grpc.RpcError as e:
        print(f"  ✗ Ошибка: {e.details()}")
    
    # 4. Обновление термина
    print("\n4. Обновление термина 'State'...")
    try:
        response = stub.UpdateTerm(glossary_pb2.UpdateTermRequest(
            keyword="State",
            description="Состояние - данные компонента React, которые могут изменяться со временем и влияют на отображение компонента"
        ))
        if response.success:
            print(f"  ✓ {response.message}")
        else:
            print(f"  ✗ {response.message}")
    except grpc.RpcError as e:
        print(f"  ✗ Ошибка: {e.details()}")
    
    # 5. Получение обновленного термина
    print("\n5. Получение обновленного термина 'State'...")
    try:
        response = stub.GetTerm(glossary_pb2.GetTermRequest(keyword="State"))
        if response.success:
            print(f"  ✓ {response.term.keyword}: {response.term.description}")
    except grpc.RpcError as e:
        print(f"  ✗ Ошибка: {e.details()}")
    
    # 6. Удаление термина (закомментировано, чтобы не удалять тестовые данные)
    # print("\n6. Удаление термина 'Hook'...")
    # try:
    #     response = stub.DeleteTerm(glossary_pb2.DeleteTermRequest(keyword="Hook"))
    #     if response.success:
    #         print(f"  ✓ {response.message}")
    #     else:
    #         print(f"  ✗ {response.message}")
    # except grpc.RpcError as e:
    #     print(f"  ✗ Ошибка: {e.details()}")
    
    channel.close()
    print("\n=== Тестирование завершено ===")


if __name__ == '__main__':
    run()
