"""
gRPC сервер для управления глоссарием терминов.
"""

import grpc
from concurrent import futures
import logging
import sys
import os

# Добавляем путь к сгенерированным proto-файлам
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    import glossary.glossary_pb2 as glossary_pb2
    import glossary.glossary_pb2_grpc as glossary_pb2_grpc
except ImportError as e:
    print(f"Ошибка: Не найдены сгенерированные proto-файлы.")
    print("\nВыполните команду для генерации:")
    print("python -m grpc_tools.protoc -I src/protobufs --python_out=src/glossary --grpc_python_out=src/glossary src/protobufs/glossary.proto")
    print("\nПосле генерации убедитесь, что в src/glossary/glossary_pb2_grpc.py строка 6 содержит:")
    print("from . import glossary_pb2 as glossary__pb2")
    sys.exit(1)

from database import Database
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GlossaryServicer(glossary_pb2_grpc.GlossaryServiceServicer):
    """Реализация gRPC сервиса для управления глоссарием."""
    
    def __init__(self, db):
        self.db = db
    
    def GetTerms(self, request, context):
        """Получение списка всех терминов."""
        try:
            terms = self.db.get_all_terms()
            term_messages = [
                glossary_pb2.Term(keyword=t['keyword'], description=t['description'])
                for t in terms
            ]
            return glossary_pb2.GetTermsResponse(terms=term_messages)
        except Exception as e:
            logger.error(f"Ошибка при получении списка терминов: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return glossary_pb2.GetTermsResponse(terms=[])
    
    def GetTerm(self, request, context):
        """Получение термина по ключевому слову."""
        try:
            term = self.db.get_term(request.keyword)
            if term:
                return glossary_pb2.GetTermResponse(
                    success=True,
                    term=glossary_pb2.Term(keyword=term['keyword'], description=term['description']),
                    message="Термин найден"
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return glossary_pb2.GetTermResponse(
                    success=False,
                    term=glossary_pb2.Term(),
                    message="Термин не найден"
                )
        except Exception as e:
            logger.error(f"Ошибка при получении термина: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return glossary_pb2.GetTermResponse(
                success=False,
                term=glossary_pb2.Term(),
                message=f"Ошибка: {str(e)}"
            )
    
    def AddTerm(self, request, context):
        """Добавление нового термина."""
        try:
            self.db.add_term(request.keyword, request.description)
            return glossary_pb2.AddTermResponse(
                success=True,
                message="Термин успешно добавлен"
            )
        except psycopg2.IntegrityError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            return glossary_pb2.AddTermResponse(
                success=False,
                message="Термин с таким ключевым словом уже существует"
            )
        except Exception as e:
            logger.error(f"Ошибка при добавлении термина: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return glossary_pb2.AddTermResponse(
                success=False,
                message=f"Ошибка: {str(e)}"
            )
    
    def UpdateTerm(self, request, context):
        """Обновление существующего термина."""
        try:
            updated = self.db.update_term(request.keyword, request.description)
            if updated:
                return glossary_pb2.UpdateTermResponse(
                    success=True,
                    message="Термин успешно обновлен"
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return glossary_pb2.UpdateTermResponse(
                    success=False,
                    message="Термин не найден"
                )
        except Exception as e:
            logger.error(f"Ошибка при обновлении термина: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return glossary_pb2.UpdateTermResponse(
                success=False,
                message=f"Ошибка: {str(e)}"
            )
    
    def DeleteTerm(self, request, context):
        """Удаление термина."""
        try:
            deleted = self.db.delete_term(request.keyword)
            if deleted:
                return glossary_pb2.DeleteTermResponse(
                    success=True,
                    message="Термин успешно удален"
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return glossary_pb2.DeleteTermResponse(
                    success=False,
                    message="Термин не найден"
                )
        except Exception as e:
            logger.error(f"Ошибка при удалении термина: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return glossary_pb2.DeleteTermResponse(
                success=False,
                message=f"Ошибка: {str(e)}"
            )


def serve():
    """Запуск gRPC сервера."""
    db = Database()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    glossary_pb2_grpc.add_GlossaryServiceServicer_to_server(
        GlossaryServicer(db), server
    )
    server.add_insecure_port('[::]:50051')
    logger.info("Запуск gRPC сервера на порту 50051")
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Остановка сервера...")
        server.stop(0)
        db.close()


if __name__ == '__main__':
    serve()
