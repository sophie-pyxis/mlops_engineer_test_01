import json
import unittest
from unittest.mock import MagicMock

from src.controller import PassengerController
from src.service import InferenceService
from src.repository import PassengerRepository


class TestPassengerAPI(unittest.TestCase):
    """Testes unitários da API de inferência do Titanic.

    MagicMock substitui o modelo e o DynamoDB — nenhuma chamada real
    à AWS ou alocação de memória para o pkl ocorre durante a suite.
    """

    def setUp(self):
        """Monta o cenário de teste injetando dublês nas dependências do Controller."""
        self.mock_service = MagicMock(spec=InferenceService)
        self.mock_repository = MagicMock(spec=PassengerRepository)
        self.controller = PassengerController(self.mock_service, self.mock_repository)

    def test_create_passenger_success(self):
        """Verifica o fluxo feliz do POST: payload válido deve retornar 201 com id e probabilidade."""
        # Arrange
        valid_payload = json.dumps({"caracteristicas": [3, 22.0, 1, 0, 7.25]})
        self.mock_service.calculate_survival_probability.return_value = 0.65

        # Act
        response = self.controller.create_passenger(valid_payload)

        # Assert
        self.assertEqual(response['statusCode'], 201)
        body = json.loads(response['body'])
        self.assertIn('id', body)
        self.assertEqual(body['probabilidade_sobrevivencia'], 0.65)
        self.mock_repository.save.assert_called_once()

    def test_create_passenger_invalid_schema(self):
        """Garante que payloads inválidos são rejeitados com 400 antes de acionar o modelo ou o banco."""
        # Arrange
        invalid_payload = json.dumps({"outra_chave_qualquer": "valor_malicioso"})

        # Act
        response = self.controller.create_passenger(invalid_payload)

        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.mock_service.calculate_survival_probability.assert_not_called()
        self.mock_repository.save.assert_not_called()

    def test_get_passenger_found(self):
        """Verifica que o Controller converte a probabilidade de string para float ao ler do DynamoDB."""
        # Arrange
        fake_id = "1234-uuid-mock"
        self.mock_repository.get_by_id.return_value = {
            'id': fake_id,
            'probabilidade_sobrevivencia': '0.85'
        }

        # Act
        response = self.controller.get_passenger(fake_id)

        # Assert
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['probabilidade_sobrevivencia'], 0.85)


if __name__ == '__main__':
    unittest.main()