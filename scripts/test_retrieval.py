
from backend.services.retrieval_service import retrieve_context


question = "What is the return period for Gold members?"

result = retrieve_context(question)

print("\nQUESTION:")
print(question)

print("\nRETRIEVED CONTEXT:")
print(result["context"])

print("\nSOURCES:")

for source in result["sources"]:
    print(source)
