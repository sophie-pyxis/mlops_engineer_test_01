# Importa modulo para formatacao das strings pseudo-HTTP dos testes
import json
# Importa base nativa para assercoes orientadas a objeto
import unittest
# Importa a biblioteca MagicMock. Fundamental em MLOps:
# Sem Mocks, os testes fariam acesso pago na AWS e cobrariam recursos reais a cada execucao!
from unittest.mock import MagicMock

# Importa as estruturas reais para teste simulado
from src.controller import PassengerController
from src.service import InferenceService
from src.repository import PassengerRepository

# Classe isolada herda framework de test case padrao do python
class TestPassengerAPI(unittest.TestCase):
    
    # Metodo de montagem de cenario invocado antes de todo e qualquer teste (Boilerplate)
    def setUp(self):
        # Transforma o servico de Machine Learning em um Duble Virtual (Mock)
        # Nao aloca modelo pkl em memoria e economiza centenas de milissegundos
        self.mock_service = MagicMock(spec=InferenceService)
        # Mimetiza o Repositorio (Nenhum consumo de WCU/RCU real ocorrera contra o DynamoDB)
        self.mock_repository = MagicMock(spec=PassengerRepository)
        
        # Cria a instancia da arquitetura sob os agentes cenograficos (Test Driven Design)
        self.controller = PassengerController(self.mock_service, self.mock_repository)

    # Verifica se a escoragem preditiva ocorre quando formatada perfeitamente
    def test_create_passenger_success(self):
        # Arrange (Dado): Simula o pacote de bits disparados da rede no Postman
        valid_payload = json.dumps({"caracteristicas": [3, 22.0, 1, 0, 7.25]})
        
        # Treina o robo Mock para responder "65% de sobrevivencia" independente da logica de arvore
        self.mock_service.calculate_survival_probability.return_value = 0.65
        
        # Act (Quando): Invocamos a acao de fronteira no controlador
        response = self.controller.create_passenger(valid_payload)
        
        # Assert (Entao): Confirmamos sucesso se obtermos a criacao (Http 201)
        self.assertEqual(response['statusCode'], 201)
        # Extrai dicionario avaliativo da resposta embutida
        body = json.loads(response['body'])
        # Confirma que um Ticket ID unico esta anexado ao pacote
        self.assertIn('id', body)
        # Valida se a probabilidade coincide com os 65% pre-simulados
        self.assertEqual(body['probabilidade_sobrevivencia'], 0.65)
        # Garante que, silenciosamente, o controlador chamou a funcão de acesso ao DynamoDB pelo menos 1 vez
        self.mock_repository.save.assert_called_once()

    # Valida o paredao de Schemas operando com rejeicao antecipada (Data Quality)
    def test_create_passenger_invalid_schema(self):
        # Arrange (Dado): Um payload hostil, onde inserimos palavras onde a API precisa de numeros
        invalid_payload = json.dumps({"outra_chave_qualquer": "valor_malicioso"})
        
        # Act (Quando): Requisitamos acesso negocial
        response = self.controller.create_passenger(invalid_payload)
        
        # Assert (Entao): Schema lanca validacao falha e envia Bad Request sem pena
        self.assertEqual(response['statusCode'], 400)
        # Assegura explicitamente que o Scikit-Learn (Service) sequer foi incomodado (Custo computacional salvo)
        self.mock_service.calculate_survival_probability.assert_not_called()
        # Repositorio (Banco) protegido e nao ativado
        self.mock_repository.save.assert_not_called()

    # Testa a leitura confiavel de dados do banco simulado
    def test_get_passenger_found(self):
        # Arrange (Dado): Id cenografico
        fake_id = "1234-uuid-mock"
        # O mock finge ler da Nuvem AWS uma variavel String pura (Devido aos limitadores NoSQL DynamoDB)
        self.mock_repository.get_by_id.return_value = {
            'id': fake_id, 
            'probabilidade_sobrevivencia': '0.85' 
        }
        
        # Act (Quando): Disparado Get Request pelo controlador
        response = self.controller.get_passenger(fake_id)
        
        # Assert (Entao): Valida Sucesso transacional
        self.assertEqual(response['statusCode'], 200)
        # Quebra string padrao
        body = json.loads(response['body'])
        # O Controller precisou refinar o metadado. Tem que ser interpretado de volta como float numerico puro!
        self.assertEqual(body['probabilidade_sobrevivencia'], 0.85)

# Entrypoint especifico para testes locais em IDEs
if __name__ == '__main__':
    # Roda as validacoes
    unittest.main()