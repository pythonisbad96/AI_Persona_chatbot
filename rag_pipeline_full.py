import os, json
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

# 1) load
with open("data/metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

docs = []
for item in metadata:
    p = os.path.join("data/speeches", item["file"])
    if os.path.exists(p):
        loaded = TextLoader(p, encoding="utf-8").load()
        for d in loaded:
            d.metadata = {"title": item["title"], "date": item["date"], "category": item["category"]}
        docs.extend(loaded)

# 2) chunk
split_docs = CharacterTextSplitter(chunk_size=800, chunk_overlap=100).split_documents(docs)

# 3) embed & store
emb = OpenAIEmbeddings(model="text-embedding-3-small")
db = FAISS.from_documents(split_docs, emb)
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# 4) prompt (context 포함!)
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "너는 대한민국 제15대 대통령 김대중이다. 말투와 어휘는 연설문 톤을 따른다. "
     "반드시 사실에 근거하고 과장하지 말라. 답변 말미에 '국민 여러분' 혹은 '감사합니다' 같은 표현을 곁들인다.\n\n"
     "다음은 참고할 맥락이다:\n{context}"),
    ("human", "{question}")
])

# 5) llm
llm = ChatOpenAI(model="gpt-4o-mini")

# 6) LCEL pipeline
def rag_pipeline(question):
    hits = retriever.get_relevant_documents(question)
    context = "\n\n".join([d.page_content for d in hits])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})

# test
print(rag_pipeline("남북정상회담 당시에 강조하신 핵심 메시지를 알려주세요."))
