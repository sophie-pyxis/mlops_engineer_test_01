import uuid
import json
import logging
from typing import Dict, Any
from schemas import PassengerFeatureSchema
from service import InferenceService
from repository import PassengerRepository

logger = logging.getLogger()


class PassengerController:
    """Orquestra o fluxo HTTP: valida entrada, aciona domínio e formata a resposta."""

    def __init__(self, service: InferenceService, repository: PassengerRepository):
        """Recebe as dependências por injeção — padrão que viabiliza mocks nos testes unitários."""
        self.service = service
        self.repository = repository

    def create_passenger(self, body_str: str) -> Dict[str, Any]:
        """Processa o POST /sobreviventes: valida payload, executa inferência e persiste o resultado."""
        try:
            schema = PassengerFeatureSchema.from_json(body_str)
            probability = self.service.calculate_survival_probability(schema.caracteristicas)
            passenger_id = str(uuid.uuid4())
            self.repository.save(passenger_id, schema.caracteristicas, probability)
            return self._build_response(201, {'id': passenger_id, 'probabilidade_sobrevivencia': probability})

        except ValueError as e:
            # Erros de validação são falhas do cliente — retorna 400 sem acionar o modelo
            logger.warning(f"Payload inválido: {str(e)}")
            return self._build_response(400, {'erro': str(e)})

    def get_passengers(self) -> Dict[str, Any]:
        """Retorna a lista completa de passageiros avaliados."""
        items = self.repository.get_all()
        return self._build_response(200, items)

    def get_passenger(self, passenger_id: str) -> Dict[str, Any]:
        """Busca um passageiro pelo ID. Converte probabilidade de string para float antes de retornar."""
        item = self.repository.get_by_id(passenger_id)

        if item:
            # DynamoDB armazena números como string — conversão necessária antes de serializar o JSON
            item['probabilidade_sobrevivencia'] = float(item['probabilidade_sobrevivencia'])
            return self._build_response(200, item)

        return self._build_response(404, {'erro': 'Passageiro nao encontrado'})

    def delete_passenger(self, passenger_id: str) -> Dict[str, Any]:
        """Remove o passageiro da base. REST designa 204 (No Content) para deleções bem-sucedidas."""
        self.repository.delete(passenger_id)
        return self._build_response(204, '')

    def _build_response(self, status_code: int, body: Any) -> Dict[str, Any]:
        """Formata a resposta no padrão esperado pelo AWS API Gateway Proxy Integration."""
        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(body) if body else ''
        }