import os
import pickle
import logging
from typing import List

logger = logging.getLogger()


class InferenceService:
    """Camada de negócio responsável pelo carregamento e execução do modelo de ML."""

    # Atributo de classe para manter o modelo em memória entre invocações (Warm Start)
    _model = None

    @classmethod
    def get_model(cls):
        """Carrega o modelo do disco apenas no Cold Start — nas invocações seguintes
        o modelo já está em memória e é retornado instantaneamente."""
        if cls._model is None:
            logger.info("Cold Start: carregando modelo pkl para a memória cache.")
            model_path = os.path.join(os.path.dirname(__file__), 'modelo', 'model.pkl')
            with open(model_path, 'rb') as f:
                cls._model = pickle.load(f)
        return cls._model

    def calculate_survival_probability(self, features: List[float]) -> float:
        """Executa a inferência e retorna a probabilidade de sobrevivência (classe 1).

        predict_proba retorna shape (n_amostras, n_classes).
        Como passamos 1 amostra: [[prob_classe_0, prob_classe_1]]
        O acesso correto é [0][1] — primeira amostra, probabilidade da classe positiva.
        """
        model = self.get_model()
        probability = model.predict_proba([features])[0][1]
        logger.info("Inferência computada com sucesso.")
        return float(probability)