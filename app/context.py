from contextvars import ContextVar

# Variável de contexto compartilhada
jwt_token_ctx = ContextVar('jwt_token', default=None)