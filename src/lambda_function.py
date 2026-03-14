import logging
from controller import PassengerController
from service import InferenceService
from repository import PassengerRepository

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Dependências instanciadas no escopo global para reaproveitamento entre invocações (Warm Start)
service = InferenceService()
repository = PassengerRepository()
controller = PassengerController(service, repository)


def lambda_handler(event, context):
    """Entrypoint da função Lambda. Roteia requisições HTTP para o Controller correspondente."""
    http_method = event.get('httpMethod')
    resource = event.get('resource')

    logger.info(f"Recebendo requisição: [{http_method}] {resource}")

    try:
        if http_method == 'POST' and resource == '/sobreviventes':
            return controller.create_passenger(event.get('body'))

        elif http_method == 'GET' and resource == '/sobreviventes':
            return controller.get_passengers()

        elif http_method == 'GET' and resource == '/sobreviventes/{id}':
            passenger_id = event['pathParameters']['id']
            return controller.get_passenger(passenger_id)

        elif http_method == 'DELETE' and resource == '/sobreviventes/{id}':
            passenger_id = event['pathParameters']['id']
            return controller.delete_passenger(passenger_id)

        else:
            logger.warning(f"Rota não mapeada: {resource}")
            return controller._build_response(405, {'erro': 'Metodo ou Rota nao permitidos'})

    except Exception as e:
        # exc_info=True anexa o traceback completo ao log do CloudWatch
        logger.error(f"Erro interno não tratado: {str(e)}", exc_info=True)
        return controller._build_response(500, {'erro_interno': 'Falha no servidor de Machine Learning'})