from llama_index.readers.web import SimpleWebPageReader
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
import nest_asyncio; nest_asyncio.apply()
documents = SimpleWebPageReader(html_to_text=True).load_data(
        ['https://vedantasociety.net/vivekananda']
    )
from llama_index.core.evaluation import (
    generate_question_context_pairs,
    EmbeddingQAFinetuneDataset,
)
llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1,api_key=openai_api_key)
node_parser = SimpleNodeParser.from_defaults(chunk_size=512)
nodes = node_parser.get_nodes_from_documents(documents)
qa_dataset = generate_question_context_pairs(
    nodes, llm=llm, num_questions_per_chunk=2
)
#queries = qa_dataset.queries.values()
queries = list(qa_dataset.queries.values())
print(list(queries)[2])
gpt35 = OpenAI(temperature=0, model="gpt-3.5-turbo")
service_context_gpt35 = ServiceContext.from_defaults(llm=gpt35)

gpt4 = OpenAI(temperature=0, model="gpt-4")
service_context_gpt4 = ServiceContext.from_defaults(llm=gpt4)
vector_index = VectorStoreIndex(nodes, service_context = service_context_gpt35)
query_engine = vector_index.as_query_engine()
from llama_index.core.evaluation import FaithfulnessEvaluator
faithfulness_gpt4 = FaithfulnessEvaluator(service_context=service_context_gpt4)

eval_query = queries[10]
#Generate response first and use faithfull evaluator.
response_vector = query_engine.query(eval_query)

# Compute faithfulness evaluation
eval_result = faithfulness_gpt4.evaluate_response(response=response_vector)

# You can check passing parameter in eval_result if it passed the evaluation.
eval_result.passing