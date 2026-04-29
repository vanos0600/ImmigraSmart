from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset
import os

# 1. Prepara tus datos (puedes traerlos de tus logs de Supabase)
data_samples = {
    'question': ['¿Puedo trabajar con visa de estudiante?'],
    'answer': ['Sí, pero solo si tu estudio es acreditado por el MŠMT.'],
    'contexts': [['El trabajo para estudiantes está permitido en programas acreditados...']],
    'ground_truth': ['Los estudiantes en programas acreditados tienen acceso libre al mercado laboral.']
}

dataset = Dataset.from_dict(data_samples)

# 2. Ejecuta la evaluación
# Nota: Ragas usará la API Key que tengas en tu entorno
score = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision]
)

print(score.to_pandas())