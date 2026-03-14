# Importa para resolucao do caminho de diretorio dos arquivos do sistema
import os
# Importa modulo de desserializacao para carregar objetos binarios (modelo Scikit-Learn)
import pickle
# Importa framework de monitoramento para auditoria
import logging
# Importa tipagem para o parametro de entrada analitico
from typing import List

# Obtem a instancia central de geracao de logs
logger = logging.getLogger()

# Implementa a camada que detem a regra de negocio e algoritmos estatisticos (Domain Logic)
class InferenceService:
    # Atributo de classe (estatico) utilizado para manter a instancia do modelo ativa na memoria
    _model = None

    # Metodo implementado com Padrao Singleton focado na performance do ambiente Serverless
    @classmethod
    def get_model(cls):
        # Se o container lambda for novo (Cold Start), o modelo e None e exige leitura de disco
        if cls._model is None:
            # Log de alerta de cold start estatistico
            logger.info("Executando Cold Start: Carregando modelo pkl para a memoria cache.")
            # Resolve o caminho absoluto e dinamico ate a pasta modelo ignorando o CWD atual
            model_path = os.path.join(os.path.dirname(__file__), 'modelo', 'model.pkl')
            # Abre o arquivo em modo binario de leitura 'rb'
            with open(model_path, 'rb') as f:
                # Desserializa a rede/arvore para o atributo Singleton utilizando o Pickle
                cls._model = pickle.load(f)
        # Retorna o modelo (que em Warm Starts da Lambda, ja estara em memoria Ram instantaneamente)
        return cls._model

    # Metodo que expoem a abstracao da regra de calculo preditivo
    def calculate_survival_probability(self, features: List[float]) -> float:
        # Recupera o modelo instanciado da memoria do container
        model = self.get_model()
        
        # O modelo exige vetor de amostras 2D: passamos a lista encapsulada em outra lista '[features]'
        # predict_proba retorna [[probabilidade_0, probabilidade_1]] da classe binaria
        #  captura o batch atual e [1] captura o percentual positivo (Sobrevivencia = classe 1)
        probability = model.predict_proba([features])[1]
        
        # Log de sucesso da transacao analitica
        logger.info("Inferencia algoritmica computada com exito pelo Scikit-Learn.")
        
        # Retorna forçando o tipo flutuante (evitando tipos numéricos complexos do numpy)
        return float(probability)