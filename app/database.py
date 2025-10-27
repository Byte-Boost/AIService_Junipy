# from pymongo import MongoClient
# import os
# import logging

# logger = logging.getLogger("uvicorn.error")

# # Configurações do banco
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# DB_NAME = os.getenv("DB_NAME", "chatdb")


# class DatabaseClient:
#     def __init__(self):
#         """Inicializa o cliente MongoDB."""
#         try:
#             self.client = MongoClient(MONGO_URI)
#             self.db = self.client[DB_NAME]
#             logger.info("Conexão com MongoDB estabelecida.")
#         except Exception as e:
#             logger.error(f"Erro ao conectar ao MongoDB: {e}")
#             raise

#     # 🔹 Exemplo: salvar mensagens recebidas do Java
#     def save_chat_messages(self, user_id: str, messages: list):
#         """Salva mensagens recebidas do backend Java."""
#         if not messages:
#             return
#         try:
#             for msg in messages:
#                 self.db.messages.insert_one({
#                     "userId": user_id,
#                     "role": msg.get("role"),
#                     "message": msg.get("message"),
#                     "chatId": msg.get("chatId"),
#                     "createdAt": msg.get("createdAt")
#                 })
#         except Exception as e:
#             logger.error(f"Erro ao salvar mensagens: {e}")

#     # 🔹 Exemplo: salvar o resultado do processamento (contexto/sumário)
#     def save_context_summary(self, user_id: str, summary: dict):
#         """Salva o contexto ou sumário gerado pela IA."""
#         try:
#             self.db.summaries.insert_one({
#                 "userId": user_id,
#                 "summary": summary,
#             })
#         except Exception as e:
#             logger.error(f"Erro ao salvar sumário: {e}")

#     def close(self):
#         """Fecha a conexão com o banco."""
#         try:
#             self.client.close()
#             logger.info("Conexão MongoDB encerrada.")
#         except Exception:
#             pass


# def get_database_client() -> DatabaseClient:
#     """Retorna um cliente do banco de dados."""
#     return DatabaseClient()
